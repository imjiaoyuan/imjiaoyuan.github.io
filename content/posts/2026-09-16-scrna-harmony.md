---
title: 多组织单细胞整合流程
date: 2026-09-16
---

这是一批多组织单细胞数据的整合流程，34 个文库、8 个组织、约 19 万个细胞，从逐个文库的表达矩阵做到批次校正之后的统一聚类。流程里最容易出问题的往往不是分析本身，而是去双细胞和批次校正这两步的先后顺序和阈值，错了不报错，只是细胞悄悄变少，或者聚类结果跟着文库走。

同一物种做多个组织、分多批建库的单细胞测序时，文库之间叠着建库批次、测序质量和组织本身的转录组差异。如果每个文库单独聚类，同一类细胞会在不同文库变成不同的 cluster，跨组织的比较也就无从谈起。所以流程的顺序是先去双细胞，每个文库单独判，再合并起来按文库做整合、消除批次，最后把整合后的 UMAP 和逐文库、逐组织的 QC 摆在一起看整合是否做干净。

## 双细胞去除

双细胞是两个细胞被同一个液滴包住，测出来的表达谱是两个类型的叠加，聚类时会自己形成一个中间态 cluster，或者把两个真实类型连起来。它必须逐文库判断，不能合并之后一起做，合并之后，文库之间的批次差异会被 DoubletFinder 当成异常信号，识别结果不可用。

每个文库的质控阈值和去双细胞写成同一个函数，逐文库调用，

```r
library(Seurat)
process_library <- function(file_path, lib_id, tissue_name) {
  obj <- readRDS(file_path)
  DefaultAssay(obj) <- "RNA"
  obj[["integrated"]] <- NULL
  for (r in names(obj@reductions)) obj@reductions[[r]] <- NULL
  obj <- DietSeurat(obj, assays = "RNA")
  obj$lib <- lib_id
  obj$sample <- tissue_name
  min_gene <- if (tissue_name == "root") 300 else 500
  obj <- subset(obj, subset = nFeature_RNA > min_gene & nFeature_RNA < 9000 & nCount_RNA > 300 & nCount_RNA < 70000)
}
```

- `DefaultAssay(obj) <- "RNA"`，只保留 RNA assay。上游如果做过整合，integrated assay 里存的校正后表达值会让 DoubletFinder 的双细胞率估计失真。
- `obj@reductions[[r]] <- NULL` 与 `DietSeurat`，丢掉降维结果和其它 assay，减少内存占用。34 个文库逐个处理，每个文库留着旧降维结果很容易撑爆内存。
- `obj$lib` 与 `obj$sample`，把文库号和所属组织写进元数据。组织名此时就带上，后面按组织调阈值、按组织看整合效果都靠它。
- `if (tissue_name == "root") 300 else 500`，根这类 RNA 含量低的组织放宽基因数下限，统一阈值会把根切掉一大半。
- `nFeature_RNA < 9000`，检测基因数上限，用于去掉双细胞和核聚集。这个值要按物种和建库版本调。
- `nCount_RNA > 300 & nCount_RNA < 70000`，UMI 数的上下限，与基因数一起用，单看基因数会把高表达低复杂度的细胞误删。

拿到干净的对象之后再跑双细胞识别，

```r
library(DoubletFinder)
tmp <- NormalizeData(obj, verbose = FALSE)
tmp <- FindVariableFeatures(tmp, nfeatures = 2000, verbose = FALSE)
tmp <- ScaleData(tmp, features = VariableFeatures(tmp), verbose = FALSE)
tmp <- RunPCA(tmp, npcs = 30, verbose = FALSE)
sweep.res <- paramSweep(tmp, PCs = 1:20, sct = FALSE, num.cores = 1)
sweep.stats <- summarizeSweep(sweep.res, GT = FALSE)
bcmvn <- find.pK(sweep.stats)
pK_val <- as.numeric(as.vector(bcmvn[bcmvn$MeanBC == max(bcmvn$MeanBC), ]$pK))[1]
nExp_poi <- round(0.008 * (ncol(tmp)/1000) * ncol(tmp))
tmp <- doubletFinder(tmp, PCs = 1:20, pN = 0.25, pK = pK_val, nExp = nExp_poi, sct = FALSE)
```

- `nfeatures = 2000`，高变基因数量，也就是在细胞之间变异最大的那批基因，降维和双细胞识别都靠它们。取太大掺进噪音，取太小丢掉细胞类型特异基因。
- `paramSweep(tmp, PCs = 1:20, sct = FALSE)`，扫描不同的 pK 值，为每个 pK 生成一套人工双细胞的分类结果。
- `summarizeSweep` 与 `find.pK`，把扫描结果汇总成 BCmvn 曲线，这里直接取 BCmvn 最大值对应的 pK，不画图。
- `pN = 0.25`，人工生成的双细胞比例，DoubletFinder 的默认值，一般不用改。
- `pK_val`，邻域大小，不同文库的细胞数和复杂度差别很大，固定 pK 会让某些文库过度去除或去除不足，所以由 find.pK 逐文库给出。
- `nExp_poi`，预期双细胞数。10x 的双细胞率约为每 1000 个细胞 0.8%，公式是 0.008 乘以细胞数除以 1000 再乘以细胞数。
- `sct = FALSE`，不用 SCTransform 的标准化结果，与前面 NormalizeData 的处理保持一致。

pK 定下来之后给这个文库跑一遍分类，判定 singlet 和 doublet：

```r
df_col <- grep("^DF.classifications", colnames(tmp@meta.data), value = TRUE)
obj_clean <- subset(obj, cells = colnames(tmp)[tmp@meta.data[[df_col]] == "Singlet"])
saveRDS(obj_clean, file = file.path("results/removed_doublet", paste0(lib_id, ".rds")))
```

- `grep("^DF.classifications", ...)`，DoubletFinder 把 pN、pK 拼进列名，列名随细胞数和参数变化，写死列名会取不到，所以按前缀找。
- `subset(obj, cells = ...)`，取子集时用的是原对象而不是 tmp，tmp 只用来做识别，标准化和降维结果不带到下游。
- 每个文库的 singlet 单独存一份文件，文件名就是文库号，后面合并时按文件名取。

顺手把每个文库过滤前后的细胞数记下来，汇总放到最后：

```r
qc_before <- data.frame(library = lib_id, tissue = tissue_name, cells_before = ncol(obj),
                        total_UMI_before = sum(obj$nCount_RNA), median_UMI_before = median(obj$nCount_RNA),
                        median_genes_before = median(obj$nFeature_RNA))
qc_after  <- data.frame(library = lib_id, tissue = tissue_name, cells_after = ncol(obj_clean),
                        total_UMI_after = sum(obj_clean$nCount_RNA), median_UMI_after = median(obj_clean$nCount_RNA),
                        median_genes_after = median(obj_clean$nFeature_RNA))
qc_summary <- merge(qc_before, qc_after, by = c("library", "tissue"), all = TRUE)
write.csv(qc_summary, "results/doublet_removal_qc.csv", row.names = FALSE)
```

- 去双细胞前后的细胞数、UMI 总和、UMI 中位数、基因数中位数全部记录，按文库合并成一张表。
- 判读这张表看两点，某个文库去除比例明显高于其它文库，先查是不是建库质量问题；某个组织去得特别少，可能是双细胞率被低估。
- `all = TRUE`，两个数据框按文库号合并，缺一侧的文库不会静默丢掉。

## 批次整合与聚类

批次效应是不同文库之间由实验操作和测序带来的系统性差异，它和要比较的生物学差异混在同一个矩阵里。所以按文库校正，把批次扣掉，生物学差异留着。植物分生组织类细胞增殖活跃，细胞周期基因是主要变异来源，会把同一类型按周期相位劈成两个 cluster，先做细胞周期打分，把它当成已知的变异处理。

```r
rds_files <- list.files("results/removed_doublet", pattern = "\\.rds$", full.names = TRUE)
obj_list <- lapply(rds_files, readRDS)
scRNA <- merge(x = obj_list[[1]], y = obj_list[-1], add.cell.ids = gsub("\\.rds$", "", basename(rds_files)))
scRNA <- JoinLayers(scRNA)
scRNA <- NormalizeData(scRNA, verbose = FALSE)
scRNA <- FindVariableFeatures(scRNA, nfeatures = 2000, verbose = FALSE)
```

- `list.files("results/removed_doublet")`，直接列出上一步的全部产物，文库数量变了不用改脚本。
- `add.cell.ids`，给每个细胞的 barcode 加文库前缀，避免不同文库的 barcode 重名互相覆盖。前缀用文件名去掉扩展名，与元数据里的 `lib` 一致。
- `JoinLayers`，Seurat v5 把分层存储的计数矩阵合成一层，v5 之前不需要这一步。
- `NormalizeData` 放在合并之后做，所有文库用同一套参数，避免每批各归各的之后再合并导致不可比。
- `nfeatures = 2000`，高变基因数量，聚类和降维都靠它们。

合并之后先做细胞周期打分，处在不同周期的同类细胞会在 PCA 上分开：

```r
s_genes   <- read.table("gene_list/pal_S.txt", header = FALSE)$V1
g2m_genes <- read.table("gene_list/pal_G2M.txt", header = FALSE)$V1
scRNA <- CellCycleScoring(scRNA, s.features = s_genes, g2m.features = g2m_genes)
scRNA <- ScaleData(scRNA, features = VariableFeatures(scRNA), verbose = FALSE)
scRNA <- RunPCA(scRNA, npcs = 50, verbose = FALSE)
```

- `read.table(header = FALSE)$V1`，基因列表一行一个基因名，没有表头，取第一列就是基因。
- `CellCycleScoring`，给每个细胞打 S 期和 G2M 期得分。基因列表要用同物种或近缘物种的，人鼠的列表直接拿来用效果很差。
- `ScaleData(features = VariableFeatures(scRNA))`，只对高变基因做标准化，全基因做又慢又没必要。
- `npcs = 50`，先算 50 个主成分，后面只用前 20 个，多算的部分用来看各主成分解释的方差，判断取几个合适。

主成分有了就按文库号做批次校正，这是整段流程的核心一步：

```r
library(harmony)
scRNA <- RunHarmony(scRNA, group.by.vars = "lib", sigma = 0.05)
scRNA <- FindNeighbors(scRNA, reduction = "harmony", dims = 1:20)
scRNA <- FindClusters(scRNA, resolution = 2)
scRNA <- RunUMAP(scRNA, reduction = "harmony", dims = 1:20, reduction.name = "umap_harmony")
saveRDS(scRNA, "results/harmony.rds")
```

- `group.by.vars = "lib"`，按文库校正。这里填的必须是批次变量，填成组织会把这个研究要比较的生物学差异一起扣掉。
- `sigma = 0.05`，校正强度，值越大校正越强。偏小意味着假设文库间差异不大。如果某个文库明显离群，先查是不是组织或建库质量的问题，不要急着加大 sigma。
- `dims = 1:20`，用校正后的前 20 个主成分建邻接图。主成分太少会丢掉细胞类型间的细微差别，太多会引入噪音并让图变得过于连通。
- `resolution = 2`，聚类分辨率，取高是有意的。先过度聚类，再用各 cluster 的组织构成判断哪些该合，比一开始就用低分辨率更可控。
- `reduction.name = "umap_harmony"`，单独命名，便于和后面逐文库跑的 UMAP 对比，也避免和默认的 `umap` 混淆。
- `saveRDS`，把对象整体存下来，后面的出图和检查都直接读它，不用重算。

## 整合效果检查

聚类跑完先看 UMAP，分别画整合后和逐文库两张图，确认 cluster 由细胞类型而不是文库驱动。

```r
library(scales)

n_color <- length(unique(scRNA$seurat_clusters))
my_colors <- hue_pal()(n_color)
tissues <- sort(unique(scRNA$sample))
tissue_colors <- setNames(hue_pal()(length(tissues)), tissues)

p1 <- DimPlot(scRNA, reduction = "umap_harmony", group.by = "seurat_clusters",
              label = TRUE, pt.size = 0.05, raster = FALSE, cols = my_colors)
p2 <- DimPlot(scRNA, reduction = "umap_harmony", group.by = "sample", pt.size = 0.05, raster = FALSE, cols = tissue_colors)
pdf("results/harmony_umap.pdf", width = 22, height = 10)
print(p1 + p2)
dev.off()
```

- 两组颜色在第一段里定好，后面的分面图和小提琴图直接用，不用每张图重新调色。
- `setNames(hue_pal()(...), tissues)`，组织配色带名字，`scale_fill_manual` 才能按组织名对上号。
- `group.by = "seurat_clusters"`，左图按 cluster 着色，看过度聚类之后的分群是否连成一片。
- `group.by = "sample"`，右图按组织着色。如果每个 cluster 主要由某一个文库或组织占据，说明批次没校正干净。
- `pt.size = 0.05` 与 `raster = FALSE`，十几万个细胞按默认点大小会糊成一片，点调小并保持矢量输出，放大后还能看清局部。
- 两张图放在同一张 PDF 里对比，着色变量不同、坐标完全相同。

整张 UMAP 之外还要看每个文库自己的分布，把同一套坐标拆成小图：

```r
library(ggplot2)
umap_df <- as.data.frame(Embeddings(scRNA, reduction = "umap_harmony"))
colnames(umap_df) <- c("UMAP_1", "UMAP_2")
umap_df$sample <- scRNA$sample
umap_df$cluster <- scRNA$seurat_clusters
p_split <- ggplot(umap_df, aes(x = UMAP_1, y = UMAP_2)) +
  geom_point(data = umap_df[, c("UMAP_1", "UMAP_2")], color = "grey80", size = 0.01, alpha = 0.3) +
  geom_point(aes(color = cluster), size = 0.05) +
  facet_wrap(~sample, ncol = 4)
ggsave("results/harmony_umap_tissue_split.pdf", p_split, width = 22, height = 11, limitsize = FALSE)
```
- 灰色底层是所有细胞，彩色点是该组织的细胞。每个分面单独看该组织在整体 UMAP 上占哪些位置，比按组织着色一张图更好判断。
- `alpha = 0.3`，底层点调透明，否则会盖住彩色点。
- 分面图单独存一张 PDF，和上面两张图一起看，哪个组织在整体 UMAP 上占了不该占的位置一眼能看出来。
- `Embeddings(scRNA, "umap_harmony")`，把坐标取成数据框，画分面图要在 ggplot 里做，Seurat 的 DimPlot 不支持这种叠加。

逐文库的 QC 小提琴图一次看完全部文库，

```r
library(patchwork)
p_vln_list <- lapply(c("nFeature_RNA", "nCount_RNA"), function(f_name) {
  ggplot(scRNA@meta.data, aes(x = sample, y = .data[[f_name]], fill = sample)) +
    geom_violin(trim = TRUE, scale = "width", color = NA, adjust = 0.8) +
    geom_boxplot(width = 0.1, fill = "white", color = "black", outlier.shape = NA, coef = 0) +
    scale_fill_manual(values = tissue_colors)
})
p_qc_vln <- wrap_plots(p_vln_list, ncol = 2)
ggsave("results/qc_library_vlnplot.pdf", p_qc_vln, width = 10.6, height = 10, limitsize = FALSE)
```

- `scale = "width"`，每个组织的小提琴宽度一致，组织之间比的是分布形状而不是细胞数。
- `adjust = 0.8`，核密度估计的带宽，调小能看出双峰。双峰往往说明该组织里混着两类质量差异很大的细胞，或者整合没做干净。
- `geom_boxplot(coef = 0)`，叠一层箱线图，箱体表示四分位距，与分布形状一起看，受长尾影响时读数更稳。
- 基因数与 UMI 数两条并排，看两个指标是否一致。基因数正常而 UMI 数异常，通常是测序深度问题。

文库之间的一致性还可以用伪 bulk 的相关矩阵检查，

```r
lib_avg <- AverageExpression(scRNA, assays = "RNA", layer = "data", group.by = "lib")$RNA
lib_avg <- as.matrix(lib_avg)
colnames(lib_avg) <- gsub("-", "_", colnames(lib_avg))
lib_cor <- cor(lib_avg, method = "spearman")
```

- `AverageExpression(group.by = "lib")`，把每个文库的表达量按文库平均，得到文库水平的伪 bulk，比单细胞层面的相关性稳。
- `method = "spearman"`，用秩相关，对表达量的整体缩放不敏感。
- `gsub("-", "_", ...)`，文库名前缀里带短横线与其它符号冲突，统一成下划线避免列名解析出错。
- 同一组织的文库之间相关应该高，组织之间的相关低。出现同一组织的两个文库互相不相关，说明其中一个文库有问题，后面所有跨组织比较都会受影响。
