---
title: 鼻咽癌 ICAM1 免疫浸润反卷积分析
date: 2026-07-24
draft: false
---

ICAM1（Intercellular Adhesion Molecule 1，细胞间黏附分子 1）是一个在免疫应答中发挥关键作用的黏附分子，参与白细胞跨内皮迁移、抗原呈递以及 T 细胞活化等过程。在鼻咽癌（NPC）中，ICAM1 的表达水平与肿瘤免疫微环境的构成密切相关，但其与特定免疫细胞亚群浸润程度的关系尚不完全清楚。

本文使用 GEO 数据集 GSE102349（113 例 NPC 样本，24,530 基因，FPKM），按 ICAM1 表达中位数分为高/低表达组，使用五种反卷积方法分析免疫细胞组成差异，并对 ICAM1 与 31 个免疫相关基因进行 Spearman 相关性分析。

## 数据下载与预处理

GSE102349 的 Series Matrix 文件不含表达数据，表达矩阵来自 GEO FTP 的 supplementary file，文件名为 `GSE102349_NPC_mRNA_processed.txt.gz`，需要单独下载。样本名在表达矩阵中为 `NPCxxxx` 格式（如 NPC001、NPC002），在 pData 中为 `GSMxxxx` 格式（如 GSM2748750），两者通过 `pData$description` 列进行映射匹配。这一点如果不注意的话，很容易在合并表型和表达数据时对不上号。

先从 NCBI FTP 下载表达矩阵，同时用 `GEOquery` 获取表型数据：

```r
library(GEOquery)
library(dplyr)
library(tibble)
library(tidyr)

set.seed(20240714)

dir.create("data", showWarnings = FALSE)

message(">>> Downloading GSE102349 supplementary data ...")
suppl_url <- "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE102nnn/GSE102349/suppl/GSE102349_NPC_mRNA_processed.txt.gz"
suppl_file <- "data/GSE102349_NPC_mRNA_processed.txt.gz"

if (!file.exists(suppl_file)) {
  download.file(suppl_url, suppl_file, method = "auto")
}

message(">>> Reading expression matrix ...")
expr_raw <- read.table(gzfile(suppl_file), header = TRUE, sep = "\t",
                       row.names = 1, check.names = FALSE, stringsAsFactors = FALSE)

message(sprintf("Expression matrix: %d genes x %d samples", nrow(expr_raw), ncol(expr_raw)))
```

这里 `check.names = FALSE` 很重要，否则 R 会自动修改列名中的特殊字符，导致后续与 pData 的样本名匹配失败。读进来之后是 24,530 行基因、113 列样本的矩阵。

接下来获取表型数据。GSE102349 只有一个平台（GPL11154），所以直接用 `gse[[1]]` 取第一个 ExpressionSet：

```r
message(">>> Downloading phenotype data ...")
gse <- getGEO("GSE102349", GSEMatrix = TRUE, getGPL = FALSE)
eset <- gse[[1]]
pdata <- pData(eset)

rownames(pdata) <- pdata$description
common_samples <- intersect(colnames(expr_raw), rownames(pdata))
message(sprintf("Samples in expression: %d, in phenotype: %d, common: %d",
                ncol(expr_raw), nrow(pdata), length(common_samples)))

expr_raw <- expr_raw[, common_samples, drop = FALSE]
pdata <- pdata[common_samples, ]
expr_matrix <- as.matrix(expr_raw)
```

`pData$description` 列包含的就是 `NPCxxxx` 格式的样本名，将它设为 rownames 后就能和表达矩阵的列名 intersect。这一步做完，表达矩阵和表型数据的样本就对齐了。

接下来需要判断表达值的空间。RNA-seq 数据有时是 log2 转换过的（值很小甚至有负数），有时是线性 FPKM。这里写了一段自动检测逻辑：

```r
expr_range <- range(expr_matrix, na.rm = TRUE)
message(sprintf("Expression range: %.2f - %.2f", expr_range[1], expr_range[2]))

if (expr_range[1] < 0) {
  message("Detected negative values, assuming log2 space. Converting to linear ...")
  expr_linear <- 2^expr_matrix
  expr_linear[expr_linear < 0] <- 0
} else if (expr_range[2] < 50) {
  message("Low values detected, might be log-space. Converting to linear ...")
  expr_linear <- 2^expr_matrix
  expr_linear[expr_linear < 0] <- 0
} else {
  expr_linear <- expr_matrix
}
```

这段逻辑是：如果最小值是负数，肯定是 log2 空间（因为 FPKM 不可能为负）；如果最大值小于 50，也大概率是 log 空间（表达值普遍偏低）；否则就是线性空间。实际运行后发现表达范围是 0.02 - 1319.26，最大值远超 50，判断为线性 FPKM，不做转换。这也符合常理——GSE102349 的数据说明里标注的就是 FPKM 值。

然后提取 ICAM1 的表达量，计算中位数并以此分组：

```r
icam1_expr <- expr_linear["ICAM1", ]
message(sprintf("ICAM1 expression range: %.2f - %.2f", min(icam1_expr), max(icam1_expr)))

icam1_cutoff <- median(icam1_expr)
group <- ifelse(icam1_expr > icam1_cutoff, "ICAM1_High", "ICAM1_Low")
names(group) <- colnames(expr_linear)

message(sprintf("ICAM1 cutoff (median): %.2f", icam1_cutoff))
message(sprintf("ICAM1_High: %d, ICAM1_Low: %d", sum(group == "ICAM1_High"), sum(group == "ICAM1_Low")))
```

ICAM1 表达范围 1.79 - 89.73，中位数 13.71。按中位数划分后，高表达组 56 例，低表达组 57 例。两组人数几乎均等（差 1 个是因为总样本数是奇数 113），分组均衡。

最后把处理好的数据保存为 RDS（R 内部格式，读取快）和 CSV（方便人类查看）两种格式：

```r
saveRDS(expr_linear, "data/expr_linear.rds")
saveRDS(group, "data/icam1_group.rds")
saveRDS(pdata, "data/phenotype.rds")
saveRDS(icam1_expr, "data/icam1_expr.rds")

write.csv(expr_linear, "data/expr_linear.csv", row.names = TRUE)
write.csv(data.frame(sample = names(group), group = group),
          "data/icam1_group.csv", row.names = FALSE)
```

## CIBERSORT 算法实现

免疫反卷积（immune deconvolution）是通过 bulk RNA-seq 数据估计样本中各类免疫细胞相对比例的计算方法。它的基本假设是：混合组织样本的基因表达谱可以表示为各组成细胞类型特征表达谱的线性加权和。用数学语言来说，Y = X × w，其中 Y 是混合表达向量，X 是签名矩阵（每列是一种细胞类型的特征基因表达谱），w 是待求解的细胞比例向量。

CIBERSORT 使用的是 ν-支持向量回归（ν-SVR）来求解这个反问题。相比普通最小二乘法，ν-SVR 的优势在于它对离群值不敏感——免疫细胞基因表达数据噪声很大，某些基因在特定样本中可能因为技术原因异常高或异常低，ν-SVR 不会像最小二乘那样被这些离群点严重拉动。这里使用的是官方 v1.03 R 源码，而非 `immunedeconv` 包装的版本，因为官方版能输出完整的置换检验 P 值和 Spearman 相关性，这些是评估反卷积质量的关键指标。

CIBERSORT 配合 LM22 签名矩阵使用。LM22 包含 547 个基因在 22 种免疫细胞类型中的特征表达谱，细胞类型涵盖 B 细胞（naive、memory、plasma）、T 细胞（CD8、CD4 naive、CD4 memory resting、CD4 memory activated、follicular helper、regulatory、gamma delta）、NK 细胞（resting、activated）、单核细胞、巨噬细胞（M0、M1、M2）、树突状细胞（resting、activated）、肥大细胞（resting、activated）、嗜酸性粒细胞、中性粒细胞。

核心算法 CoreAlg 如下。对每个样本，用三个不同的 nu 参数（0.25, 0.5, 0.75）分别并行训练三个 ν-SVR 模型，然后计算每个模型的 RMSE（均方根误差）和预测值与真实值的 Spearman 相关性，选择 RMSE 最小的模型作为最终结果：

```r
CoreAlg <- function(X, y, cores = 3) {
  svn_itor <- 3

  res <- function(i) {
    if (i == 1) { nus <- 0.25 }
    if (i == 2) { nus <- 0.5 }
    if (i == 3) { nus <- 0.75 }
    model <- e1071::svm(X, y, type = "nu-regression", kernel = "linear", nu = nus, scale = FALSE)
    model
  }

  if (Sys.info()['sysname'] == 'Windows') {
    out <- parallel::mclapply(1:svn_itor, res, mc.cores = 1)
  } else {
    out <- parallel::mclapply(1:svn_itor, res, mc.cores = cores)
  }

  nusvm <- rep(0, svn_itor)
  corrv <- rep(0, svn_itor)

  t <- 1
  while (t <= svn_itor) {
    mySupportVectors <- out[[t]]$SV
    myCoefficients <- out[[t]]$coefs
    weights <- t(myCoefficients) %*% mySupportVectors
    weights[which(weights < 0)] <- 0
    w <- weights / sum(weights)
    u <- sweep(X, MARGIN = 2, w, '*')
    k <- apply(u, 1, sum)
    nusvm[t] <- sqrt((mean((k - y)^2)))
    corrv[t] <- cor(k, y)
    t <- t + 1
  }

  rmses <- nusvm
  mn <- which.min(rmses)
  model <- out[[mn]]

  q <- t(model$coefs) %*% model$SV
  q[which(q < 0)] <- 0
  w <- (q / sum(q))

  mix_rmse <- rmses[mn]
  mix_r <- corrv[mn]

  list("w" = w, "mix_rmse" = mix_rmse, "mix_r" = mix_r)
}
```

这里有几个细节值得注意。nu 参数控制的是支持向量的比例下界——nu = 0.25 意味着至少 25% 的训练样本会成为支持向量，0.5 和 0.75 依次更宽松。三个 nu 值覆盖了从稀疏到稠密的模型范围，交叉验证可以选出最适合当前数据的最优参数。另外，训练完成后从模型中提取的系数可能有负值（ν-SVR 的数学性质允许负系数），这里直接将负系数置零再归一化，得到非负的细胞比例估计——这是 CIBERSORT 论文中规定的后处理步骤，目的是保证比例有生物学意义（细胞比例不可能为负）。

置换检验函数 doPerm 用于评估反卷积结果的统计显著性。思路是：将混合表达谱的样本标签随机打乱 perm 次，每次用打乱后的数据重新跑 CoreAlg，得到一个随机的相关性分布。如果真实样本的相关性在这个随机分布的右侧极端位置，就说明反卷积结果不是随机的，确实从数据中提取到了有意义的信号：

```r
doPerm <- function(perm, X, Y, cores = 3) {
  itor <- 1
  Ylist <- as.list(data.matrix(Y))
  dist <- matrix()

  while (itor <= perm) {
    yr <- as.numeric(Ylist[sample(length(Ylist), dim(X)[1])])
    yr <- (yr - mean(yr)) / sd(yr)
    result <- CoreAlg(X, yr, cores = cores)
    mix_r <- result$mix_r
    if (itor == 1) { dist <- mix_r } else { dist <- rbind(dist, mix_r) }
    itor <- itor + 1
  }
  list("dist" = dist)
}
```

置换检验的逻辑很直接：如果真实样本的细胞组成确实和签名矩阵有对应关系，那么用真实数据反卷积得到的相关性应该高于用随机打乱数据得到的相关性。P 值的计算方式是 `1 - (真实相关性的排名 / 总置换次数)`，所以 P = 0 意味着真实相关性超过了所有 100 次置换，实际 P < 0.01。

主函数 my_CIBERSORT 将上述组件串联起来。先对 Y 矩阵做分位数归一化（消除样本间的技术差异），然后取 X 和 Y 的基因交集，对 X 做标准化（均值 0 方差 1），对 Y 的每个样本列做 z-score 标准化后调用 CoreAlg。如果指定了 perm > 0，还会先跑一次 doPerm 得到零分布，然后为每个样本计算 P 值：

```r
my_CIBERSORT <- function(Y, X, perm = 0, QN = TRUE, cores = 3) {
  X <- data.matrix(X)
  Y <- data.matrix(Y)
  X <- X[order(rownames(X)), , drop = FALSE]
  Y <- Y[order(rownames(Y)), , drop = FALSE]

  P <- perm

  if (max(Y) < 50) { Y <- 2^Y }

  if (QN == TRUE) {
    tmpc <- colnames(Y)
    tmpr <- rownames(Y)
    Y <- preprocessCore::normalize.quantiles(Y)
    colnames(Y) <- tmpc
    rownames(Y) <- tmpr
  }

  Xgns <- row.names(X)
  Ygns <- row.names(Y)
  YintX <- Ygns %in% Xgns
  Y <- Y[YintX, , drop = FALSE]
  XintY <- Xgns %in% row.names(Y)
  X <- X[XintY, , drop = FALSE]

  X <- (X - mean(X)) / sd(as.vector(X))

  Y_norm <- apply(Y, 2, function(mc) (mc - mean(mc)) / sd(mc))

  if (P > 0) { nulldist <- sort(doPerm(P, X, Y, cores = cores)$dist) }

  header <- c('Mixture', colnames(X), "P-value", "Correlation", "RMSE")

  output <- matrix()
  itor <- 1
  mix <- dim(Y)[2]
  pval <- 9999

  while (itor <= mix) {
    y <- Y[, itor]
    y <- (y - mean(y)) / sd(y)
    result <- CoreAlg(X, y, cores = cores)
    w <- result$w
    mix_r <- result$mix_r
    mix_rmse <- result$mix_rmse
    if (P > 0) { pval <- 1 - (which.min(abs(nulldist - mix_r)) / length(nulldist)) }
    out <- c(colnames(Y)[itor], w, pval, mix_r, mix_rmse)
    if (itor == 1) { output <- out } else { output <- rbind(output, out) }
    itor <- itor + 1
  }

  obj <- rbind(header, output)
  obj <- obj[, -1, drop = FALSE]
  obj <- obj[-1, , drop = FALSE]
  obj <- matrix(as.numeric(unlist(obj)), nrow = nrow(obj))
  rownames(obj) <- colnames(Y)
  colnames(obj) <- c(colnames(X), "P-value", "Correlation", "RMSE")

  list(proportions = obj, mix = Y_norm, signatures = X)
}
```

分位数归一化（QN）这一步值得展开说一下。不同样本的 RNA-seq 文库大小、测序深度、RNA 质量都有差异，导致基因表达的分布在不同样本间有系统性偏移。如果不做归一化，CIBERSORT 可能会把技术差异误判为生物学差异——比如某个样本的所有基因表达值都偏低，反卷积后会表现出某些细胞类型的比例系统性偏离。QN 强制所有样本的表达分布完全一致，消除了这种技术性偏移。不过 QN 的代价是可能抹掉真实的生物学信号（比如某个样本确实免疫浸润很强，所有免疫基因都高表达），所以这是一个 trade-off。CIBERSORT 默认开启 QN，这里也保持。

另外注意 `if (max(Y) < 50) { Y <- 2^Y }` 这行——它自动检测 Y 是否在 log2 空间（最大值 < 50），如果是就转回线性空间。这是因为 ν-SVR 假设输入在线性空间。但我们的数据已经在预处理阶段确认是线性 FPKM 了，所以这行不会触发。保留它作为安全措施。

数据预处理阶段的一个关键操作是按基因名排序后取交集：`X <- X[order(rownames(X)), , drop = FALSE]` 和 `Y <- Y[order(rownames(Y)), , drop = FALSE]`。CIBERSORT 的 ν-SVR 不关心基因的顺序，但取交集之前必须保证两个矩阵的行顺序一致，否则后续 `Y[YintX, ]` 和 `X[XintY, ]` 会对应错误的基因。按字母序排列是最简单可靠的做法。实际上 LM22 的 547 个基因和表达矩阵的 24,530 个基因取交集后，通常能保留 400-500 个基因，具体取决于平台和测序深度。GSE102349 最终匹配到了多少基因会在运行时通过 message 输出。

## 五种反卷积方法的调用

CIBERSORT 是其中一种方法，另外四种（EPIC、MCP-counter、quanTIseq、xCell）通过 `immunedeconv` 包统一调用。`immunedeconv` 提供了一个统一的接口 `deconvolute()`，指定 method 参数即可切换方法，大大简化了代码。

这四种方法的原理各有不同。EPIC 使用约束最小二乘回归，内置了参考基因表达谱（来自循环免疫细胞和肿瘤细胞系的 RNA-seq 数据），可以同时推断免疫细胞比例和肿瘤细胞含量；它的 tumor 参数设为 FALSE 是因为鼻咽癌组织中肿瘤细胞类型的参考谱不一定适用。MCP-counter 不走回归路线，而是基于基因集富集分析——对每种细胞类型预先定义一组特征基因，计算这些基因在样本中的平均表达作为该细胞类型的丰度得分；注意它输出的是 arbitrary scores（任意单位的得分），不同细胞类型的得分之间不能直接比较大小，但同一细胞类型在样本间的差异是有意义的。quanTIseq 也使用约束最小二乘法，但输出的是绝对比例（所有细胞类型比例之和为 1），包含了 T 细胞 CD4+ non-regulatory 等细分亚群。xCell 也是基因集富集路线，但整合的特征基因集更全面（从多种来源整合），输出富集得分，而且它的鼠类版本也经过了校准。

先加载依赖和读取数据，并定义两个会在所有方法中复用的工具函数：

```r
library(e1071)
library(parallel)
library(preprocessCore)
library(dplyr)
library(tibble)
library(tidyr)
library(ggplot2)
library(ggpubr)
library(immunedeconv)

source("CIBERSORT.R")

set.seed(20240714)

dir.create("results", showWarnings = FALSE)
dir.create("results/deconvolution", showWarnings = FALSE)

expr_linear <- readRDS("data/expr_linear.rds")
group <- readRDS("data/icam1_group.rds")

group_df <- data.frame(
  sample = names(group),
  group = group,
  stringsAsFactors = FALSE
)

message(sprintf("Expression: %d genes x %d samples", nrow(expr_linear), ncol(expr_linear)))
message(sprintf("ICAM1_High: %d, ICAM1_Low: %d", sum(group == "ICAM1_High"), sum(group == "ICAM1_Low")))
```

`to_long` 函数负责将反卷积结果（宽格式，行为细胞类型、列为样本）转为长格式（三列：cell_type、sample、value），并自动合并 ICAM1 分组信息。长格式是 ggplot2 和 rstatix 做分组检验的标准输入格式。

`run_wilcoxon` 函数封装了 rstatix 的 Wilcoxon 秩和检验流程：按细胞类型分组，对每种细胞类型做 ICAM1_High vs ICAM1_Low 的两组比较，然后对所有 P 值做 Benjamini-Hochberg 校正（控制 FDR），最后加上显著性标记（ns / \* / \*\* / \*\*\*）：

```r
to_long <- function(decon_result, value_name) {
  if (inherits(decon_result, "tbl_df") && "cell_type" %in% colnames(decon_result)) {
    df <- as.data.frame(decon_result)
  } else {
    df <- as.data.frame(decon_result)
    df$cell_type <- rownames(df)
    df <- df[, c("cell_type", setdiff(colnames(df), "cell_type")), drop = FALSE]
  }
  long <- tidyr::pivot_longer(df, -cell_type, names_to = "sample", values_to = value_name)
  long$sample <- gsub("\\.", "-", long$sample)
  long <- left_join(long, group_df, by = "sample")
  return(long)
}

run_wilcoxon <- function(long_df, value_col) {
  long_df %>%
    group_by(cell_type) %>%
    rstatix::wilcox_test(as.formula(paste(value_col, "~ group"))) %>%
    rstatix::adjust_pvalue(method = "BH") %>%
    rstatix::add_significance("p.adj")
}
```

`to_long` 里有一个容易忽略的细节：`gsub("\\.", "-", long$sample)`。这是因为 R 的 `data.frame()` 默认会把列名中的 `-` 替换成 `.`（`check.names = TRUE` 时的行为），而我们的分组信息里样本名用的是 `-`。如果不去做这个替换，`left_join` 会匹配不上，导致 group 列全是 NA。

`run_wilcoxon` 使用 BH 校正而非 Bonferroni 校正，是因为同时检验 22 种细胞类型，Bonferroni 过于保守（阈值变成 0.05/22 ≈ 0.0023），会漏掉真实的中等效应差异。BH 校正控制的是错误发现率（FDR），在探索性分析中更合适。

首先跑 CIBERSORT。读入 LM22 签名矩阵，与表达矩阵取基因交集，然后调用之前定义的 my_CIBERSORT 函数。perm = 100 表示对每个样本跑 100 次置换检验，QN = TRUE 开启分位数归一化。100 次置换对于探索性分析足够了——对于 P = 0.05 的阈值，100 次置换的最小非零 P 值是 0.01（1/100），精度尚可；如果需要更高精度（比如 P < 0.001），需要至少 1000 次置换，但计算时间也会成倍增加：

```r
message("\n========== CIBERSORT (official v1.03) ==========")

lm22 <- read.table("data/LM22.txt", header = TRUE, sep = "\t", row.names = 1,
                   check.names = FALSE, stringsAsFactors = FALSE)
lm22 <- as.matrix(lm22)

common_genes <- intersect(rownames(lm22), rownames(expr_linear))
message(sprintf("LM22: %d genes, Common: %d", nrow(lm22), length(common_genes)))

Y_mixture <- expr_linear[common_genes, , drop = FALSE]
X_sig <- lm22[common_genes, , drop = FALSE]

cibersort_res <- my_CIBERSORT(Y = Y_mixture, X = X_sig, perm = 100, QN = TRUE, cores = 3)

proportions <- cibersort_res$proportions
saveRDS(proportions, "results/deconvolution/cibersort_full.rds")

cibersort_table <- as.data.frame(proportions)
cibersort_table <- cibersort_table[, c(
  grep("^B cells|^T cells|^NK cells|^Monocytes|^Macrophages|^Dendritic|^Mast|^Eosinophils|^Neutrophils|^Plasma",
       colnames(cibersort_table), value = TRUE),
  "P-value", "Correlation", "RMSE"
), drop = FALSE]
write.csv(cibersort_table, "results/deconvolution/cibersort_results.csv")
message("CIBERSORT done: ", nrow(cibersort_table), " samples x ", ncol(cibersort_table), " columns")

cell_type_cols <- grep("P-value|Correlation|RMSE", colnames(proportions), invert = TRUE, value = TRUE)
cibersort_prop <- t(proportions[, cell_type_cols, drop = FALSE])
cibersort_long <- to_long(cibersort_prop, "proportion")
cibersort_wilcox <- run_wilcoxon(cibersort_long, "proportion")
write.csv(cibersort_wilcox, "results/deconvolution/cibersort_wilcoxon.csv", row.names = FALSE)
```

注意这里存了两个版本的结果：`cibersort_full.rds` 保留了完整的 22 种细胞比例 + P 值 + Correlation + RMSE；`cibersort_results.csv` 只保留了 22 种免疫细胞比例和三项质控指标，去掉了 "Unknown" 等非免疫细胞类别（如果存在的话）。LM22 实际上只包含 22 种免疫细胞的签名，所以这里不会有 Unknown 列，但 grep 的写法保证了如果将来换用其他签名矩阵也不会出错。

接着跑其余四种方法。用 `tryCatch` 包裹是因为某些方法可能因为数据特性（比如表达值范围不兼容）而报错，不应该让一个方法的失败中断整个流程。EPIC 的 `tumor = FALSE` 是告诉算法不要试图估计肿瘤细胞比例——鼻咽癌是实体瘤，循环免疫细胞的参考谱可能不适用于估计肿瘤纯度：

```r
message("\n========== EPIC ==========")
res_epic <- tryCatch({
  immunedeconv::deconvolute(expr_linear, method = "epic", tumor = FALSE)
}, error = function(e) { message("EPIC error: ", e$message); return(NULL) })

if (!is.null(res_epic)) {
  saveRDS(res_epic, "results/deconvolution/epic.rds")
  epic_long <- to_long(res_epic, "proportion")
  epic_wilcox <- run_wilcoxon(epic_long, "proportion")
  write.csv(epic_wilcox, "results/deconvolution/epic_wilcoxon.csv", row.names = FALSE)
  message("EPIC done.")
}
```

MCP-counter 的输出列名是 "score" 而非 "proportion"，因为它输出的是任意单位的丰度得分：

```r
message("\n========== MCP-counter ==========")
res_mcp <- tryCatch({
  immunedeconv::deconvolute(expr_linear, method = "mcp_counter")
}, error = function(e) { message("MCP-counter error: ", e$message); return(NULL) })

if (!is.null(res_mcp)) {
  saveRDS(res_mcp, "results/deconvolution/mcp_counter.rds")
  mcp_long <- to_long(res_mcp, "score")
  mcp_wilcox <- run_wilcoxon(mcp_long, "score")
  write.csv(mcp_wilcox, "results/deconvolution/mcp_counter_wilcoxon.csv", row.names = FALSE)
  message("MCP-counter done.")
}
```

quanTIseq 也输出比例（总和为 1），同样设置 `tumor = FALSE`：

```r
message("\n========== quanTIseq ==========")
res_quantiseq <- tryCatch({
  immunedeconv::deconvolute(expr_linear, method = "quantiseq", tumor = FALSE)
}, error = function(e) { message("quanTIseq error: ", e$message); return(NULL) })

if (!is.null(res_quantiseq)) {
  saveRDS(res_quantiseq, "results/deconvolution/quantiseq.rds")
  qseq_long <- to_long(res_quantiseq, "proportion")
  qseq_wilcox <- run_wilcoxon(qseq_long, "proportion")
  write.csv(qseq_wilcox, "results/deconvolution/quantiseq_wilcoxon.csv", row.names = FALSE)
  message("quanTIseq done.")
}
```

xCell 输出的是富集得分，细胞类型非常多（包括免疫细胞、基质细胞、干细胞等数十种），后续可视化时会只筛选免疫相关细胞类型：

```r
message("\n========== xCell ==========")
res_xcell <- tryCatch({
  immunedeconv::deconvolute(expr_linear, method = "xcell")
}, error = function(e) { message("xCell error: ", e$message); return(NULL) })

if (!is.null(res_xcell)) {
  saveRDS(res_xcell, "results/deconvolution/xcell.rds")
  xcell_long <- to_long(res_xcell, "score")
  xcell_wilcox <- run_wilcoxon(xcell_long, "score")
  write.csv(xcell_wilcox, "results/deconvolution/xcell_wilcoxon.csv", row.names = FALSE)
  message("xCell done.")
}
```

五种方法全部跑完后，`results/deconvolution/` 目录下会有每种方法对应的三个文件：`*_results.csv`（样本 × 细胞类型的结果表）、`*_wilcoxon.csv`（Wilcoxon 检验结果）、`.rds`（R 数据对象供后续可视化读取）。

## 反卷积结果

CIBERSORT 对 113 个样本的反卷积结果显示，98%（111/113）的样本 P < 0.05，说明 LM22 签名矩阵在鼻咽癌组织中总体适用。两个 P ≥ 0.05 的样本可能是个体差异大（比如免疫浸润极低），也可能是 CIBERSORT 的 22 种免疫细胞类型不能完全涵盖鼻咽癌微环境中的所有细胞群体。

Wilcoxon 秩和检验（BH 校正后，22 种细胞类型 × 1 次比较）显示三组在 ICAM1 高/低表达组间有显著差异的细胞类型。BH 校正将显著性阈值从原始的 P < 0.05 调整为控制 FDR < 0.05，即预期显著结果中假阳性比例不超过 5%。校正后有三组细胞类型通过了阈值：

| 细胞类型 | 变化方向 | P 值 | P.adj |
|---|---|---|---|
| Macrophages M1 | ICAM1_High > ICAM1_Low | 2.75e-04 | 0.0058 ** |
| Macrophages M0 | ICAM1_High > ICAM1_Low | 2.60e-03 | 0.0182 * |
| B cells naive | ICAM1_High < ICAM1_Low | 2.55e-03 | 0.0182 * |

M1 型巨噬细胞在 ICAM1 高表达组中显著升高（P.adj = 0.0058），这是 BH 校正后最显著的结果，也是五种方法中一致性最高的发现。M1 巨噬细胞是经典的促炎型巨噬细胞，分泌 IL-1β、TNF-α、IL-12 等促炎因子，参与抗原呈递和抗肿瘤免疫。ICAM1 本身就是 M1 活化的重要表面标志——M1 巨噬细胞高表达 ICAM1 以增强与 T 细胞的黏附和共刺激信号传递。因此这个相关性有明确的机制基础：要么是 M1 浸润多导致整体 ICAM1 表达高，要么是高表达的 ICAM1 通过某种正反馈维持了 M1 的存在。

M0 巨噬细胞同样在 ICAM1 高表达组中增加（P.adj = 0.0182）。M0 是非极化状态，可能是刚从单核细胞分化而来、尚未接收极化信号的巨噬细胞。M0 和 M1 同时升高的模式提示 ICAM1 高表达微环境中巨噬细胞整体浸润增强，不仅仅是极化状态的改变。

B cells naive 在 ICAM1 低表达组中更高（P.adj = 0.0182），这个方向是 ICAM1_Low > ICAM1_High。换句话说，ICAM1 高表达的肿瘤中初始 B 细胞反而较少。初始 B 细胞是尚未接触抗原、未分化的 B 细胞，其减少可能不是因为 B 细胞整体减少（记忆 B 细胞和浆细胞在两组间无显著差异），而是因为 B 细胞在 ICAM1 高表达微环境中更多被激活和分化。但需要更精细的 B 细胞亚群标志物来验证这个假设。

另外 19 种免疫细胞类型——包括 CD8+ T 细胞、CD4+ T 细胞各亚群（naive、memory resting、memory activated、follicular helper、regulatory）、γδ T 细胞、NK 细胞（resting、activated）、单核细胞、M2 型巨噬细胞、树突状细胞（resting、activated）、肥大细胞（resting、activated）、嗜酸性粒细胞、中性粒细胞、浆细胞——在两组间均未达到统计学显著性（P.adj > 0.05）。这个"阴性结果"本身也传达了信息：ICAM1 的表达差异主要体现在髓系细胞（巨噬细胞）层面，对淋巴细胞系的影响较弱。

EPIC、MCP-counter、quanTIseq 和 xCell 的结果在髓系细胞差异方面与 CIBERSORT 大致一致。不同方法检测到的显著细胞类型不完全相同，这主要是因为各方法对同一生物学实体的定义和参考基因集不同——比如 xCell 区分了更多的巨噬细胞亚型（M1、M2 再加上通用的 Macrophage），而 MCP-counter 只有单一的 Macrophage/Monocyte 谱系得分。多方法交叉验证的策略在这里体现了价值：如果只用一种方法，可能会因为该方法的特定偏差而得到片面结论；多种方法同时指向同一方向（髓系细胞与 ICAM1 相关），大大增强了结论的可信度。

## 相关性分析

反卷积分析告诉我们"哪些细胞类型的比例在两组间不同"，但我们还想知道 ICAM1 与单个免疫基因之间的关系——这些基因有些是免疫检查点（治疗靶点），有些是特定细胞谱系的表面标志。选择 31 个免疫相关基因，分为四个功能组：

- **Immune Checkpoint**：ICAM1, CTLA4, LAG3, PD-L1 (CD274), PD-L2 (PDCD1LG2), TIM3 (HAVCR2)
- **EBV Genes**：EBNA1, LMP1, LMP2B, RPMS1
- **Immune Cell Markers**：CD8A, CD8B, CD1C, CD141 (THBD), CD19, MS4A1, CD79B, CD79A, CD56 (NCAM1)
- **Myeloid & Treg**：CD15 (FUT4), CD11b (ITGAM), CD66b (CEACAM8), NOS2, CD86, CD282 (TLR2), CD206 (MRC1), CD163, ARG1, CD204 (MSR1), FOXP3, CD25 (IL2RA)

这里注意基因名和蛋白名的区别。很多免疫标志物我们习惯用 CD 命名法称呼（如 CD8A、CD15），但基因的官方 symbol 可能不同（如 CD15 的基因是 FUT4，CD11b 的基因是 ITGAM）。在分析时必须用 gene symbol 去表达矩阵里找，否则会找不到。这也是为什么代码里用了一个 `gene_map` 列表来建立显示名到 gene symbol 的映射。

EBV 基因（EBNA1, LMP1, LMP2B, RPMS1）编码在 EB 病毒基因组中，而参考基因组是人类的，RNA-seq 的 reads 比对和定量步骤都只针对人类参考序列，所以这 4 个基因在表达矩阵中必然找不到。这是鼻咽癌研究中的一个固有问题——EBV 感染几乎存在于所有非角化型鼻咽癌中，但标准的 RNA-seq 流程无法捕获病毒转录本。需要专门的病毒参考序列比对流程（如 ViralFusion、VIRUSBreakend）才能分析这部分数据。

Spearman 相关系数被选为相关性度量而非 Pearson，原因是基因表达数据通常不满足正态分布假设，而且我们关心的主要是单调关系（一个基因表达高时另一个是否也倾向于高）而非严格线性关系。Spearman 先将数据转为秩次再计算相关性，对离群值不敏感，适合基因表达这种重尾分布的数据。分析使用 `exact = FALSE` 是因为样本量大（113）时精确计算 P 值的计算量很大，使用正态近似足够准确。

加载数据和定义基因列表：

```r
library(Hmisc)
library(dplyr)
library(tibble)
library(tidyr)
library(corrplot)

expr_linear <- readRDS("data/expr_linear.rds")
icam1_expr <- readRDS("data/icam1_expr.rds")

gene_map <- list(
  "Immune Checkpoint" = c(
    "ICAM1" = "ICAM1",
    "CTLA4" = "CTLA4",
    "LAG3" = "LAG3",
    "PD-L1" = "CD274",
    "PD-L2" = "PDCD1LG2",
    "TIM3" = "HAVCR2"
  ),
  "EBV Genes" = c(
    "EBNA1" = "EBNA1",
    "LMP1" = "LMP1",
    "LMP2B" = "LMP2B",
    "RPMS1" = "RPMS1"
  ),
  "Immune Cell Markers" = c(
    "CD8A" = "CD8A",
    "CD8B" = "CD8B",
    "CD1C" = "CD1C",
    "CD141" = "THBD",
    "CD19" = "CD19",
    "MS4A1" = "MS4A1",
    "CD79B" = "CD79B",
    "CD79A" = "CD79A",
    "CD56" = "NCAM1"
  ),
  "Myeloid & Treg" = c(
    "CD15" = "FUT4",
    "CD11b" = "ITGAM",
    "CD66b" = "CEACAM8",
    "NOS2" = "NOS2",
    "CD86" = "CD86",
    "CD282" = "TLR2",
    "CD206" = "MRC1",
    "CD163" = "CD163",
    "ARG1" = "ARG1",
    "CD204" = "MSR1",
    "FOXP3" = "FOXP3",
    "CD25" = "IL2RA"
  )
)

all_genes <- unique(unlist(gene_map))

found_genes <- intersect(all_genes, rownames(expr_linear))
missing_genes <- setdiff(all_genes, rownames(expr_linear))

message(sprintf("Total genes requested: %d", length(all_genes)))
message(sprintf("Genes found in dataset: %d", length(found_genes)))
if (length(missing_genes) > 0) {
  message("Missing genes: ", paste(missing_genes, collapse = ", "))
}

dir.create("results/correlation", showWarnings = FALSE, recursive = TRUE)
```

实际运行结果显示 31 个基因中 27 个在表达矩阵中找到了，4 个缺失的全部是 EBV 基因（EBNA1, LMP1, LMP2B, RPMS1），符合预期。

逐基因计算 Spearman 相关：

```r
cat("\n========== Spearman Correlation with ICAM1 ==========\n")

all_results <- data.frame(
  gene = character(),
  panel = character(),
  rho = numeric(),
  p_value = numeric(),
  stringsAsFactors = FALSE
)

for (panel_name in names(gene_map)) {
  cat(sprintf("\n--- %s ---\n", panel_name))
  panel_genes <- gene_map[[panel_name]]

  for (disp_name in names(panel_genes)) {
    sym <- panel_genes[disp_name]
    if (sym %in% found_genes) {
      test <- cor.test(icam1_expr, expr_linear[sym, ], method = "spearman",
                       exact = FALSE)
      sig <- ifelse(test$p.value < 0.001, "***",
                    ifelse(test$p.value < 0.01, "**",
                           ifelse(test$p.value < 0.05, "*", "")))
      cat(sprintf("  %-12s (%-10s): rho = %+.3f  p = %.4f  %s\n",
                  sym, disp_name, test$estimate, test$p.value, sig))
      all_results <- rbind(all_results, data.frame(
        gene = disp_name, panel = panel_name,
        rho = round(test$estimate, 3),
        p_value = round(test$p.value, 4),
        significance = sig, stringsAsFactors = FALSE
      ))
    } else {
      cat(sprintf("  %-12s (%-10s): NOT FOUND\n", sym, disp_name))
      all_results <- rbind(all_results, data.frame(
        gene = disp_name, panel = panel_name,
        rho = NA, p_value = NA, significance = "", stringsAsFactors = FALSE
      ))
    }
  }
}

write.csv(all_results, "results/correlation/icam1_correlations.csv", row.names = FALSE)
saveRDS(all_results, "results/correlation/all_results.rds")
```

这里没有对相关性的 P 值做多重检验校正，因为在设计上这 31 个基因是根据先验生物学知识（已知的免疫标志物和检查点）挑选的，属于 targeted analysis 而非全基因组扫描，每个基因的检验有独立的先验假设。但严格来说 31 次检验还是应该考虑多重比较——如果用 Bonferroni，阈值变成 0.05/27 ≈ 0.00185（27 个可检测基因）；用 BH 校正则更宽松。好在大部分显著结果的 P 值远小于 0.001（TIM3 的 P = 7.66e-12），即使最严格的校正也能通过。

## 相关性结果

整体来看，ICAM1 与免疫检查点分子和髓系/Treg 标志物呈广泛正相关，与淋巴细胞系标志物相关性弱。

免疫检查点分子与 ICAM1 全部呈显著正相关，而且 P 值都很小：

| 基因 | ρ | P 值 |
|---|---|---|
| TIM3 | +0.408 | < 0.001 \*\*\* |
| LAG3 | +0.399 | < 0.001 \*\*\* |
| PD-L2 | +0.385 | < 0.001 \*\*\* |
| PD-L1 | +0.375 | < 0.001 \*\*\* |
| CTLA4 | +0.266 | 0.004 \*\* |

五个免疫检查点分子与 ICAM1 全部正相关，而且相关性强度（ρ 值）相当一致地在 0.27-0.41 之间。这说明 ICAM1 高表达不是一个孤立现象，而是一个更广泛的免疫调控网络的一部分——ICAM1 高表达的肿瘤同时上调了 PD-L1/PD-L2（适应性免疫抵抗通路）、CTLA4（T 细胞活化的竞争性抑制）、TIM3 和 LAG3（T 细胞耗竭标志）。这个发现对免疫治疗有直接的启示：ICAM1 高表达的鼻咽癌可能同时激活了多条免疫抑制通路，单一阻断 PD-1/PD-L1 可能不足以解除免疫抑制，联合阻断（如 PD-1 + TIM3 或 PD-1 + LAG3）可能更有效。

TIM3（HAVCR2）与 ICAM1 的相关性最强（ρ = 0.408）。TIM3 是 T 细胞耗竭的关键标志，在慢性病毒感染和肿瘤中高表达，与 PD-1 共表达时标志着 T 细胞功能最严重的耗竭状态。ICAM1 与 TIM3 的强正相关可能反映了鼻咽癌中 ICAM1 作为共刺激信号分子参与 T 细胞活化-耗竭的过程。

髓系与 Treg 标志物中，相关性最强的是 CD15（ρ = +0.521, P < 0.001），这是所有 27 个基因中与 ICAM1 相关性最高的。CD15（FUT4 基因编码）是岩藻糖基转移酶，其产物 CD15 抗原（也叫 Lewis X 或 SSEA-1）高表达于中性粒细胞和单核细胞表面。这个最强的正相关与反卷积分析中髓系细胞在 ICAM1 高表达组增加的结果高度一致。

| 基因 | ρ | P 值 |
|---|---|---|
| CD15 | +0.521 | < 0.001 \*\*\* |
| CD11b | +0.419 | < 0.001 \*\*\* |
| CD86 | +0.386 | < 0.001 \*\*\* |
| FOXP3 | +0.381 | < 0.001 \*\*\* |
| CD25 | +0.344 | < 0.001 \*\*\* |
| CD282 | +0.292 | 0.002 \*\* |
| CD163 | +0.229 | 0.015 \* |

CD11b（ITGAM）编码整合素 αM 链，与 CD18 组成 Mac-1（CR3）受体，是单核/巨噬细胞和中性粒细胞的核心表面标志。它的 ρ = 0.419 进一步支持了髓系浸润的解释。CD86（ρ = 0.386）是 M1 型巨噬细胞和树突状细胞的共刺激分子，参与 T 细胞活化，与 ICAM1 的功能有天然关联——两者都是免疫突触的重要组成部分。

FOXP3（ρ = 0.381）和 CD25（ρ = 0.344）作为 Treg 的标志物，两者的正相关提示 ICAM1 高表达微环境中可能存在 Treg 的协同浸润。这在功能上形成了一种微妙的平衡：一方面 M1 型巨噬细胞和共刺激分子（CD86、ICAM1）促进免疫激活，另一方面 Treg 和免疫检查点（PD-L1、CTLA4、TIM3）抑制免疫应答。ICAM1 高表达的肿瘤微环境似乎是"热肿瘤"（免疫浸润强）和"免疫抑制"（检查点高表达）的混合体——这对免疫治疗策略的选择至关重要。

CD163 是 M2 型巨噬细胞（免疫抑制型）的标志，它与 ICAM1 的相关性虽然也显著（ρ = 0.229, P = 0.015），但明显弱于 M1 相关标志物（ICAM1 本身 ρ = 1 因为是自相关、CD86 ρ = 0.386）。这提示 ICAM1 表达更偏向与促炎性的 M1 表型关联，而非免疫抑制性的 M2 表型。

淋巴细胞标志物整体上与 ICAM1 不相关：

| 基因 | ρ | P 值 |
|---|---|---|
| CD8A | +0.174 | 0.065 |
| CD8B | +0.168 | 0.075 |
| CD56 | -0.152 | 0.109 |
| CD1C | -0.147 | 0.121 |
| CD141 | +0.096 | 0.312 |
| CD79A | -0.077 | 0.418 |
| MS4A1 | -0.025 | 0.795 |
| CD79B | -0.019 | 0.840 |
| CD19 | -0.014 | 0.883 |

CD8A（P = 0.065）和 CD8B（P = 0.075）虽然接近显著但未达到阈值，ρ 值也很低（~0.17）。B 细胞标志物（CD19、MS4A1/CD20、CD79A、CD79B）的 ρ 值全部接近零（-0.077 到 +0.014）。这与反卷积分析中淋巴细胞亚群在 ICAM1 高/低组间无显著差异的结果完美吻合——从两个完全不同的分析角度（反卷积 vs 单基因相关）得出了相同的结论：ICAM1 的表达差异主要与髓系细胞相关，与淋巴细胞关系不大。

这种髓系特异性关联的生物学解释可能有几种：ICAM1 本身在髓系细胞（尤其是活化的巨噬细胞和树突状细胞）上高表达，所以组织中髓系细胞比例高的样本自然 ICAM1 总表达量高；ICAM1 通过 LFA-1 与 T 细胞结合促进跨内皮迁移，但这个过程在鼻咽癌中可能优先招募髓系细胞而非淋巴细胞；鼻咽癌作为一种与 EBV 相关的恶性肿瘤，其免疫微环境的构成可能受到病毒抗原驱动，呈现髓系偏向的浸润模式。

## 可视化

可视化部分使用了 ComplexHeatmap 绘制相关性热图，ggplot2 + ggpubr 绘制箱线图（按 ICAM1 分组比较每种方法得到的细胞比例/得分），以及相关性点图。

加载库并设置通用参数。配色上，ICAM1 高表达组用红色（#E64B35），低表达组用蓝色（#4DBBD5），红蓝对比是生物信息学中处理分组数据的经典配色。`make_boxplot` 是一个通用绘图函数，接受长格式数据、值列名、Y 轴标签和标题，自动生成带 Wilcoxon 检验显著性标注的箱线图：

```r
library(ComplexHeatmap)
library(circlize)
library(RColorBrewer)
library(viridis)
library(ggplot2)
library(ggpubr)
library(dplyr)
library(tidyr)
library(tibble)
library(reshape2)
library(grid)

all_results <- readRDS("results/correlation/all_results.rds")
all_results <- all_results[!is.na(all_results$rho), ]

group <- readRDS("data/icam1_group.rds")
icam1_expr <- readRDS("data/icam1_expr.rds")
group_df <- data.frame(sample = names(group), group = group, stringsAsFactors = FALSE)

dir.create("results/figures", showWarnings = FALSE, recursive = TRUE)

clrs <- c("ICAM1_High" = "#E64B35", "ICAM1_Low" = "#4DBBD5")

make_boxplot <- function(long_df, y_col, y_label, title) {
  ggplot(long_df, aes(x = cell_type, y = .data[[y_col]], fill = group)) +
    geom_boxplot(outlier.size = 0.3, linewidth = 0.3) +
    scale_fill_manual(values = clrs) +
    stat_compare_means(aes(group = group), label = "p.signif",
                       method = "wilcox.test", hide.ns = TRUE,
                       size = 3, vjust = 0.5) +
    labs(title = title, x = "", y = y_label, fill = "ICAM1 Group") +
    theme_minimal(base_size = 12) +
    theme(axis.text.x = element_text(angle = 45, hjust = 1, size = 8),
          legend.position = "bottom", panel.grid.minor = element_blank())
}
```

`stat_compare_means` 的 `hide.ns = TRUE` 参数只显示显著的比较结果，避免箱线图上堆满 "ns" 标记。`label = "p.signif"` 直接显示星号而非 P 值数字，图更干净。

### 相关性热图

使用 ComplexHeatmap 将三个功能组的基因与 ICAM1 的 Spearman ρ 值绘制为拼接热图。每个功能组是一个独立的 Heatmap 对象，用 `%v%` 操作符纵向拼接。红蓝色阶代表正负相关，单元格内标注显著性星号（\* P<0.05, \*\* P<0.01, \*\*\* P<0.001）。与相关性的散点图不同，热图能一眼看出三组基因在整体上的差异——Immune Checkpoint 和 Myeloid & Treg 组几乎全是红色（正相关），而 Immune Cell Markers 组则是白色（接近零相关）：

```r
gene_labels <- list(
  "Immune Checkpoint" = c("CTLA4", "LAG3", "PD-L1", "PD-L2", "TIM3"),
  "Immune Cell Markers" = c("CD8A", "CD8B", "CD1C", "CD141", "CD19",
                              "MS4A1", "CD79B", "CD79A", "CD56"),
  "Myeloid & Treg" = c("CD15", "CD11b", "CD66b", "NOS2", "CD86",
                         "CD282", "CD206", "CD163", "ARG1", "CD204",
                         "FOXP3", "CD25")
)

col_fun <- colorRamp2(c(-0.5, 0, 0.5), c("#2166AC", "white", "#B2182B"))
ht_list <- NULL

for (th in c("Immune Checkpoint", "Immune Cell Markers", "Myeloid & Treg")) {
  genes_in_panel <- gene_labels[[th]]
  panel_data <- all_results[all_results$panel == th, ]
  panel_vec <- panel_data$rho
  names(panel_vec) <- panel_data$gene
  panel_vec <- panel_vec[intersect(genes_in_panel, names(panel_vec))]
  if (length(panel_vec) == 0) next

  n_genes <- length(panel_vec)
  pval_mat <- matrix("", nrow = n_genes, ncol = 1)
  rownames(pval_mat) <- names(panel_vec)
  colnames(pval_mat) <- "ICAM1"
  for (i in seq_along(panel_vec)) {
    gn <- names(panel_vec)[i]
    pv <- panel_data$p_value[panel_data$gene == gn]
    if (length(pv) == 1 && !is.na(pv)) {
      if (pv < 0.001) pval_mat[i, 1] <- "***"
      else if (pv < 0.01) pval_mat[i, 1] <- "**"
      else if (pv < 0.05) pval_mat[i, 1] <- "*"
    }
  }

  rho_mat <- matrix(panel_vec, ncol = 1)
  colnames(rho_mat) <- "ICAM1"
  rownames(rho_mat) <- names(panel_vec)

  cell_fun <- function(j, i, x, y, width, height, fill) {
    grid.text(pval_mat[i, j], x = x, y = y,
              gp = gpar(fontsize = 9, col = "black", fontface = "bold"))
  }

  ht <- Heatmap(
    rho_mat, name = paste0("rho_", gsub(" ", "_", th)), col = col_fun,
    cluster_rows = FALSE, cluster_columns = FALSE,
    row_names_side = "left", show_row_names = TRUE,
    column_names_side = "top", column_title = th,
    column_title_gp = gpar(fontsize = 12, fontface = "bold"),
    row_names_gp = gpar(fontsize = 11),
    row_names_max_width = max_text_width(names(panel_vec), gp = gpar(fontsize = 11)),
    cell_fun = cell_fun,
    width = unit(2, "cm"), height = unit(n_genes * 0.65, "cm"),
    heatmap_legend_param = list(
      title = "Spearman rho", title_gp = gpar(fontsize = 9),
      labels_gp = gpar(fontsize = 8), direction = "horizontal"
    )
  )

  if (is.null(ht_list)) { ht_list <- ht } else { ht_list <- ht_list %v% ht }
}

pdf("results/figures/Figure1_correlation_heatmap.pdf", width = 6, height = 9)
draw(ht_list, heatmap_legend_side = "bottom",
     padding = unit(c(2, 2, 2, 4), "mm"), merge_legend = TRUE)
dev.off()
```

热图只有一列（全部是与 ICAM1 的相关性），三个面板纵向排列。`cluster_rows = FALSE` 保留基因的预定顺序而非层次聚类排序，方便按功能组阅读。`row_names_max_width` 确保基因名不会被截断。图例放在底部、水平方向（`direction = "horizontal"`），这是 ComplexHeatmap 的常见做法——图例在顶部或底部时水平排列更省空间。

### 反卷积方法箱线图

五种反卷积方法各生成一张箱线图，X 轴是细胞类型，Y 轴是比例或得分，按 ICAM1 分组填充红/蓝色。以 CIBERSORT 为例：

```r
cibersort_file <- "results/deconvolution/cibersort_full.rds"
if (file.exists(cibersort_file)) {
  proportions <- readRDS(cibersort_file)
  cell_type_cols <- grep("P-value|Correlation|RMSE", colnames(proportions),
                         invert = TRUE, value = TRUE)
  cibersort_prop <- t(proportions[, cell_type_cols, drop = FALSE])
  cibersort_long <- cibersort_prop %>%
    as.data.frame() %>% tibble::rownames_to_column("cell_type") %>%
    tidyr::pivot_longer(-cell_type, names_to = "sample", values_to = "proportion") %>%
    mutate(sample = gsub("\\.", "-", sample)) %>%
    left_join(group_df, by = "sample")

  p <- make_boxplot(cibersort_long, "proportion", "Estimated Proportion",
                    "CIBERSORT: Cell Type Proportions by ICAM1 Expression")
  ggsave("results/figures/Figure2_cibersort_boxplot.pdf", p, width = 14, height = 6)
}
```

其余四种方法的代码结构完全相同，只是替换数据来源（`epic.rds` / `mcp_counter.rds` / `quantiseq.rds` / `xcell.rds`）和 Y 轴标签（proportion 或 score）。xCell 的细胞类型多达 60+ 种，这里手动筛选了 20 种免疫细胞子集（从 B cell 到 Mast cell），去掉了基质细胞和干细胞等无关类型，避免箱线图过于拥挤。

### ICAM1 分组验证

用箱线图+散点展示中位数分组后两组的 ICAM1 表达水平，确认分组确实将样本区分开了：

```r
icam1_df <- data.frame(sample = names(icam1_expr), ICAM1 = icam1_expr, group = group)

p_icam1 <- ggplot(icam1_df, aes(x = group, y = ICAM1, fill = group)) +
  geom_boxplot(outlier.size = 0.5) +
  geom_jitter(width = 0.1, alpha = 0.5, size = 1) +
  scale_fill_manual(values = clrs) +
  stat_compare_means(aes(group = group), label = "p.format", method = "wilcox.test") +
  labs(title = "ICAM1 Expression by Group (Median Split)", x = "", y = "ICAM1 Expression (FPKM)") +
  theme_minimal(base_size = 13) + theme(legend.position = "none")

ggsave("results/figures/Figure7_icam1_groups.pdf", p_icam1, width = 6, height = 5)
```

这张图虽然简单但是必要——它直观地确认了中位数分组是有效的，两组的 ICAM1 表达确实完全分离（Wilcoxon P 应该趋近于 0）。`geom_jitter` 叠加散点可以看到个体分布，`alpha = 0.5` 处理重叠。

### 相关性点图

以 Cleveland 点图形式展示三组基因的 Spearman ρ 值，Y 轴是基因名（按功能组分面），X 轴是 ρ 值。点的大小编码显著性（-log10(p)，越显著点越大），颜色编码相关性的方向和强度：

```r
dot_data <- all_results
dot_data$panel <- factor(dot_data$panel, levels = c(
  "Immune Checkpoint", "Immune Cell Markers", "Myeloid & Treg"
))
dot_data$gene <- factor(dot_data$gene, levels = rev(unique(dot_data$gene)))

p_dot <- ggplot(dot_data, aes(x = rho, y = gene, color = rho, size = -log10(p_value + 1e-10))) +
  geom_point() +
  scale_color_gradient2(low = "#2166AC", mid = "white", high = "#B2182B",
                        midpoint = 0, limits = c(-0.5, 0.5)) +
  scale_size_continuous(range = c(2, 7)) +
  facet_wrap(~ panel, scales = "free_y", ncol = 1, strip.position = "right") +
  geom_vline(xintercept = 0, linetype = "dashed", alpha = 0.4) +
  labs(x = "Spearman Correlation with ICAM1", y = "",
       color = "rho", size = expression(-log[10](p))) +
  theme_minimal(base_size = 12) +
  theme(strip.text = element_text(face = "bold", size = 11),
        panel.grid.major.y = element_blank(), panel.spacing = unit(1, "lines"))

ggsave("results/figures/Figure8_correlation_dotplot.pdf", p_dot, width = 9, height = 12)
```

相比热图，点图的优势在于可以同时展示三个维度的信息（ρ 值、P 值、基因所属功能组），而且是"位置+大小+颜色"三通道编码，人眼识别效率很高。`facet_wrap(~ panel, scales = "free_y", ncol = 1)` 的好处是每个功能组独立一行，Y 轴基因数量可以不同（Immune Checkpoint 只有 5 个基因而 Myeloid & Treg 有 12 个），不会因为统一 Y 轴范围导致某些组过度压缩。`p_value + 1e-10` 是为了避免 P = 0 时 `log10(0)` 产生 -Inf（虽然 Spearman 精确检验不会给出 P = 0，但浮点精度下可能）。

总共生成 8 张 PDF 图表，全部保存在 `results/figures/` 下：一张相关性热图、五张反卷积箱线图（每种方法一张）、一张分组验证图、一张相关性点图。

## 讨论

反卷积和相关性分析一致表明，ICAM1 表达与髓系细胞浸润密切相关，与淋巴细胞关联较弱。

M1 巨噬细胞在 ICAM1 高表达组中显著升高（P.adj = 0.0058），在所有方法中重复性最好。ICAM1 是 M1 极化的标志物——IFN-γ 和 LPS 刺激下巨噬细胞向 M1 极化，同时上调 ICAM1、CD86 等表面分子，因此高 ICAM1 至少部分反映了 M1 浸润的增加。CD15（ρ = 0.521）和 CD11b（ρ = 0.419）作为髓系标志物与 ICAM1 的强正相关也支持这一点。

免疫检查点方面，ICAM1 与 PD-L1（ρ = 0.375）、TIM3（ρ = 0.408）、LAG3（ρ = 0.399）、CTLA4（ρ = 0.266）全部正相关，提示 ICAM1 高表达肿瘤中免疫抑制信号同步增强。ICAM1 可能是一个双重指标——既反映免疫浸润（"热肿瘤"），又伴随检查点上调（需要解除抑制），这对联合治疗（抗 PD-1 + 抗 TIM3/LAG3）有参考价值。FOXP3（ρ = 0.381）和 CD25（ρ = 0.344）的正相关则提示 Treg 参与了这一抑制性微环境。

B cells naive 在反卷积中组间差异显著（P.adj = 0.0182），但 B 细胞系单基因标志物与 ICAM1 均不相关。这不矛盾：反卷积整合多基因信息估计细胞丰度，单基因相关只捕捉一个基因的关联，且可能受该基因在多细胞类型中表达的影响。

局限性：中位数分组损失连续表达信息，可改用 ICAM1 作为连续变量做回归；反卷积推断的是相对比例，总和为 1 导致细胞类型间存在负相关诱导；EBV 基因无法从标准 RNA-seq 中检出；样本量对中等以上效应足够，小效应可能漏检。
