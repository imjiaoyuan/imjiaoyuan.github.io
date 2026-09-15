---
title: DAP-seq 结合 scRNA-seq 构建调控网络
date: 2026-09-17
---

这套分析用 DAP-seq 实测的转录因子结合位点当物理证据，用单细胞共表达当表达证据，两层取交集建调控网络，也就是 mGRN+。表达层用的是上游整合流程产出的 harmony 注释对象，脚本按运行顺序列在下面，最后一节写这套做法与已有的大规模 DAP-seq 建网络研究的差异。

基因调控网络最怕两件事。只靠表达相关性连边，会把连带变化当成直接调控。只靠结合位点连边，会把能结合当成在调控。所以这里的做法是两层取交集，物理层用 DAP-seq 实测的转录因子结合峰落在靶基因启动子上，表达层要求这对转录因子与靶基因在单细胞数据里确实共表达，两者都满足的边才进最终网络，这样连出来的是 mGRN+，有多层证据支撑的调控网络。这套做法参照大规模 DAP-seq 建调控网络的思路，差异在最后一节列出。

DAP-seq 把转录因子在体外表达出来，让它去结合打碎的基因组 DNA，再测序看它结合到了哪里，得到的是这个转录因子在全基因组的结合位点。它不需要抗体，代价是拿到的是体外结合，体内染色质环境的信息没有。测出来的信号堆叠起来就是峰（peak），MACS2 输出的 narrowPeak 格式里第 1 到第 3 列是峰的位置，第 7 列是峰强度。

数据限制决定了网络的层数，没有 ATAC 或 ACR 数据，所以没有可及性那一层；没有原始比对结果，只有 narrowPeak，所以峰质控只能简化；没有 bulk RNA-seq，所以表达层用单细胞数据顶替。

## 统一基因 ID

网络里所有东西都要落到同一套 ID，DAP 实验号对应的转录因子、转录起始位点、表达矩阵的基因名。任何一处不统一，都会在取交集时静默丢掉基因，不报错。GTF 与同源表的 ID 写法常常只差一个符号，比如下划线与短横线之差，所以要先建映射表。

```bash
tail -n +2 gene_list/homology.csv > results/dap/homology.noheader.csv
```

- `-n +2`，从第二行开始输出，跳过表头。后面的 awk 就不用再处理表头行。

跳过表头之后，只留同源表里能用的那套 ID：

```bash
awk -F',' '$2~/^Palv2-/ {print $2}' results/dap/homology.noheader.csv > results/dap/valid_id.raw.txt
```

- `-F','`，同源表是逗号分隔。
- `$2~/^Palv2-/`，只取第二列里以 `Palv2-` 开头的 ID，这是同源表里可用的那套写法。

同一套 ID 里有重复，去重后才好数数：

```bash
sort -u results/dap/valid_id.raw.txt -o results/dap/valid_id.txt
```

- `sort -u`，去重。单独写一步的好处是能直接数两份 ID 各自剩下多少条。

另一头从 GTF 里取基因 ID，取注释里写的那套：

```bash
grep -oP 'gene_id "Palv2_\K[^"]+' ref/annotation.gtf > results/dap/gtf_id.raw.txt
```

- `-o`，只输出匹配到的部分，不要把整行打出来。GTF 一行有九列，直接输出整行后面没法用。
- `-P`，启用 PCRE 语法，`\K` 才可用，它表示丢弃前面已经匹配的部分，只保留后面的基因名。用普通 grep 要接两次 sed 才能做到同一件事。
- GTF 里写的是 `Palv2_` 加数字，同源表里是 `Palv2-` 加数字，只差一个符号，这正是要建映射表的原因。

GTF 里一个基因占多行，去重后才是基因总数：

```bash
sort -u results/dap/gtf_id.raw.txt -o results/dap/gtf_id.txt
```

- GTF 里同一个基因会出现很多行，去重后得到基因总数。

两份 ID 只差一个符号，按这个规则把两边对起来：

```bash
awk -v OFS=',' 'FILENAME==ARGV[1]{valid[$1]=1; next} {map_id="Palv2-"$0; if(valid[map_id]==1) print "Palv2_"$0, map_id}' results/dap/valid_id.txt results/dap/gtf_id.txt > results/dap/gene_id_map.csv
```

- `-v OFS=','`，输出用逗号分隔。
- `FILENAME==ARGV[1]`，awk 读第一个文件时建索引，读第二个文件时按索引筛选并输出映射关系。
- `map_id="Palv2-"$0`，把 GTF 的 ID 拼成同源表的写法再做匹配。
- 输出是两列映射表，左边是 GTF 的 ID，右边是同源表的 ID。后面所有步骤都以这份表为准。

数一下映射表有多少行，与两边的 ID 数对得上才算建成：

```bash
wc -l results/dap/gene_id_map.csv
```

- 建完先数一下行数。映射表明显少于 GTF 的基因数，说明有一部分基因在两套命名里对不上号，这部分基因后面的网络里直接没有节点，不报错，但会少东西。

## 转录起始位点提取

启动子的位置由转录起始位点决定，而基因组注释里没有现成的转录起始位点字段，要从外显子推，正链基因取所有外显子起点的最小值，负链基因取外显子终点的最大值。不能直接用 GTF 里 gene 行的首尾，那包含了 UTR 之外的区域，而且对负链基因会反向。

```bash
awk 'BEGIN{OFS="\t"}
$3=="exon"{
  line=$0; gsub(/.*gene_id "/,"",line); gsub(/".*/,"",line); gid=line
  if (gid==""||gid~/^gene_id/) next
  key=gid"|"$1"|"$7
  if(!(key in seen)){seen[key]=1; if($7=="+")tss[key]=$4; else tss[key]=$5}
  else{if($7=="+"){if($4<tss[key])tss[key]=$4}else{if($5>tss[key])tss[key]=$5}}
}
END{for(k in seen){split(k,p,"|"); print p[2],tss[k]-1,tss[k],p[1],".",p[3]}}' ref/annotation.gtf | sort -k1,1 -k2,2n > results/dap/tss.bed
```

- `$3=="exon"`，只在 exon 行上计算。用 CDS 行会把非编码基因丢掉。
- `gsub(/.*gene_id "/,"",line)`，从属性列里取出基因 ID。属性列格式在不同来源的 GTF 里差异很大，按固定列号取会错。
- `gsub(/".*/,"",line)`，去掉 ID 后面剩下的引号和其它属性字段。
- `if (gid==""||gid~/^gene_id/) next`，拿不到 ID 的行直接跳过，避免把属性列的残渣当成基因名。
- `key=gid"|"$1"|"$7`，用基因 ID 加染色体加链作为键，避免同名基因互相覆盖。
- `tss[key]=$4` 与 `tss[key]=$5`，第一次遇到这个基因时，正链取外显子起点，负链取外显子终点。
- `if($5>tss[key])tss[key]=$5`，负链要取最大值，与正链逻辑相反。写反了负链基因的启动子会落到基因下游。
- `END{for(k in seen)...}`，awk 数组无序，输出顺序不保证，所以管道里接一次 sort。
- `tss[k]-1` 与 `tss[k]` 是 BED 的起点终点，tss 位点本身写成一个碱基宽的区间；输出六列依次是染色体、起点、终点、基因 ID、分数、链，分数列用点占位。

TSS 位点上的基因 ID 也换成同源表的写法，后面按 ID 连接才对得上：

```bash
awk -v OFS="\t" '{old=$4; new=old; gsub(/^Palv2_/,"Palv2-",new); gsub(/^Palv1_/,"Palv1-",new); $4=new; print}' results/dap/tss.bed | sort -k1,1 -k2,2n > results/dap/tss_palv2.bed
```

- `gsub(/^Palv2_/,"Palv2-",new)`，只替换基因 ID 列的前缀，不碰坐标。
- 输出文件名带 `palv2` 表示 ID 已经转成网络里用的那套写法，后面所有区间操作都用这一份。
- 这一步不做映射表的白名单过滤，GTF 里的基因全部保留，免得在 TSS 阶段就丢基因，后面统计时看不出丢了什么。

## 物理层：峰落到启动子上

把每个转录因子的 DAP-seq 峰与所有基因上游 3 kb 的启动子区间求交集，命中即一条实测结合边。启动子窗口取 TSS 上游 3000 bp 到 0，也就是链特异的 `[-3000, 0]`，

```bash
awk -v w=3000 -v FAI=ref/genome.fa.fai 'BEGIN{OFS="\t"}
FILENAME==FAI{len[$1]=$2; next}
{chr=$1;s=$2;e=$3;gid=$4;str=$6; L=len[chr]
  if(str=="+"){ns=s-w;if(ns<0)ns=0;ne=s}
  else if(str=="-"){ns=e;ne=e+w}
  else next
  if(ne > L) ne = L
  if(ns > L) ns = L
  if(ns < 0) ns = 0
  if(ne > ns) print chr,ns,ne,gid,0,str}' ref/genome.fa.fai results/dap/tss_palv2.bed | sort -k1,1 -k2,2n > results/dap/promoter_up3kb.bed
```

- `FILENAME==FAI{len[$1]=$2; next}`，第一个文件是 .fai，先读它得到每条染色体长度，用于把区间截到染色体范围内。
- `str=="+"`，正链基因启动子在上游，取 TSS 往前 3 kb，写成 `ns=s-3000`。
- `str=="-"`，负链基因的上游在坐标大的方向，取 TSS 往后 3 kb，写成 `ne=e+3000`。这两条写成一样，负链的启动子就跑到基因里去了。
- `if(ns<0)ns=0`，起点不能是负数。基因就在染色体开头时把起点截到 0。
- `if(ne>L)ne=L`，终点不能超出染色体末端，否则后面 bedtools 会报错。
- `if(ne>ns) print`，只有区间合法才输出，避免产生零长度区间。
- 窗口长度写成变量 `w`，这里是 3 kb。窗口越大召回越高，同时会把更多远端增强子带来的假边算进来，常见做法是 3 kb 或 5 kb，取哪个都要在方法里写明。
- 第 5 列那个 0 是 BED 的分数列，这里用不到。

建网络之前先把表头写进总表，后面每个转录因子的边都往里追加：

```bash
echo "tf_experiment,target_geneid,peak_chr,peak_start,peak_end,peak_name,peak_score" > results/dap/physical_network.csv
```

- 先写表头，后面每个转录因子的边往这个文件里追加。表头七个字段，第四列之后是峰本身的信息，方便回查是哪条峰支持了这条边。

每个转录因子的峰分开取交，中间文件各自保存，

```bash
bedtools intersect -a dap/TF01_peaks.narrowPeak -b results/dap/promoter_up3kb.bed -wa -wb > results/dap/TF01.peak_in_promoter.tsv
```

- `-a`，转录因子的峰文件，MACS2 输出的 narrowPeak。
- `-b`，上一步的启动子区间。
- `-wa -wb`，同时输出峰和启动子两侧的区间。启动子的基因 ID 在 B 侧，也就是第 14 列。

把落在启动子里的峰转成边，实验号带在输出里，后面再换成基因 ID：

```bash
awk 'BEGIN{OFS=","}{print "TF01",$14,$1,$2,$3,$4,$5}' results/dap/TF01.peak_in_promoter.tsv > results/dap/TF01.edges.unsorted.csv
```

- `print "TF01",$14,...`，把实验号带进输出，用来标识这是哪个转录因子的峰。实验号要与映射文件里的写法一致，否则后面换成基因 ID 时会变成空值。
- `OFS=","`，输出用逗号分隔，与后面两步的 awk 保持一致。

同一对转录因子与靶基因可能有多个峰，先按峰强度排好：

```bash
sort -t',' -k1,1 -k2,2 -k7,7rn results/dap/TF01.edges.unsorted.csv -o results/dap/TF01.edges.sorted.csv
```

- `-t','`，按逗号分列。
- `-k7,7rn`，按第 7 列的峰强度降序排，同一对转录因子与靶基因的多个峰按强弱排好，下一步才能只留最强的那条。

只留最强的那条边，追加到总表：

```bash
awk -F',' '!seen[$1"|"$2]++' results/dap/TF01.edges.sorted.csv >> results/dap/physical_network.csv
```

- `!seen[$1"|"$2]++`，每个转录因子与靶基因的组合只保留第一条，也就是最强的那个峰。不去重的话，同一对被多个峰命中的边会重复计数，影响后面按度数做的统计。
- `>>`，追加到总表。每个转录因子跑一遍，所有边累在同一个文件里。

转录因子多的时候上面四步写成循环，把文件名和实验号当变量传进去，

```bash
for peak_file in dap/*.narrowPeak; do tf=$(basename "$peak_file" .narrowPeak | sed 's/_peaks//'); bedtools intersect -a "$peak_file" -b results/dap/promoter_up3kb.bed -wa -wb 2>/dev/null | awk -v tf="$tf" 'BEGIN{OFS=","}{print tf,$14,$1,$2,$3,$4,$5}' | sort -t',' -k1,1 -k2,2 -k7,7rn | awk -F',' '!seen[$1"|"$2]++' >> results/dap/physical_network.csv; done
```

- `basename "$peak_file" .narrowPeak`，从文件名取实验号，去掉扩展名。
- `sed 's/_peaks//'`，再消掉 MACS2 常见的 `_peaks` 后缀，实验号要与映射表里的写法对上。
- `-v tf="$tf"`，把实验号作为变量传进 awk，避免在 awk 里再解析文件名。
- 三个命令串成管道，中间不落盘，一个转录因子的边很少，单独存文件反而占地方。
- 每个转录因子单独跑一遍再汇总，最后一步才写总表，这样中途出错只需要重跑一个转录因子。

每个转录因子跑完合成一张总表，数一下边有多少条：

```bash
wc -l results/dap/physical_network.csv
```

- 数边数和行的数量级，与峰文件数量对照一下。边上万到十几万条都正常，边数只有几十条说明实验号或列号取错了。

## 表达层：伪 bulk 与单细胞矩阵

表达层要回答两件事，这两个基因是不是同步变化，以及这种同步是不是细胞类型特异的。同步性用皮尔逊相关系数衡量，它需要一份每行是一个样本、每列是一个基因的矩阵，所以先把同一细胞类型同一组织的细胞表达量加起来，做成伪 bulk；同时把单细胞稀疏矩阵原样导出，供 GRNBoost2 使用。

```r
library(Seurat); library(Matrix)
scRNA <- readRDS("results/harmony_annotated.rds")
scRNA <- subset(scRNA, !is.na(cell_type))
scRNA$group <- paste(scRNA$sample, scRNA$cell_type, sep = "|")
```

- `readRDS`，读的是上游整合流程产出的带注释对象，细胞类型已经在这一层定好，不要在这里重新聚类。
- `!is.na(cell_type)`，没有注释的细胞直接丢掉，它们的归属未知。
- `paste(..., sep = "|")`，按样本和细胞类型两个维度分组。只按细胞类型聚合会把组织间的差异抹掉，后面算相关时样本量也会太少。

做伪 bulk 之前先看每个分组有多少细胞，太少的组后面要丢掉：

```r
gp <- table(scRNA$group)
sm <- names(gp[gp < 10])
scRNA <- subset(scRNA, cells = colnames(scRNA)[!scRNA$group %in% sm])
```

- `gp < 10`，细胞数少于 10 的组丢掉。细胞太少的组，伪 bulk 值由少数几个细胞决定，相关分析会不稳定。
- 先算出要丢的组名再取子集，比在 subset 里写表达式好排查，能直接打印丢了哪几组。

把同一细胞类型同一组织的细胞表达量加起来，得到伪 bulk 矩阵：

```r
pb <- as.matrix(AggregateExpression(scRNA, assays = "RNA", slot = "counts",
              group.by = "group", return.seurat = FALSE)$RNA)
colnames(pb) <- gsub("^g", "", colnames(pb))
pb <- pb[rowSums(pb) >= 10, , drop = FALSE]
cpm <- sweep(pb, 2, colSums(pb) / 1e6, "/")
write.csv(cpm, "results/dap/pseudobulk_matrix.csv")
```

- `slot = "counts"`，用原始计数相加，不要用标准化后的值。标准化是针对单细胞做的，相加之后没有意义。
- `colnames(pb) <- gsub("^g", "", ...)`，Seurat 聚合后会在组名前加 `g`，去掉之后列名才是 `sample|cell_type`。
- `rowSums(pb) >= 10`，总计数太低的基因丢掉，这类基因在伪 bulk 里的表达值基本是噪音。
- `sweep(pb, 2, colSums(pb) / 1e6, "/")`，转成 CPM，让不同组之间的表达量可比，皮尔逊相关必须在可比的尺度上算。
- 输出矩阵是基因乘分组，行名是基因 ID，列名是 `样本|细胞类型`。

同一个对象再导一份单细胞稀疏矩阵，GRNBoost2 那一侧要用：

```r
cnt <- GetAssayData(scRNA, assay = "RNA", slot = "counts")
Matrix::writeMM(cnt, "results/dap/singlecell_matrix.mtx")
write.table(rownames(cnt), "results/dap/singlecell_genes.tsv", row.names = FALSE, col.names = FALSE, quote = FALSE)
write.table(colnames(cnt), "results/dap/singlecell_cells.tsv", row.names = FALSE, col.names = FALSE, quote = FALSE)
```

- `writeMM`，写成 MatrixMarket 格式，Python 侧用 `scipy.io.mmread` 直接读成稀疏矩阵，不用转 CSV。
- 矩阵是基因乘细胞，与两个 ID 文件的行列顺序一一对应，顺序错了两边就对不上，必须一起导出。
- `quote = FALSE`，ID 里带引号会让 Python 读进来多一个字符。

## 表达层：共表达网络

表达层内部也做一次取交。GRNBoost2 是一种基于梯度提升的调控网络推断方法，把每个转录因子当目标变量、其它基因当特征，用特征重要性衡量调控强度，它直接跑在高维稀疏的单细胞矩阵上，因为要用到细胞之间的异质性，聚合之后这份信息就没了。皮尔逊相关跑在伪 bulk 上，衡量的是基因沿样本维度的同步变化。两者都支持的边保留。

阈值按这套数据的规模直接定下来：importance 取 0.0001，每个转录因子各留 2000 条边，高变基因取 3000 个，细胞最多抽 30000 个，随机种子 42。数字直接写在下面用到的地方，换数据时改数字即可。

- importance 阈值 0.0001。调低会保留更多边，调高只留最强的边。
- 每个转录因子按重要性留前 2000 条边，按相关系数也留前 2000 条。
- 高变基因取 3000 个。用全部基因时 GRNBoost2 需要稠密特征，基因太多会爆内存。
- 单细胞最多抽 30000 个细胞。二十万细胞的矩阵在常见机器上跑不动，抽样是必要的，抽样之后要记录实际用了多少细胞。
- 随机种子固定 42。抽样和 GRNBoost2 都带随机性，固定种子是结果可复现的前提。
- 线程数 16，并行由 armoreto 底下的 dask 负责。

读矩阵并按方差选基因，

```python
import numpy as np
import pandas as pd
from scipy.io import mmread

tf_tab = pd.read_csv("gene_list/dap_tf_mapping.csv")
tf_in = sorted(set(tf_tab["tf_geneid"].dropna().astype(str).str.strip()) - {""})
genes = [l.strip() for l in open("results/dap/singlecell_genes.tsv")]
cells = [l.strip() for l in open("results/dap/singlecell_cells.tsv")]
X = mmread("results/dap/singlecell_matrix.mtx").tocsc()
mn = np.asarray(X.mean(axis=1)).ravel()
m2 = np.asarray(X.multiply(X).mean(axis=1)).ravel()
var = m2 - mn ** 2
order = np.argsort(-var)
top = list([genes[i] for i in order[:3000]])
sel = list(dict.fromkeys(top + [t for t in tf_in if t not in top]))
Xsel = X[[genes.index(g) for g in sel], :].T.tocsc()
```

- `mmread(...).tocsc()`，转成列压缩格式，后面按基因取行、按细胞取列都靠它。
- `var = m2 - mn ** 2`，直接在稀疏矩阵上算方差，不整体转稠密，内存才够用。
- `sel = list(dict.fromkeys(top + tf_in))`，高变基因加上全部转录因子，并去重保序。转录因子即使表达方差不大也要留，否则网络里没有起点。
- `Xsel` 转置成细胞乘基因，GRNBoost2 的输入方向就是样本乘特征。
- `tf_in`，转录因子清单，直接从 DAP 实验与基因 ID 的对应表里取，不去重会重复计数，不去空字符串会多出一个不存在的基因。
抽样与 GRNBoost2，

```python
from dask.distributed import Client, LocalCluster
from arboreto.algo import grnboost2

if Xsel.shape[0] > 30000:
    rng = np.random.default_rng(42)
    pick = np.sort(rng.choice(Xsel.shape[0], size=30000, replace=False))
    Xsel = Xsel[pick, :]
Xsel = np.asarray(Xsel.toarray(), dtype=np.float32)
cluster = LocalCluster(n_workers=1, threads_per_worker=16, processes=False, dashboard_address=None)
client = Client(cluster)
g = grnboost2(expression_data=Xsel, gene_names=sel, tf_names=tf_in, client_or_address=client, seed=42, verbose=False)
```

- `rng.choice(...)`，随机抽细胞，抽样之后每个细胞仍是整条表达谱，不能按基因抽。
- `pick = np.sort(pick)`，先排序会让内存访问连续，稀疏矩阵取子集快很多，结果与顺序无关。
- `toarray()`，GRNBoost2 底层的 arboreto 会对稀疏切片调用 `.A`，新版 scipy 已经移除这个属性，所以这里显式转稠密。内存由基因数与抽样细胞数共同决定，两万基因乘三万细胞是这套默认值的上限。
- `n_workers=1, threads_per_worker=16`，单进程多线程的本地模式，避免再起多个进程抢内存。
- `tf_names=tf_in`，只算这些转录因子为因变量的模型，其它基因只作为特征出现。
- `seed=42`，固定随机种子。

按重要性和相关系数各取一次，然后取交，

```python
g = g[g["importance"] >= 0.0001]
g = g.sort_values(["TF", "importance"], ascending=[True, False]).groupby("TF").head(2000)
g.to_csv("results/dap/grnboost2_network.csv", index=False)
pb = pd.read_csv("results/dap/pseudobulk_matrix.csv", index_col=0).T
pcc_rows = []
for tf in tf_in:
    corr = pb.corrwith(pb[tf]).abs().drop(labels=[tf], errors="ignore").sort_values(ascending=False).head(2000)
    for gg, c in corr.items():
        pcc_rows.append((tf, gg, c))
pcc = pd.DataFrame(pcc_rows, columns=["TF", "target", "pcc"])
coexpr = g.merge(pcc[["TF", "target"]], on=["TF", "target"], how="inner")[["TF", "target", "importance"]]
coexpr.to_csv("results/dap/coexpression_network.csv", index=False)
```

- `groupby("TF").head(2000)`，每个转录因子内部取前 2000 条。全局取前 2000 会让少数强转录因子占据全部边，网络变成以个别节点为中心的星型结构。
- `pb.corrwith(pb[tf]).abs()`，先取绝对值再排序，因为负调控的边同样是调控关系。
- `.drop(labels=[tf])`，去掉转录因子与自己算出来的相关系数 1。
- `how="inner"`，两种方法都支持的边才保留，这是表达层内部的取交。
- GRNBoost2 那一层单独存一份 `grnboost2_network.csv`，后面统计时可以把 GRNa 与 GRNb 的边数并排列出来。

## 两层取交

物理层给的是边集，表达层给的也是边集，取交集即可。用集合判断而不是两层循环，边数上百万也吃得消，

```python
phys_dap = pd.read_csv("results/dap/dap_physical_network.csv")
coexpr   = pd.read_csv("results/dap/coexpression_network.csv")
tf_map   = pd.read_csv("gene_list/dap_tf_mapping.csv")
tf_map   = tf_map[tf_map["tf_geneid"].notna() & (tf_map["tf_geneid"] != "")]
tf_lookup = dict(zip(tf_map["tf_experiment_id"].astype(str).str.strip(),
                     tf_map["tf_geneid"].astype(str).str.strip()))
phys_dap["TF"] = phys_dap["tf_experiment"].astype(str).str.strip().map(tf_lookup)
phys_dap = phys_dap.dropna(subset=["TF"])
```

- `notna() & ( != "")`，映射表里可能有空行，先去掉，否则 dict 里会出现空键。
- `str.strip()`，实验号前后的空格会让匹配失败，两边都要去空格再建字典。
- `map(tf_lookup)`，把实验号换成基因 ID。map 之后要查一下有多少行变成空值，空值说明有实验号没有对应基因，属于映射表缺失。

单细胞侧的网络有了，把 DAP 的物理网络和共表达网络并起来，先按转录因子加靶基因拼键：

```python
dap_edges = {r["TF"] + "|" + r["target_geneid"]: {
        "peak_chr": r["peak_chr"], "peak_start": r["peak_start"],
        "peak_end": r["peak_end"], "peak_score": r["peak_score"]}
    for _, r in phys_dap.iterrows()}
phys_keys = set(dap_edges)
coexpr["key"] = coexpr["TF"].astype(str).str.strip() + "|" + coexpr["target"].astype(str).str.strip()
inter = phys_keys & set(coexpr["key"])
```

- `dap_edges`，键是 `TF|靶基因`，值是峰的位置和强度。这样取交之后还能把支持这条边的峰信息带出来。
- `phys_keys & set(coexpr["key"])`，集合求交，Python 的集合是哈希表，百万级键也是毫秒级。
- 键统一写成加号或竖线都行，两边一致就可以，混用会导致零交集且不报错。

两边用同一个键对齐，取交集：

```python
clu = coexpr.set_index("key")["importance"].to_dict()
name_lookup = dict(zip(tf_map["tf_geneid"].astype(str).str.strip(),
                       tf_map.get("tf_gene_name", tf_map["tf_geneid"]).astype(str).str.strip()))
rows = []
for k in sorted(inter):
    tf, target = k.split("|")
    d = dap_edges.get(k, {})
    rows.append({"TF": tf, "target": target, "importance": clu.get(k),
                 "peak_chr": d.get("peak_chr", ""), "peak_start": d.get("peak_start", ""),
                 "peak_end": d.get("peak_end", ""), "peak_score": d.get("peak_score", "")})
mgrn = pd.DataFrame(rows)
mgrn["TF_name"] = mgrn["TF"].map(name_lookup).fillna("")
mgrn.to_csv("results/dap/mgrn_plus.csv", index=False)
```

- `set_index("key")["importance"].to_dict()`，把表达层的重要性查成字典，比在循环里逐行筛选快。
- `sorted(inter)`，输出顺序固定，同一份输入重复跑出来的文件逐字节一致，方便比对。
- `TF_name`，转录因子的基因名，画图时比 ID 好读，映射不到就留空，不要在这里丢边。
- 输出的 `mgrn_plus.csv` 就是最终边表，每条边的两端都同时有实验结合证据和表达共变证据，另外带上支持它的峰。

这里没有加 motif 预测层。对已经有 DAP-seq 峰的转录因子来说，峰本身就给出了实测结合边，再用序列扫描预测一遍启动子只会引入假阳性。同理也没有 de novo motif 发现，那属于另一类分析。

## 组织子网络

全局网络会掩盖组织特异调控，同一个转录因子在不同组织里连的可能是不同的靶基因。按组织各取一次子网络，是后面所有组织间比较的基础。判定一个基因在某个组织里是否活跃，用的是该组织的伪 bulk 表达，CPM 大于 1 且在该组织至少三成的分组里成立。

```python
mgrn = pd.read_csv("results/dap/mgrn_plus.csv")
expr = pd.read_csv("results/dap/pseudobulk_matrix.csv", index_col=0)
groups   = expr.columns.tolist()
tissue_of = {g: g.split("|")[0] if "|" in g else g for g in groups}
tissues  = sorted(set(tissue_of.values()))
tissue_expr = pd.DataFrame({t: expr[[g for g in groups if tissue_of[g] == t]].mean(axis=1) for t in tissues})
tissue_expr.to_csv("results/dap/tissue_expression_mean.csv")
```

- `tissue_of`，从 `样本|细胞类型` 的列名里取组织。分组名格式不一致时这里会静默取到整串名字，要先把列名打出来看一眼。
- `tissue_expr`，基因乘组织的平均 CPM，后面算组织偏好性用它，同时存一份 `tissue_expression_mean.csv` 供 R 那几段读。
- 阈值都写死在代码里，同一份数据反复跑出来的子网络必须一样。

并完还要给每条边标组织偏好，先把几个统计量定下来：

```python
def _tau(x):
    x = np.asarray(x, float); m = x.max()
    if m == 0: return 0.0
    xh = x / m
    return float((1.0 - xh).sum() / (len(x) - 1))

gm   = tissue_expr.mean(axis=1)
pref = tissue_expr.ge(gm, axis=0)
tau_map = {g: _tau(tissue_expr.loc[g].values) for g in tissue_expr.index}
sub["target_tau"]        = sub["target"].map(tau_map)
sub["target_top_tissue"] = sub["target"].map(tissue_expr.idxmax(axis=1).to_dict())
sub["target_pref"]       = sub["target"].map(lambda g: bool(pref.loc[g, t]))
```

- `_tau`，组织特异性指数，把表达量除以最大值后算平均偏离程度。全部组织表达相近时接近 0，只在一个组织高表达时接近 1。
- `pref`，靶基因在该组织的表达是否不低于它自己的跨组织平均。用它标出组织偏好，比绝对值阈值稳。
- `target_top_tissue`，表达最高的组织，用来快速看一条边是不是跨组织错配。

逐个组织切片，只保留两端都在该组织活跃的边：

```python
for t in tissues:
    cols = [g for g in groups if tissue_of[g] == t]
    frac = (expr[cols] > 1.0).mean(axis=1)
    active = set(frac[frac >= 0.3].index)
    sub = mgrn[mgrn["TF"].isin(active) & mgrn["target"].isin(active)].copy()
    sub.to_csv(f"results/dap/subnetwork/{t}_subGRN.csv", index=False)
```

- `(expr[cols] > 1.0).mean(axis=1)`，在该组织的分组里表达超过 CPM 1 的比例，这里与建网时用的阈值一致。
- `isin(active)`，边的两端都要在该组织活跃，只留一端会连出大量在该组织不表达的节点，组织比较结果就失真了。
- 每个组织一个文件，文件名就是组织名，后面所有步骤按文件名找组织，命名不要加空格。

每个组织单独出一个子网络，同时记下它的规模：

```python
summary.append({"tissue": t, "n_active_genes": len(active), "n_edges": len(sub),
                "n_tf": sub["TF"].nunique() if len(sub) else 0,
                "n_target": sub["target"].nunique() if len(sub) else 0,
                "n_target_pref": int(sub["target_pref"].sum())})
```

- 单个组织的边数与活跃基因数先看一眼。某个组织的活跃基因数特别少，说明该组织的测序深度或细胞数不足，后面它的模块特别小就是这个原因，不是调控更简单。
- `n_target_pref`，该组织里靶基因偏好于本组织的边数，是组织特异调控的初步计数。

## 模块与功能富集

用 igraph 在网络里做社区检测得到模块，模块就是连得比较紧的一组基因。网络分析的单位是模块，单条边的功能往往没有意义，一组共同调控的靶基因才能给出清晰的通路信号。

```r
library(igraph)
edges <- as.matrix(el[, c("TF", "target")])
g <- graph_from_edgelist(edges, directed = FALSE)
g <- simplify(g, remove.multiple = TRUE, remove.loops = TRUE)
comm <- cluster_louvain(g, weights = NULL)
memb <- membership(comm); n_mod <- max(memb)
```

- `graph_from_edgelist`，第一列是边的起点，第二列是终点。
- `directed = FALSE`，模块划分只看连接的紧密程度，方向不影响划分结果。
- `simplify`，去掉重复边和自环。同一对基因被多个峰支持会重复出现，不去掉会虚增该边的权重。
- `cluster_louvain`，模块度优化的社区检测，不需要预设模块数，比 fast greedy 稳定。
- 模块可注释基因不到 20 个的不做富集，富集结果每个模块只留最显著的几条。

富集用超几何检验，前景是该模块的基因集，背景是网络里出现的全部基因。先把注释读进来，

```r
library(readr)
library(readxl)
go_terms <- read_tsv("gene_list/go_basic_terms.tsv", show_col_types = FALSE)
go_info  <- setNames(go_terms$name, go_terms$go_id)
go_anno  <- read_excel("gene_list/go_anno.xlsx")
gene2go  <- split(go_anno$go_id, go_anno$gene_id)
go2gene  <- split(go_anno$gene_id, go_anno$go_id)
all_bg_genes <- unique(go_anno$gene_id)
```

- `go_basic_terms.tsv`，从 `go-basic.obo` 解析出来的编号、名称、命名空间三列；`go_anno.xlsx` 是基因到 GO 的映射，ID 统一转成同一套写法后再用。
- `split(go_anno$go_id, go_anno$gene_id)` 与反向的那一次，把长表转成基因到 GO、GO 到基因两个列表，富集时两边都要查。
- `all_bg_genes`，有 GO 注释的全部基因，也就是富集分析的背景。

接着做 GO 富集，先把注释表拆成基因到 GO 和 GO 到基因两个方向：

```r
library(dplyr)
ora <- function(mod_genes) {
  mod_ann <- intersect(mod_genes, all_bg_genes)
  if (length(mod_ann) < 20) return(NULL)
  k <- length(mod_ann); N <- length(all_bg_genes)
  terms <- unique(unlist(gene2go[mod_ann]))
  res <- lapply(terms, function(g) {
    x <- sum(mod_ann %in% go2gene[[g]])
    m <- length(intersect(go2gene[[g]], all_bg_genes))
    p <- phyper(x - 1, m, N - m, k, lower.tail = FALSE)
    data.frame(go_id = g, n_module = x, n_bg = m, pvalue = p, go_name = go_info[g])
  })
  res <- bind_rows(res) %>% arrange(pvalue)
  res$qvalue <- p.adjust(res$pvalue, method = "BH")
  res$is_hub <- grepl("photosynthesis|kinase|transcription factor|binding", res$go_name, ignore.case = TRUE)
  res
}
```

- `phyper(x - 1, m, N - m, k, lower.tail = FALSE)`，超几何检验的右尾概率。参数依次是模块里落在该 GO 的基因数、背景里落在该 GO 的基因数、背景总数、模块中可注释的基因数。
- `length(mod_ann) < 20`，可注释基因不到 20 个的模块直接跳过，这类模块的富集结果不稳。
- `N` 取网络里出现的基因数，不是全部表达基因。背景取大了会把显著性高估，这是富集分析最常见的错误。
- `p.adjust(..., method = "BH")`，多重检验校正，模块多、GO 条目更多，不校正全是显著。
- `grepl("photosynthesis|kinase|transcription factor|binding", ...)`，这几个词干是出现频率很高的泛化条目，富集到它们的模块后面单独标注并从深度结果里剔除。

富集要判断模块是不是组织特异，先读回每个基因在各组织的平均表达：

```r
expr <- as.matrix(read.csv("results/dap/tissue_expression_mean.csv", row.names = 1, check.names = FALSE))
top_tissue <- setNames(colnames(expr)[max.col(expr, ties.method = "first")], rownames(expr))

all_go <- bind_rows(lapply(list.files("results/dap/subnetwork", pattern = "_subGRN.csv$", full.names = TRUE), function(f) {
  out <- ora(unique(read_csv(f, show_col_types = FALSE)$target))
  if (is.null(out)) return(NULL)
  out$tissue <- sub("_subGRN.csv$", "", basename(f))
  out
}))
```

- `tissue_expression_mean.csv`，上游算好的基因乘组织平均表达，行名是基因，列名是组织。
- `max.col(expr, ties.method = "first")`，逐行取最大值所在的列号，并列时取第一个，转成基因到组织的命名向量就得到 `top_tissue`。
- `all_go`，把每个组织的子网络基因集跑一遍 `ora`，结果拼成一张表，同时把组织名写成一列，后面按组织筛选靠它。

逐个组织算富集，结果拼成一张表：

```r
for (tissue in unique(all_go$tissue)) {
  mod_genes <- unique(read_csv(paste0("results/dap/subnetwork/", tissue, "_subGRN.csv"), show_col_types = FALSE)$target)
  gs <- intersect(mod_genes, names(top_tissue))
  all_go$tissue_marker_frac[all_go$tissue == tissue] <- if (length(gs)) mean(top_tissue[gs] == tissue) else 0
}
deep <- all_go %>% filter(tissue_marker_frac >= 0.5, !is_hub)
write_csv(deep, "results/dap/module_go_tissue_specific_deep.csv")
```

- `top_tissue`，每个基因在哪个组织表达最高，按伪 bulk 的组织均值算。
- `all_go$tissue_marker_frac`，模块内基因里有多少比例以本组织为最高表达组织，0.5 以上算组织特异模块。
- `deep`，只看组织特异模块并且剔除 hub 类富集，剩下的才是能写进结论的通路。

每个组织取显著条目画一张气泡图，再把所有组织拼成一张大图，

```r
library(ggplot2)
library(patchwork)
panels <- list()
for (t in unique(all_go$tissue)) {
  d <- all_go %>% filter(tissue == t, qvalue < 0.05) %>% slice_min(pvalue, n = 15) %>% ungroup()
  d$logp <- -log10(d$pvalue)
  panels[[t]] <- ggplot(d, aes(x = logp, y = reorder(go_name, logp))) +
    geom_point(aes(size = n_module, color = logp)) +
    scale_size_continuous(name = "Gene count", range = c(12, 32)) +
    labs(title = t, x = "-log10(p)", y = NULL) + theme_bw(base_size = 50)
}
fig <- wrap_plots(panels, ncol = 4)
ggsave("results/dap/module_go_integrated.pdf", fig, width = 110, height = 78, limitsize = FALSE)
```

- `panels[[t]]`，每个组织一张子图，存在按组织名索引的列表里，`wrap_plots` 按列表顺序拼接。
- `d$logp <- -log10(d$pvalue)`，把 p 值转成绘图用的对数刻度。
- `reorder(go_name, logp)`，纵轴按显著性排序，条目按名字排会反复看串行。

- `qvalue < 0.05`，只画校正后显著的条目。
- `slice_min(pvalue, n = 15)`，每个组织取最显著的 15 条，取多了图上看不出差别。
- `scale_size_continuous(range = c(12, 32))`，点的大小表示模块里落在该条目的基因数，同时看显著性和规模。
- `limitsize = FALSE`，输出尺寸超过 ggplot 的默认限制，不关掉这一步会直接报错。

## 网络结构与 hub

度分布、每个转录因子的出度、转录因子在各组织的活性热图，用来回答谁是这个网络的枢纽。hub 就是网络里连接数很高的节点。

```r
mgrn <- read_csv("results/dap/mgrn_plus.csv")
hub <- mgrn %>% count(TF, name = "n_targets") %>% arrange(desc(n_targets)) %>%
  left_join(mgrn %>% distinct(TF, TF_name), by = "TF")
write_csv(hub, "results/dap/summary/hub_tf.csv")
```

- `count(TF, name = "n_targets")`，每个转录因子连的靶基因数，也就是出度。
- `distinct(TF, TF_name)`，去重后再连接，否则连接会按边的条数把表撑大。
- 出度只统计不重复的靶基因。同一条边被多个峰支持时，边表里已经去过重，这里不用再管。

边表汇总完统计每个转录因子的出度，出度高的就是枢纽：

```r
top_tf <- head(hub, 20)
p1 <- ggplot(top_tf, aes(reorder(TF, n_targets), n_targets, fill = n_targets)) +
  geom_col(show.legend = FALSE) + coord_flip() +
  scale_x_discrete(labels = setNames(top_tf$TF_name, top_tf$TF)) +
  labs(title = "Top hub TFs (global mGRN+)", x = NULL, y = "n targets") + theme_bw(base_size = 13)
p2 <- ggplot(hub, aes(n_targets)) + geom_histogram(bins = 40, fill = "steelblue") +
  scale_x_log10() + labs(title = "TF out-degree distribution", x = "n targets (log)", y = "count") + theme_bw(base_size = 13)
ggsave("results/dap/summary/hub_tf.pdf", p1 + p2, width = 14, height = 6, limitsize = FALSE)
```

- `coord_flip()`，横过来画，基因名才能横着读。
- `scale_x_log10()`，出度分布跨度大，取对数才看得出形状。看的是长尾有多长，几个度数很高的转录因子就是候选 hub。
- 两条图并排，左边是排名，右边是分布，用来判断出度是平滑衰减还是被少数转录因子垄断。

组织乘转录因子的活性矩阵，用每个转录因子在各组织子网络里的靶基因数表示，

```r
sub_files <- list.files("results/dap/subnetwork", pattern = "_subGRN.csv$", full.names = TRUE)
tissues <- sub("_subGRN.csv$", "", basename(sub_files))
mat <- matrix(0, nrow = nrow(hub), ncol = length(tissues), dimnames = list(hub$TF, tissues))
for (i in seq_along(sub_files)) {
  el <- read_csv(sub_files[i], show_col_types = FALSE)
  tt <- table(el$TF)
  mat[names(tt), tissues[i]] <- as.numeric(tt)
}
mat <- mat[order(rowSums(mat), decreasing = TRUE), , drop = FALSE]
```

- `sub_files`，子网络目录下的全部 `_subGRN.csv`，文件名前缀就是组织名。
- `table(el$TF)`，该组织子网络里每个转录因子连的靶基因数。
- 只填已有组织的列，没有出现过的转录因子保持 0，画热图时才看得出哪个转录因子只在个别组织活跃。
- `order(rowSums(mat))`，按跨组织总活性排序，热图的行顺序就是活性排名。

把每个转录因子在各组织的活性做成热图，看谁只在个别组织活跃：

```r
mat_melt <- as.data.frame(as.table(mat), stringsAsFactors = FALSE)
names(mat_melt) <- c("TF", "tissue", "n_target")
labels <- setNames(hub$TF_name, hub$TF)
p3 <- ggplot(mat_melt, aes(tissue, TF, fill = n_target)) + geom_tile() +
  scale_fill_viridis_c(name = "n targets") +
  scale_y_discrete(labels = function(x) ifelse(is.na(labels[x]), x, labels[x])) +
  labs(title = "TF activity across tissues", x = NULL, y = NULL) + theme_minimal(base_size = 12)
```

- `geom_tile()`，块的颜色是靶基因数。同一个转录因子在不同组织行里颜色差别大，说明它换了一批靶基因。
- `scale_y_discrete(labels = ...)`，把 ID 换成基因名显示。映射不到时退回 ID，不要留空标签。

再做一次置换检验，看网络是否真的把通路基因富集到了相关组织里。以子叶网络里的光合作用基因为例，

```r
known <- go_anno %>% filter(grepl("phot", go_name) | grepl("photosynth", go_name, ignore.case = TRUE)) %>%
  pull(gene_id) %>% unique()
known <- union(known, go_anno %>% filter(grepl("GO:0015979", go_id)) %>% pull(gene_id))
lt <- read_csv("results/dap/subnetwork/cotyledon_subGRN.csv", show_col_types = FALSE)
leaf_targets <- unique(lt$target)
pool <- unique(go_anno$gene_id)
obs <- sum(leaf_targets %in% known)
K <- length(known); N <- length(pool); n <- length(leaf_targets)
null <- replicate(10000, sum(sample(pool, n) %in% known))
pval <- (sum(null >= obs) + 1) / (length(null) + 1)
```

- `known`，用 GO 名称里的 phot、photosynth 加上显式的 GO:0015979 两条口径取并集，单用一条会漏。
- `pool`，有 GO 注释的全部基因，抽样从这里抽，不能用全部表达基因当池子。
- `replicate(10000, ...)`，每次随机抽与观测同样多的靶基因，数命中数，重复一万次得到零分布。
- `(sum(null >= obs) + 1) / (length(null) + 1)`，加一修正的经验 p 值，避免出现 p 等于 0。
- `expected = n * K / N`，随机期望命中数。观测值明显高于它、p 值很小，才说明网络有通路层面的召回能力。

## 组织间比较

组织间比较看两件事，哪些边是多个组织共有的，通常是核心调控；哪些边是某个组织特有的，往往与该组织的功能相关。判据用边的两端在同一组织里是否都活跃，再加上靶基因的组织偏好性，

```r
edge_sets <- list()
info <- data.frame()
for (t in tissues) {
  d <- read_csv(paste0("results/dap/subnetwork/", t, "_subGRN.csv"), show_col_types = FALSE)
  d$edge <- paste(d$TF, d$target, sep = "|")
  d$tissue <- t
  edge_sets[[t]] <- unique(d$edge)
  info <- rbind(info, d[, c("edge", "tissue", "target_pref")])
}
res <- info %>% count(edge, name = "n_tissues_active") %>%
  left_join(info %>% filter(target_pref) %>% count(edge, name = "n_target_pref"), by = "edge") %>%
  mutate(n_target_pref = ifelse(is.na(n_target_pref), 0, n_target_pref)) %>%
  mutate(class = ifelse(n_tissues_active >= 6, "core", ifelse(n_target_pref == 1, "specific", "shared")))
```

- `n_tissues_active`，这条边的两端在几个组织里同时活跃。8 个组织的实验里取 6 作为核心边的门槛。
- `n_target_pref == 1`，靶基因只在一个组织里高于自身跨组织平均，并且边在该组织成立，算组织特异调控。
- 两类之外的边算 shared，在多个组织里活跃，但靶基因没有明显偏好。
- `edge_sets`，每个组织的边集合，后面算两两 Jaccard 用它。
- `info`，把各组织的边表摞起来，边的多组织活跃数和靶基因偏好数都从它数出来。
- `target_tau >= 0.5`，用 mgrn 表里已有的组织特异性指数另存一列，两类判据可以对照着看，结论不一致的边要单独查。

两两 Jaccard 指数用来看哪个组织对最相似，

```r
jacc <- matrix(NA_real_, length(tissues), length(tissues), dimnames = list(tissues, tissues))
for (i in seq_along(tissues)) for (j in seq_along(tissues)) {
  a <- edge_sets[[tissues[i]]]; b <- edge_sets[[tissues[j]]]
  jacc[i, j] <- length(intersect(a, b)) / length(union(a, b))
}
write.csv(round(jacc, 4), "results/dap/tissue_edge_jaccard.csv")
```

- 边用 `TF|靶基因` 字符串表示，`intersect` 与 `union` 直接作用在字符向量上。
- `length(intersect(a, b)) / length(union(a, b))`，交集除以并集，取值 0 到 1。
- 叶与子叶、茎与茎尖这类同源组织的值通常最高，花粉与其它组织的值最低。对角线上恒等于 1，只是自比，不参与比较。
- 矩阵存成 CSV，画热图时行名列名同时读回来，行列顺序不会乱。

组织特异的边单独计数，用来判断某个组织是不是真的有自己的调控模块，

```r
sp_by_tissue <- info %>% filter(target_pref) %>%
  filter(edge %in% res$edge[res$class == "specific"]) %>%
  count(tissue, name = "n_specific_edges")
write_csv(sp_by_tissue, "results/dap/tissue_specific_edge_count.csv")
```

- 先过滤出靶基因偏好本组织的边，再限定在判定为 specific 的边里计数。
- 某个组织的特异边特别少，先查它的活跃基因数，很可能是数据量不足而不是调控简单。

## 表达验证

网络连出来之后回到表达数据检查它是否可信，这一步不能省。三件事，转录因子与靶基因的表达在样本层面是否相关，边两端的表达是否落在同一类细胞里，hub 转录因子的组织表达是否与它在子网络里的分布一致。

```r
expr <- read.csv("results/dap/tissue_expression_mean.csv", row.names = 1, check.names = FALSE)
tissues <- colnames(expr)
ef <- read_csv("gene_list/dap_tf_mapping.csv", show_col_types = FALSE)
tf_ids <- intersect(ef$tf_geneid, rownames(expr))
tf_mat <- as.matrix(expr[tf_ids, tissues, drop = FALSE])
```

- `tissue_expression_mean.csv`，伪 bulk 的组织均值表达，与前面表达层用的是同一份数据。
- `row.names = 1`，第一列是基因 ID，读成行名才能按基因取子集。
- `check.names = FALSE`，组织名里有连字符、下划线这类字符，不让 R 改写列名，否则后面按名字取列会失败。
- `intersect(ef$tf_geneid, rownames(expr))`，只留既在 DAP 转录因子表里、又在表达矩阵里的基因。两边对不上时取交，不要用 `dap_tf_mapping.csv` 的整张表直接索引，那会出一堆 NA 行。

第一件事，看转录因子的组织表达谱，

```r
library(pheatmap)
tf_l <- log1p(tf_mat)
fam <- setNames(ef$gene_family, ef$tf_geneid)
rowann <- data.frame(family = fam[rownames(tf_l)], row.names = rownames(tf_l))
pheatmap(tf_l, cluster_rows = TRUE, cluster_cols = TRUE, scale = "row",
         annotation_row = rowann, main = "TF expression across tissues (row z, log CPM)",
         fontsize_row = 6, fontsize_col = 10,
         filename = "results/dap/fig_tf_fpkm_heatmap.pdf",
         width = 8, height = max(8, 0.28 * nrow(tf_l)))
```

- `log1p(tf_mat)`，表达量跨几个数量级，先取对数再加行标准化，不然颜色全被最高表达的几行占掉。
- `setNames(ef$gene_family, ef$tf_geneid)`，用基因 ID 给家族名建查找表，这是 R 里把一列映射到另一列最直接的做法。
- `annotation_row = rowann`，在热图左侧标出每个转录因子属于哪个家族，同一家族的成员往往成块出现。
- `height = max(8, 0.28 * nrow(tf_l))`，行数多的时候按每行 0.28 英寸拉高，行名不会被压成一团。
- 检查点，只在某个组织表达的转录因子，不应该在其它组织里连出大量边。出现这种行就回头查子网络的活跃基因判定。

第二件事，逐组织统计边的两端是否都有表达，

```r
sub_files <- list.files("results/dap/subnetwork", pattern = "_subGRN.csv$", full.names = TRUE)
tnames <- sort(sub("_subGRN.csv$", "", basename(sub_files)))
check <- data.frame()
for (t in tnames) {
  d <- read_csv(file.path("results/dap/subnetwork", paste0(t, "_subGRN.csv")), show_col_types = FALSE)
  ba <- mapply(function(a, b)
    (is.finite(expr[a, t]) && expr[a, t] > 1.0) &&
    (is.finite(expr[b, t]) && expr[b, t] > 1.0), d$TF, d$target)
  check <- rbind(check, data.frame(tissue = t, n_edges = nrow(d),
                                   n_both_active = sum(ba), frac = sum(ba) / nrow(d)))
}
write_csv(check, "results/dap/edge_expr_check.csv")
```

- 1.0 这个 CPM 下限与组织子网络建网时的活跃基因阈值一致，两边不同会让统计和建网对不上。
- `list.files(..., pattern = "_subGRN.csv$")`，把所有组织子网络的边表列出来，组织名从文件名里剥出来。以后新增组织不用改脚本。
- `is.finite(expr[a, t])`，基因不在表达矩阵里时取出来是 NA，`is.finite` 先把它挡掉。直接比较 NA 会得到 NA，`sum()` 数出来是错的。
- `mapply(..., d$TF, d$target)`，把边表的两列逐行传进函数，得到一条逻辑向量，`sum(ba)` 就是两端都表达的边数。
- 输出每个组织的边数、两端都表达的边数和比例。比例明显偏低的组织，那里的子网络主要由一端不表达的边组成，不要拿它去讲组织特异的调控关系。

第三件事，看连接数最多的转录因子是否真的在对应组织里高表达，

```r
ed <- read_csv("results/dap/edge_shared_vs_tissue_specific.csv", show_col_types = FALSE)
ed$target_cpm <- mapply(function(e, top) {
  tg <- sub(".*\\|", "", e)
  v <- if (is.finite(expr[tg, top])) expr[tg, top] else NA_real_
  v
}, ed$edge, ed$target_top_tissue)
```

- `edge_shared_vs_tissue_specific.csv`，前面比较核心、共有、特异边时输出的边表，这里按边的类别分组。
- `sub(".*\\|", "", e)`，边名字段写成 `TF|target`，取竖线后面的靶基因。
- `ed$target_top_tissue`，每条边自己记录靶基因表达最高的组织，按这个组织取 CPM，而不是统一用某一个组织。
- 取不到值的边回填 NA，画图时由 `filter(!is.na(target_cpm))` 拿掉。

最后回头核对边的表达证据，看这类边在靶基因的组织里是不是真的高表达：

```r
p_verify <- ggplot(check, aes(tissue, frac, fill = tissue)) +
  geom_col(width = 0.6) +
  geom_text(aes(label = sprintf("%.0f%%", 100 * frac)), vjust = -0.3, size = 4) +
  scale_y_continuous(limits = c(0, 1.05), labels = scales::percent) +
  scale_fill_brewer(palette = "Set2") +
  theme_bw(base_size = 15) + theme(legend.position = "none",
    axis.text.x = element_text(angle = 35, hjust = 1)) +
  labs(x = NULL, y = "% edges with both TF & target active (tissue CPM > 1)")

p_tgt <- ggplot(ed %>% filter(!is.na(target_cpm)), aes(class, log1p(target_cpm), fill = class)) +
  geom_boxplot(outlier.size = 0.4) +
  scale_fill_manual(values = c(core = "#2166AC", shared = "#92C5DE", specific = "#D95F02")) +
  theme_bw(base_size = 15) + theme(legend.position = "none") +
  labs(x = NULL, y = "target log1p(CPM) in its top tissue")

ggsave("results/dap/fig_edge_expr_verify.pdf", p_verify + p_tgt + plot_layout(ncol = 2), width = 14, height = 5.5, limitsize = FALSE)
```

- 左图是各组织「两端都表达」的边占比，柱顶直接标百分比，比看刻度快。`scale_y_continuous(limits = c(0, 1.05))` 给文字标签留出空间。
- 右图把核心、共有、特异三类边的靶基因表达放在一起比。特异边的靶基因应该在它自己的最优组织里表达更高，如果三类分布完全重合，说明组织特异性这个划分没抓住表达上的差别。
- `fill = class` 之外同时写 `scale_fill_manual`，颜色与前面 `edge_shared_vs_tissue_specific.csv` 相关的图保持一致，读者不用重新对照图例。
- `plot_layout(ncol = 2)` 来自 patchwork，两张图拼成一行；组织多的时候把宽度调大而不是把图缩得看不清。

后续还有几组汇总，网络边数与节点数的总表、组织 hub 的功能注释、每次运行的 GO 富集与共同特异分析、模块在组织与细胞类型两个分辨率上的一致性、转录因子结合位点特征与转录因子自身性质的对照、多个转录因子靶基因的重叠关系。这些都在 `mgrn_plus.csv` 与各组织子网络之上做，输入不满足时对应脚本直接跳过并打印原因，不会生成空结果文件。

## 与已有做法的差异

这些差异影响结论的解释范围，写文章时要交代清楚。

- 启动子窗口取 3 kb，即 TSS 上游 `[-3000, 0]`，有的研究用 5 kb。窗口大小直接影响边的数量，必须写明。
- 没有染色质可及性数据，因此没有可及性那一层网络，最终网络只有物理层与表达层两个交集。
- 表达层内部也是一次交集，GRNBoost2 跑在单细胞稀疏矩阵上，默认抽样 3 万细胞；皮尔逊相关跑在按样本和细胞类型聚合的伪 bulk 上，不是用成千上万份 bulk 样本跑出来的一致性网络。
- 没有 motif 预测层，也没有 de novo motif 发现，只用 DAP-seq 峰这一层实验证据。
- 没有峰质控。上游只给了 narrowPeak 文件而没有原始比对结果，峰的质量无法评估，这一点要在方法里说明。
- 没有用随机森林之类的机器学习方法筛选关键转录因子，hub 只按连接数定义，再用组织表达与置换检验做旁证。
- 过滤阈值整体放宽，都写成代码里的字面值。换数据集时改这几处，不要改脚本逻辑，否则不同批次的结果没法比。
- 复现性上，R 侧与 Python 侧都在开头固定随机种子和抽样上限，组织子网络的阈值同样写在代码里，唯一的可调项是种子。
