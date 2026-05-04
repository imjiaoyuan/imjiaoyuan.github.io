---
title: Python library for bioinformatics and scientific computing
date: 2026-05-02
---

这个包整合了我之前写过的一些用作分析和画图的脚本，做成 pip 包用起来会更方便，不需要输入路径去调用了，并且也可以作为基础来扩展更多的功能，现在有 agent 加持，写这种包还是很简单的。这里的脚本主要都是用于生信分析和可视化的，我起名字叫`jsrc`，用我的名字首字母开头，`src`就是源代码的意思了，`jsrc` 按功能分成模块，各模块之间没有依赖关系，想用哪个用哪个。

项目地址：https://github.com/imjiaoyuan/jsrc

使用 pip 安装：

```bash
pip install jsrc
```

不过现在可能 uv 才是版本答案，可以自动解决依赖问题：

```bash
uv venv
uv run jsrc -h
```

依赖上做过一轮瘦身，现在只剩画图用的 matplotlib 一个第三方依赖，序列解析、翻译、比对、建树这些全部换成了自带的纯标准库实现（接口基本沿用 Biopython 的习惯），不用为了跑一个子命令装一堆包。

CLI 入口是 `jsrc`，后面跟模块名和子命令。模块都使用懒加载，用到哪个才 import 哪个，启动速度不受模块数量影响。如果不想加载某些模块，可以通过环境变量控制：

```bash
export JSRC_DISABLE_MODULES=grn         # 禁用不用的模块
export JSRC_MODULES=seq,genome,analyze  # 或者只启用某几个
```

目前有 5 个模块，覆盖序列处理、基因组分析、可视化和基因调控网络：

```
seq      序列提取、翻译、重命名、k-mer 统计
genome   基因组统计、CpG/ORF/重复序列、密码子、ANI、滑窗 GC
plot     基因/染色体/结构域/顺式元件/点图/环形图可视化
analyze  系统发育、motif、一致序列、SNP/INDEL、QC
grn      基因调控网络格式转换、中心性、交互式网络 viewer
```

## 序列操作

这是最简单常用的模块，生信分析中反复出现的场景就是从基因组里提取特定区域啥的，seq 模块把这些操作统一成了几个子命令。

手里有基因组 FASTA、GFF 注释文件、以及一个基因 ID 列表，可以使用`extra`提取这些基因的指定类型序列，比如 CDS 序列：

```bash
jsrc seq extract -fa genome.fa -gff genes.gff -ids ids.txt -o cds.fa -feature CDS -match Parent
```

这里 `-feature` 指定提取 CDS，也可以改成 gene、exon、mRNA 等，要看注释文件中对应的是什么。`-match` 是 GFF 属性里用来匹配 ID 列表的字段，也是要从注释文件中查看的。`-match Parent` 代表 ID 列表里的是基因名，而 GFF 的 CDS 行用 `Parent` 属性指向对应的基因。这个命令不是简单地找相同 ID 就提取，它会把同一个基因的多个 CDS 片段按照染色体坐标排序，合并重叠区域，再连成一条完整序列。遇到负链基因会自动取反向互补。输出是一个 FASTA，每个基因一条记录。

提取 CDS 后可以翻译成氨基酸序列：

```bash
jsrc seq translate -fa genome.fa -gff genes.gff -id ID -o proteins.fa
```

它会解析 GFF 里的 CDS 特征，按基因分组、排序坐标、从基因组取序列，遇到负链自动反向互补，最后用内置的翻译实现翻成蛋白。碰到长度不是 3 的倍数的序列会截掉末尾多出来的碱基再翻译，并且给出警告。

不同来源的序列 ID 格式各不相同，命名方式五花八门，rename 可以把它们统一成自己想要的格式，支持 CSV 映射和 GFF 关联两种模式：

```bash
jsrc seq rename -fa in.fa -mode csv -map mapping.csv -o out.fa

jsrc seq rename -fa in.fa -mode gff -gff genes.gff -parent Parent -o out.fa
```

CSV 就是一个两列的映射表，第一列是原名，第二列是新的名称。GFF 模式则更适合从基因组注释做重命名，比如拿 mRNA 的 ID 去匹配它在 GFF 中的父基因名。

k-mer 算是序列的"成分指纹"，这个命令既可以对单条序列做高频 k-mer 统计，也可以在多个样本间算余弦距离：

```bash
# 单样本，看高频 k-mer
jsrc seq kmer -fa a.fa -k 7 --top 30

# 多样本，算两两余弦距离
jsrc seq kmer -fa a.fa b.fa c.fa -k 5
```

多文件时输出的是一个距离矩阵，值在 0 到 1 之间，越接近 0 表示序列组成越相似。可以用来快速判断样本间是否大体一致。

## 基因组分析

拿到一个新组装之后要做的一堆例行检查——N50、gap、GC、CpG island、ORF、密码子偏好——都归在 genome 模块。

先看组装本身的统计：

```bash
jsrc genome stats -fa genome.fa
```

输出 N50、L50、序列条数、总长、GC 占比（只算 ACGT 碱基）和 gap 数，属于拿到新组装先跑一遍心里有数的东西。

CpG island 预测，按窗口扫 GC 含量和 CpG 的观察值/期望值比，圈出符合条件的区段：

```bash
jsrc genome cpg -fa genome.fa --window 200 --min-len 500
```

基因组之间估个相似度，用 k-mer 的 Mash 距离换算成 ANI，比老老实实跑一遍全基因组比对快得多，做菌株分型的时候很好用：

```bash
jsrc genome ani -fa1 genome1.fa -fa2 genome2.fa -k 21
```

此外还有找 ORF（`jsrc genome orf`）、简单重复序列（`jsrc genome repeat`）、基因组岛（`jsrc genome island`）、反向重复/回文（`jsrc genome palindrome`）、Ka/Ks（`jsrc genome kaks`）、两两遗传距离（`jsrc genome distance`）这些常规粗筛，基本够用了。

做顺式元件分析经常需要批量截取启动子。promoter 按基因列表一把全提出来，可以对每个基因指定上游和下游的长度：

```bash
jsrc genome promoter -fa genome.fa -gff genes.gff -ids genes.txt -o promoters.fa -up 2000 -down 0
```

正链基因取起始密码子上游 N bp，负链基因取终止密码子下游 N bp（也就是上游）并反向互补。坐标超出染色体边界也会自动 clamp。

从 CDS 序列计算密码子使用频率和 RSCU 值。RSCU > 1 表示该密码子使用偏多，< 1 表示偏少：

```bash
jsrc genome codon -fa cds.fa --top 20 --json
```

它会按阅读框解析 CDS，跳过终止密码子和非 ACGT 字符，然后对每个氨基酸分别计算 RSCU。单条 CDS 或多条合并都可以。给一个参考 CDS 还能顺手算 CAI 和 ENC：

```bash
jsrc genome codon -fa cds.fa --cai reference.fa --enc
```

GC 含量沿染色体的分布不是均匀的，滑窗分析能揭示局部变化。window 会在指定序列上做滑窗统计，输出每个窗口的 GC%、AT skew 和 GC skew：

```bash
jsrc genome window -fa genome.fa -id chr1 -w 1000 -s 200 --head 20
```

GC skew 的正负可以指示复制起点和终止点的位置（前导链倾向于 G 多于 C），这在原核基因组分析中比较有用；加上 `--cumulative` 会输出累积 GC skew 曲线，直接给出复制起点/终止点的预测位置。

## 一些简单的分析操作

序列比对做完之后，常见操作就是建树、找 motif、看保守性、找差异。analyze 把这些串了起来，但是本着使用尽量少的依赖的原则（极简主义者癖好），所以目前实现的分析其实比较有限。

对一组比对好的或未比对的序列，用邻接法或 UPGMA 建一棵树，输出 Newick 格式。底层的遗传距离和 NJ/UPGMA 建树都是自己实现的，行为对齐 Bio.Phylo：

```bash
# 邻接法（默认）
jsrc analyze phylo -fa aligned.fa -o tree.nwk

# UPGMA
jsrc analyze phylo -fa aligned.fa -a upgma -o tree.nwk
```

输入序列未比对的话会自动做等长填充（短的补 `-`）。输出的 Newick 可以用任意树可视化软件查看。

同一个命令加 `-n` 就是 bootstrap 版本——重复采样给分支打上置信度。重复次数和随机种子都可以设置，保证结果可重复：

```bash
jsrc analyze phylo -fa seqs.fa -n 200 -seed 42 -o boot.nwk
```

内部实现是先构建基准树，然后对多序列比对的列做有放回重采样，每次重采样重新建树，统计每个分支出现的频率作为 bootstrap 值。需要至少 3 条序列。

最直接的 motif 寻找方式——从序列中枚举所有 k-mer，按出现频率排序。虽然不如 MEME 这类专业工具精细，但胜在速度快、结果直观，适合先粗筛再决定要不要上更重的工具：

```bash
jsrc analyze motif -fa promoters.fa -o motif_out -nmotifs 5 -minw 6 -maxw 12
```

从多序列比对中计算一致序列和每个位点的保守性分数。保守性 = 该位点出现频率最高的碱基的比例，数值越高表示该位点越保守：

```bash
jsrc analyze msa_consensus -fa aligned.fa --json
```

可以用来快速判断比对质量：整体保守性高说明序列之间相似性好，适合做进化分析；如果整体保守性偏低，可能需要换个比对策略。

只比对两条序列，给出 SNP 和 INDEL 的详细统计。用内置的 `PairwiseAligner`（接口照搬 Biopython）做全局比对：

```bash
jsrc analyze snpindel -fa pair.fa --json
```

输出比对得分、对齐长度、匹配碱基数、SNP 数、INDEL 事件数和涉及的碱基数。非常适合做同一基因在不同样本间的快速比较。

这个命令可以同时接收 FASTA（组装统计）、SAM（比对统计）、VCF（变异统计）、FASTQ（测序统计），一次性给出多角度的质量概览：

```bash
jsrc analyze qc -fa assembly.fa -sam aln.sam -vcf variants.vcf.gz -fq r1.fq.gz r2.fq.gz -gs 520000000
```

单看 FASTA 的话就是最轻量的 QC，适合在进入复杂分析前快速看一眼序列的基本状况：

```bash
jsrc analyze qc -fa assembly.fa
```

```
QC: 2 sequences, 268 bp total, GC 56.7%, N50 160.
```

给 FASTQ 和基因组大小还能估算测序深度。`--json` 输出结构化数据方便后续处理，FASTQ.GZ 也直接支持，不需要先解压。解析 SAM 比对 CIGAR 算深度、区分 VCF 里的 SNP 和 INDEL 也在同一个命令里，适合做完整套分析后做一次统一汇总。

## 简单的可视化

做生信分析少不了要画图，不管是汇报还是文章。plot 模块把几种最常见的生物学图形封装成了命令行，输入 GFF 或 TSV 就可以出图，省去写 matplotlib 代码的时间。

所有图都输出 PNG，内核统一用 matplotlib Agg 后端，不需要显示器环境。

GFF + ID 列表画基因结构示意图。每个基因用一条水平线表示全长，蓝色方块表示 CDS 区域：

```bash
jsrc plot gene -gff genes.gff -ids ids.txt -o gene.png -dpi 300
```

基因会按自然序（chr9 排在 chr10 前面，而不是字典序）纵向排列，适合展示多个基因的结构差异。

用 `--feature` 换个特征类型，就能看别的结构，比如只关心外显子的数量和分布差异，就画 exon：

```bash
jsrc plot gene -gff genes.gff -ids ids.txt --feature exon -o exon.png -dpi 300
```

默认画 CDS，GFF 里有的特征比如 `five_prime_UTR` 也能直接指定。

把基因在染色体上的位置可视化出来。读取 GFF 里的 `##sequence-region` 元数据作为染色体长度，然后在对应位置画红色标记：

```bash
jsrc plot chromosome -gff genes.gff -ids ids.txt -o chr.png
```

不加 `-ids` 时把所有基因都画上，加了就只标出目标基因。适合看基因在染色体上的聚集情况。

TSV 格式输入，每行是一个结构域，包含蛋白名、结构域名、起始和终止位置：

```bash
jsrc plot domain -tsv domains.tsv -o domain.png
```

每个蛋白一条水平线，结构域用橙色方块标出并标注名称。适合快速查看结构域顺序和相对位置。

BED 格式输入，在染色体上标出顺式元件的分布：

```bash
jsrc plot cis -bed motifs.bed -o cis.png
```

每条染色体画一条水平线，元件用蓝色竖线标出，并带名称标签。

用精确 k-mer 匹配画两条序列的点图。对角线上的点表示两序列的共线性区域，散落在外的点可能代表重复序列或重排：

```bash
jsrc plot dotplot -fa1 genome1.fa -fa2 genome2.fa -k 10 -o dotplot.png
```

`-k` 控制 k-mer 大小：k 越小点越密但假阳性越多，k 越大特异性越高。命令行环境用的是 Agg 后端，`-o` 记得写上，否则图画出来也看不到。

一个轻量级的 Circos 替代方案——输入 FASTA，画出环形染色体分布图，内圈显示 GC 含量滑窗统计：

```bash
jsrc plot circoslite -fa genome.fa -w 100000 -o circos.png
```

`-w` 控制滑窗大小，默认 100 kb。外圈灰色环是染色体骨架，内圈蓝色柱子表示该窗口的 GC 比例。

## 基因调控网络可视化

这个是我自认为做的很好看的一个 grn 网络可视化。基因调控网络分析通常包含几个步骤，数据格式转换、计算网络统计量、可视化。grn 模块覆盖了这些环节，而且自带了完整的交互式网络浏览器。

GRN 的数据通常有散列：source、target、weight。`net2json` 把它们转成 JSON，浏览器直接加载：

```bash
jsrc grn net2json -i network.tsv -o json/grn.json
```

如果你只需要把注释 TSV 转成 JSON，不涉及网络转换，可以直接用这个：

```bash
jsrc grn anno2json -i annotation.tsv -o json/annotation.json
```

想知道哪些基因在调控网络中处于核心位置，最直接的方式就是算度（degree）。这个命令统计每个节点的入度、出度和总度，按总度排序输出：

```bash
jsrc grn centrality -i network.tsv --top 30
```

输出：

```
node        in_degree   out_degree  total_degree
GENE_0504   24.14       34.97       59.12
GENE_0785   26.37       29.51       55.88
...
```

入度高说明该基因被很多其他基因调控（"听命令的"），出度高说明该基因调控很多其他基因（"发号施令的"）。总度排名靠前的往往是转录因子或信号通路的关键节点。

网络和注释都转好之后，用 `build` 把 viewer 前端和 JSON 打包成一份可以直接部署的目录（也可以顺便压成 ZIP）：

```bash
jsrc grn build -d viewer -g json/grn.json -n json/annotation.json -z viewer.zip -a -t 200
```

展示模式有两种：

- `-a`（all 模式）：当网络中的基因数量小于等于阈值时，自动全量展示整张网络。适合几百个基因的小网络。
- `-e`（expand 模式）：初始只显示一个空画布，通过搜索基因名来展开其邻居。适合几千个基因的大网络，不会把浏览器卡死。

`-t` 控制 all 模式自动全量展示的阈值，`--max-nodes` 限制单次展示的节点上限（0 表示不限制）。可选的 `-n` 参数接受一个注释 JSON，包含基因 ID 和功能描述，这些信息会在 viewer 里显示在节点的详情面板中（最开始给杨树做的所以带上 Potri ID，后续会完善）。

不想打包，直接在本地起一个 HTTP 服务预览也行：

```bash
jsrc grn serve -d viewer -g json/grn.json -n json/annotation.json -p 8000 -e
```

![](/static/images/400214fe.webp)

这个 viewer 是基于 D3.js 的 Force Graph 实现的交互式页面，功能包括：

- 力导向布局，节点自动排斥、边自动吸引
- 点击节点展开其邻居，搜索框可以快速定位到指定基因
- 信息面板显示基因的注释信息
- 邻居列表按边权降序排列，支持下载为 TXT
- 图片 / PDF 导出
- 前进 / 后退导航历史

## 不足

最大的问题就是测试不全面，很多问题没有暴露出来，所以希望有更多人来用，我们一起找问题解决问题，如果有朋友有好的建议也可以找我，尽量方便更多人使用。
