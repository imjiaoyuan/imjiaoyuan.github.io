---
title: 超大基因组 SNP 检测流程
date: 2026-09-19
---

基因组一过 10 Gb，常规变异检测的默认设置就开始崩，麻烦的地方不在比对慢，而在几个 32 位的坐标上限。下面这批数据约 23 Gb、十二条染色体，每条接近 2 Gb，比人类大七倍。会崩的地方有这么几处：

- bwa 的索引有 4 Gb 上限，整个基因组建不了索引。
- .tbi 索引的坐标是 32 位，单条染色体超过 2,147,483,647 bp 就无法建索引，会直接报坐标溢出。
- BAM 和 VCF 的 32 位坐标限制同样影响 PLINK 的 .bim 文件。
- 单条染色体一次要读几十个 BAM，内存和中间文件都要按染色体切。
- 索引换成 CSI，它是另一种索引格式，用变长整数存坐标，没有 .tbi 那个 2 Gb 上限。

所以整套流程的设计原则只有一条，一切按染色体拆开，一切索引用 CSI。

## 参考基因组拆分

超大基因组上全基因组一起跑不现实，第一步就是把参考按染色体拆开：

```bash
samtools faidx ref/genome.fa chr1 > ref/chr1.fa
```

- `samtools faidx ref/genome.fa chr1`，按名称取出单条染色体。这里以 chr1 为例，其余染色体把名称换掉即可。
- 先要有 ref/genome.fa.fai，faidx 取子序列时靠它定位。没有就先生成一次。

每条染色体单独建索引，绕开 bwa 的 4 Gb 上限，

```bash
bwa index -p index/chr1 ref/chr1.fa
```

- `-p index/chr1`，索引前缀。每条染色体一个索引，同时让后面的比对可以按染色体并行。
- 拆分之后 read 只能落在被拆分的那条染色体上，跨染色体的错误比对反而更少，对变异检测是好事。

给单条染色体的 FASTA 再建一次 .fai，

```bash
samtools faidx ref/chr1.fa
```

- bcftools 和 bedtools 都需要它。
- 这是对子序列再建一次索引，与最上面那一次不是同一个文件，不要合并成一步。

## 按染色体比对

过滤也按染色体单独做，这里先给 chr1 过滤：

```bash
java -jar tools/Trimmomatic/trimmomatic-0.38.jar PE -threads 2 raw/sample01.R1.fastq.gz raw/sample01.R2.fastq.gz clean/R1.clean.fq.gz clean/R1.unpaired.fq.gz clean/R2.clean.fq.gz clean/R2.unpaired.fq.gz ILLUMINACLIP:tools/Trimmomatic/adapters/TruSeq3-PE.fa:2:30:10 SLIDINGWINDOW:4:15 MINLEN:36
```

- `PE`，双端模式。后面先接输入的两个 fastq，再依次接配对输出的 R1、未配对 R1、配对输出 R2、未配对 R2，一共六个文件。顺序写错会把未配对的 read 混进主文件。
- `-threads 2`，线程数。按染色体并行跑时每条命令给 2 到 4 个就够，给多了反而互相抢内存。
- `ILLUMINACLIP:...:2:30:10`，接头去除，四个数字依次是最大错配数、palindrome 模式下比对分数阈值、简单模式下比对分数阈值、最短可保留片段长度。
- `SLIDINGWINDOW:4:15`，四碱基滑窗，窗口平均质量低于 15 就从这里切掉。
- `MINLEN:36`，过滤后短于 36 bp 的 read 丢掉。

以 chr1 为例，比对和排序分开写，

```bash
bwa mem -t 8 -M -R '@RG\tID:sample01\tSM:sample01\tPL:ILLUMINA' index/chr1 clean/R1.clean.fq.gz clean/R2.clean.fq.gz -o aln/sample01.chr1.sam
```

- `-t 8`，比对线程数。
- `-M`，把较短的 split hit 标记为次要比对，兼容后续工具有关比对记录的解析。
- `-R`，read group。SM 就是样本名，必须唯一。每条染色体单独比对时，同一样本的 12 个 BAM 必须写同一个 SM，否则合并之后会被当成 12 个样本。
- 索引位置参数写 index/chr1，用的是单染色体索引，不是全基因组索引。
- `-o`，先落成 SAM。先存中间文件的好处是排序失败不用重新比对，代价是一个上百 G 的 SAM。

比对结果先排序，临时目录带染色体名，避免几条染色体抢同一个文件：

```bash
samtools sort -@ 2 -T tmp/sort_chr1 -o bam/sample01.chr1.bam aln/sample01.chr1.sam
```

- `-T tmp/sort_chr1`，临时文件前缀。多条染色体同时跑时不指定，会抢同一批临时文件而互相覆盖。
- `-@ 2`，排序线程数。

其余染色体照这个写法，把 `chr1` 和临时文件前缀一并换掉，

```bash
bwa mem -t 8 -M -R '@RG\tID:sample01\tSM:sample01\tPL:ILLUMINA' index/chr2 clean/R1.clean.fq.gz clean/R2.clean.fq.gz -o aln/sample01.chr2.sam
```

- `index/chr2`，换成这条染色体自己的索引；输出文件名也带上染色体名，某条跑坏了可以单独重跑。

chr2 走同一套流程，索引和输出文件名换成它自己的：

```bash
samtools sort -@ 2 -T tmp/sort_chr2 -o bam/sample01.chr2.bam aln/sample01.chr2.sam
```

- `-T tmp/sort_chr2`，临时文件前缀要与上面那条命令同一条染色体。
- 12 条染色体同时跑时，单个样本就占掉大量 CPU，按可用资源决定同时跑几条。

全部染色体比完再把 BAM 首尾相接，

```bash
samtools merge -@ 8 -f bam/sample01.merged.bam bam/sample01.chr1.bam bam/sample01.chr2.bam
```

- `merge -f`，`-f` 表示输出文件已存在时直接覆盖，12 条染色体时把文件名都列上。merge 不会重排，结果不是全局有序的。

合并之后再排一次，

```bash
samtools sort -@ 8 -o bam/sample01.sorted.bam bam/sample01.merged.bam
```

- 后面的 markdup、index 和变异检测都要求 BAM 全局有序。

## 排序与 CSI 索引

12 条染色体的 BAM 要先合成一个全局有序的，第一步去掉未比对的 read：

```bash
samtools view -b -F 4 -o bam/sample01.fix.bam bam/sample01.sorted.bam
```

- `-F 4`，过滤掉未比对的 read，减小 BAM 体积，也避免某些工具在处理未比对记录时出错。
- `-b`，输出 BAM。

去掉未比对记录之后再排一次序：

```bash
samtools sort -@ 8 -o bam/sample01.fix.sorted.bam bam/sample01.fix.bam
```

- 再排一次序是为了让多条染色体的合并结果严格按坐标有序。超大基因组上这一步往往省不掉。

换回原来的名字，后面所有命令都按这个名字找文件：

```bash
mv bam/sample01.fix.sorted.bam bam/sample01.sorted.bam
```

- 换回原来的名字，后面所有命令都用 bam/sample01.sorted.bam。重排后旧索引失效，必须重建。

重排之后旧索引失效，用 CSI 重建：

```bash
samtools index -c bam/sample01.sorted.bam
```

- `-c`，建立 CSI 索引。这个参数是整篇文档最容易漏的一个，用默认的 .tbi，bcftools 处理到超长染色体时会报区域无法存入索引，而且是在跑完几个小时之后才报。

顺手看一眼每条染色体的长度和比对上的 reads 数：

```bash
samtools idxstats bam/sample01.sorted.bam > qc/sample01.idxstats.txt
```

- 输出每条染色体的长度和比对上的 reads 数，用来快速确认索引可用、以及各条染色体是否都有覆盖。

确认索引可用，各条染色体都有覆盖：

```bash
head qc/sample01.idxstats.txt
```

- 先看前几行。染色体长度要与参考对得上，对不上说明这份 BAM 和现在的参考不是一套。

## 逐染色体检测

一次只处理一条染色体，十二条各跑一遍。有些样本只比对上头两条染色体，把它们塞进 BAM 列表会让 bcftools mpileup 直接中断，所以先按染色体过滤一遍列表。

先按染色体过滤一遍 BAM 列表，头部里带这条染色体名字的样本才留下，

```bash
for bam in bam/*.sorted.bam; do samtools view -H "$bam" -o qc/header.tmp; grep -q $'SN:chr1\t' qc/header.tmp && echo "$bam"; done > qc/bamlist.chr1.txt
```

- `samtools view -H`，只输出头部，用来查 BAM 里有哪些参考序列名。这里先把头部存成临时文件，再用 grep 查，以免在循环里套管道。
- `grep -q $'SN:chr1\t'`，头部的 SN 字段记录了每条参考序列的名字，反斜杠加 t 表示按制表符精确匹配，否则 chr1 会匹配上 chr10、chr11、chr12。

数一下过滤前后的 BAM 数，

```bash
wc -l qc/bamlist.chr1.txt bam/*.sorted.bam
```

- 两个数差距大，说明有样本根本没比对上这条染色体。后面的 mpileup 带着它们跑也不会报错，但结果只覆盖了一部分样本。

pileup 生成原始记录，

```bash
bcftools mpileup -f ref/chr1.fa -b qc/bamlist.chr1.txt -r chr1 --threads 6 -a AD,DP -O z -o vcf/raw_chr1.pileup.vcf.gz
```

- `-f ref/chr1.fa`，单染色体的参考，不要传全基因组，按染色体跑就是靠这一点压住内存。
- `-b qc/bamlist.chr1.txt`，上一步过滤出来的 BAM 列表。
- `-r chr1`，限定染色体或区间，这是控制内存的主要手段。
- `-a AD,DP`，输出等位基因深度和总深度，不能省。超大基因组里重复序列多，某个位点是不是真的变异只能靠等位基因深度比判断，先不记下来后面补不回来。
- `-O z`，输出压缩的 VCF。

再判基因型，

```bash
bcftools call -m -v --threads 2 -O z -o vcf/raw_chr1.vcf.gz vcf/raw_chr1.pileup.vcf.gz
```

- `call -m -v`，多等位模型，只输出变异位点。
- mpileup 和 call 分两步写，中间文件大一些，换来的是每一步都能单独重跑。

最后建索引，

```bash
bcftools index -c vcf/raw_chr1.vcf.gz
```

- `-c`，CSI 索引。单条染色体接近 2 Gb，用 .tbi 到不了头。

## 合并与过滤

各条染色体的 VCF 里样本集不完全相同，所以要用 merge，缺的样例会补成缺失基因型，concat 在这里不能用。VCF 和 BAM 用的是 BGZF 分块压缩，文件被截断时大小看起来正常，只有读到末尾才会报错，所以下面要多做一步完整性检查。

先把各条染色体的索引补上并覆盖旧的，

```bash
bcftools index -c -f vcf/raw_chr1.vcf.gz
```

- `index -c -f`，重建 CSI 索引，`-f` 表示覆盖已有索引。12 条染色体各建一次，这里只列 chr1。

合并的时候样本集不一致就按位置对齐，

```bash
bcftools merge --force-samples vcf/raw_chr1.vcf.gz vcf/raw_chr2.vcf.gz -O z -o vcf/raw_all.vcf.gz --threads 8
```

- `--force-samples`，样本集不一致时按位置合并，缺的样例补成缺失基因型。不加这个参数，样本集不同会直接报错。
- 12 条染色体把文件名都列上，或者用 `vcf/raw_chr{1,2,...,12}.vcf.gz` 展开。

12 条染色体的 VCF 合并成一个之后建 CSI 索引：

```bash
bcftools index -c vcf/raw_all.vcf.gz
```

- 合并后的文件同样要建 CSI 索引，后面的 filter 和查询都靠它。

两类变异分开过滤，先过 SNP，

```bash
bcftools filter -i 'TYPE="snp" && QUAL>=20 && F_MISSING<0.5' -O z -o vcf/snps_filtered.vcf.gz vcf/raw_all.vcf.gz --threads 8
```

- `-i`，保留满足条件的记录。
- `QUAL>=20`，位点质量下限。
- `F_MISSING<0.5`，缺失率低于 50%。这一层很宽松，只是去掉明显坏的位点。
- 这一层的输出是中间产物，几百 G，确认下游没问题之后再删。

再过 InDel，

```bash
bcftools filter -i 'TYPE="indel" && QUAL>=20 && F_MISSING<0.5' -O z -o vcf/indels_filtered.vcf.gz vcf/raw_all.vcf.gz --threads 8
```

- 同一套条件对 InDel 再跑一遍，两类分开存，后面的过滤条件不一样。

文件被截断时 BGZF 不会在大小上露出破绢，所以最后要查一下压缩块的结尾。先取出末尾字节，

```bash
tail -c 28 vcf/snps_filtered.vcf.gz > qc/snps.eof.bin
```

- `tail -c 28`，取文件最后 28 字节。BGZF 文件末尾必须有 28 字节的 EOF 块，开头就是这几个字节。

先取文件末尾 28 字节转成十六进制，看 BGZF 的结束块在不在：

```bash
xxd qc/snps.eof.bin > qc/snps.eof.hex
```

- 转成十六进制，直接看字节内容。

匹配到结束块的魔数就说明文件是完整的：

```bash
grep -q '1f 8b 08 04' qc/snps.eof.hex
```

- `grep -q`，只判断能不能匹配上，不打印。返回非零就说明文件被截断了。
- 截断的 VCF 大小看起来正常，也能用 zcat 读开头，只有走到末尾才报错，所以这个检查在大文件项目里要例行做。

再数一遍位点数，和预期对得上才算没截断：

```bash
bcftools index -n vcf/snps_filtered.vcf.gz
```

- `-n`，输出位点数。超大基因组上这个数字通常是几亿。

## 核心 SNP 集筛选

超大基因组的问题在于位点太多，而且大量是假的。二十多 Gb 的重复序列加上低深度，随手一检测就是几亿个位点。下面这一步用统计条件把低深度的虚假变异筛掉，把位点数砍掉一个数量级，留下来的就是核心 SNP 集，也就是拿去做下游分析的那批位点。

```bash
bcftools norm -f ref/genome.fa -d exact -Oz -o qc/00.norm.vcf.gz vcf/snps_filtered.vcf.gz
```

- `-f ref/genome.fa`，参考序列，norm 用它做左对齐。
- `-d exact`，去掉完全重复的位点，也就是坐标和等位基因都一样的记录。
- 左对齐是为了让同一位点在所有样本里写法一致。写法不一致时，后面按位置取交集会把同一个位点错开。

正式过滤之前先把双等位 SNP 挑出来，后面只处理这一类：

```bash
bcftools view -v snps -m2 -M2 -f PASS,. -Oz -o qc/01.biallelic.snp.vcf.gz qc/00.norm.vcf.gz
```

- `-v snps -m2 -M2`，只保留双等位 SNP。
- `-f PASS,.`，保留标记为 PASS 和没有过滤标记的位点。

建 CSI 索引，几亿个位点已经超出 .tbi 的能力：

```bash
bcftools index -c qc/01.biallelic.snp.vcf.gz
```

- `index -c`，建 CSI 索引。几亿个位点的 VCF 已经超出 .tbi 能力，全部索引用 CSI。

给每个基因型补上等位基因频率，下一步按它打码：

```bash
bcftools +fill-tags qc/01.biallelic.snp.vcf.gz -Oz -o qc/02.with_vaf.vcf.gz -- -t FORMAT/VAF
```

- `+fill-tags -t FORMAT/VAF`，给每个基因型加上等位基因频率。
- 没有 VAF 就没办法按等位基因平衡判断杂合是否可信，这一步是下一步的前提。

低深度和等位比例明显偏离的杂合基因型在这里打成缺失：

```bash
bcftools +setGT qc/02.with_vaf.vcf.gz -Oz -o qc/03.gt_masked.vcf.gz -- -t q -n . -i 'FMT/DP<3 | (GT="het" & (FMT/VAF<0.20 | FMT/VAF>0.80))'
```

- `-t q`，把基因型改成别的值，具体改成什么由 `-n` 指定。
- `-n .`，改成缺失。打码而不是删位点，位点还留在 VCF 里，只是这些样本在该位点上没有基因型。
- `-i`，按条件挑基因型。低深度（DP<3）和等位基因比例明显偏离 0.5 的杂合基因型都在这里打掉。
- 表达式里只能用 & 和 |，绝不能用 && 或 ||。用后者，bcftools 会把它当成记录级的布尔运算，条件恒真或恒假，几乎所有基因型会被一起打码。症状是筛完只剩几百个位点，而且不报错。

打码之后再建索引，下一步要按区间访问：

```bash
bcftools index -c qc/03.gt_masked.vcf.gz
```

- 建 CSI 索引，后面的查询和切分都靠它。

加一个抽样自检确认打码比例合理，先把基因型导出来，

```bash
bcftools query -f '[%GT\t]\n' qc/03.gt_masked.vcf.gz > qc/gt.all.txt
```

- `-f '[%GT\t]\n'`，只输出基因型，中括号表示逐样本展开。

抽样一千行，先看基因型有没有被打坏：

```bash
head -1000 qc/gt.all.txt > qc/gt.head1000.txt
```

- `head -1000`，先取一千行做抽样。全文件的基因型太多，抽样足够看出比例。

数一下缺失基因型的比例，条件写错时会接近 1：

```bash
awk '{n=0; m=0; for(i=1;i<=NF;i++){n++; if($i=="./.")m++} print m/n}' qc/gt.head1000.txt
```

- 数每行的样本数和缺失基因型数，输出缺失比例。
- 这个比例应该远低于 1。接近 1 就说明上一步的条件写错了，回去检查是不是用了双与号。

位点深度分布用来看深度上限该定在哪：

```bash
vcftools --gzvcf qc/03.gt_masked.vcf.gz --remove qc/remove_samples.txt --site-mean-depth --out qc/site_depth
```

- `--gzvcf`，直接读压缩的 VCF，不要先解压。
- `--remove qc/remove_samples.txt`，剔除高缺失率的样本。这一步必须放在算缺失率阈值之前，一批高缺失样本会把大量本来合格的位点抬到阈值以上。
- `--site-mean-depth`，输出每个位点的平均深度，用它定深度上限。
- `--out qc/site_depth`，输出前缀。

只取平均深度那一列：

```bash
awk '{print $3}' qc/site_depth.ldepth.mean > qc/site_depth.col3.txt
```

- `$3`，平均深度列，前两列是染色体和位置。

按数值排序，字典序会把 100 排到 20 前面：

```bash
sort -g qc/site_depth.col3.txt > qc/site_depth.sorted.txt
```

- `sort -g`，按数值大小排序，默认的字典序会把 100 排到 20 前面。

取第 99 百分位作为深度上限，用来剔除塌缩重复区：

```bash
awk '{a[NR]=$1} END{print a[int(NR*0.99)]}' qc/site_depth.sorted.txt > qc/maxdp.txt
```

- 取第 99 百分位作为深度上限，用于剔除塌缩重复区，也就是组装把多个重复拷贝合并成一段、深度异常高、变异几乎全是假的那种区段。
- 上限不要写死成固定值。不同测序深度的项目最优上限差很多，用分位数自动适应数据。

带上深度上限和位点级条件跑一遍，得到核心位点集：

```bash
vcftools --gzvcf qc/03.gt_masked.vcf.gz --remove qc/remove_samples.txt --minQ 30 --max-missing 0.80 --mac 3 --min-alleles 2 --max-alleles 2 --max-meanDP $(cat qc/maxdp.txt) --recode --recode-INFO-all --out qc/04.core
```

- `--minQ 30`，位点质量下限。
- `--max-missing 0.80`，缺失率不高于 20%，这是砍位点最多的条件之一。
- `--mac 3`，次等位基因计数（MAC）至少为 3。MAC 是某个位点上次等位基因在所有样本里出现的次数，只在一两个个体里出现的位点几乎都是测序错误。
- `--min-alleles 2 --max-alleles 2`，再次限定双等位。
- `--max-meanDP $(cat qc/maxdp.txt)`，上一步算出的深度上限，用命令替换直接读进来，不用手抄。
- `--recode --recode-INFO-all`，输出 VCF 并保留 INFO 字段。
- 样本剔除名单在这里和上一层的过滤一起生效。每个样本的缺失率、平均深度、杂合度要在最终核心集上重算一遍，用于确认剔除名单是否合理。

在核心集上重算个体缺失率，确认剔除名单合不合理：

```bash
vcftools --gzvcf qc/04.core.recode.vcf --missing-indv --out qc/final_missing
```

- vcftools 一次只能算一个指标，三个指标要跑三遍，每次在几十 G 的文件上都是一小时起，排在流程最后。
- `--missing-indv` 看个体缺失率。

再看个体平均深度：

```bash
vcftools --gzvcf qc/04.core.recode.vcf --depth --out qc/final_depth
```

- `--depth` 看个体平均深度。

再看个体杂合度，三个指标同时异常的样本要剔除：

```bash
vcftools --gzvcf qc/04.core.recode.vcf --het --out qc/final_het
```

- `--het` 看个体杂合度。三个指标同时异常的样本直接剔除。

压缩之后才能按区间访问：

```bash
bgzip qc/04.core.recode.vcf
```

- 压缩后的文件才能给 bcftools 按区间访问。

建 CSI 索引：

```bash
bcftools index -c qc/04.core.recode.vcf.gz
```

- 建 CSI 索引，不用 .tbi，单条染色体的坐标超出它的范围。

## 按染色体分开跑与合并

每条染色体都走三步，P1 给基因型打码，P2 做宽松过滤并算个体层面的指标，P3 出核心集，三步都在单条染色体的切片上做。下面从 chr1 开始，换染色体时把命令里的 `chr1` 全替掉即可，

```bash
mkdir -p qc/perchr
```

切片、打码一步走完，

```bash
bcftools view -r chr1 qc/02.with_vaf.vcf.gz -Ou --threads 2 | bcftools +setGT - -Oz -o qc/perchr/03.gt_masked.chr1.vcf.gz -- -t q -n . -i 'FMT/DP<3 | (GT="het" & (FMT/VAF<0.20 | FMT/VAF>0.80))'
```

- `bcftools view -r chr1`，先把这条染色体的记录抽出来再打码。先在切片上做，是因为在几十 G 的全量 VCF 上跑 setGT 到不了头。
- `-Ou` 接管道，中间是未压缩 BCF，不落盘，省一次读写。
- 输出文件名里带染色体名，12 条各一个文件，某条跑坏了可以单独重跑。
- 每条命令给 2 到 4 个线程，内存按 3 G 给就够；速度靠 12 条分开跑，不靠单条命令的线程数。

逐染色体的中间文件也建索引，下一步按区间筛要用：

```bash
bcftools index -c qc/perchr/03.gt_masked.chr1.vcf.gz
```

打完之后必须确认真的是打码而不是把整个文件打成缺失。先看这条染色体还有没有记录，

```bash
[ "$(bcftools index -n qc/perchr/03.gt_masked.chr1.vcf.gz)" -gt 0 ] || { echo "ERROR: chr1 无记录"; exit 1; }
```

- `index -n` 为 0 说明这条染色体一条记录都没输出，也要当成失败。

再抽两万行估平均缺失率，这三句要连着写，不能拆开，

```bash
set +o pipefail
bcftools view -H qc/perchr/03.gt_masked.chr1.vcf.gz | head -20000 | awk -F'\t' '{n=0;g=0;for(i=10;i<=NF;i++){split($i,a,":");n++;if(a[1]!="./.")g++} s+=1-g/n; k++} END{f=s/k; printf "chr1 平均 F_MISSING=%.4f\n", f; if (f>0.90) {print "ERROR: 打码逻辑异常" > "/dev/stderr"; exit 1}}'
set -o pipefail
```

- `set +o pipefail` 再 `set -o pipefail`，`head -20000` 读够了就关管道，bcftools 会收到 SIGPIPE 并以非零退出。在 `set -e` 加 `pipefail` 的脚本里，这个非零退出会把整个脚本带崩。这块要临时关掉 pipefail，抄脚本时容易漏。
- `split($i,a,":")` 与 `a[1]`，从第 10 列开始，每列是 `GT:其他字段` 的格式，先拆冒号再取基因型字段。直接比较整列会把有别的 FORMAT 字段的记录算错。
- `head -20000`，抽两万行估平均缺失率。全量基因型矩阵太大，抽样足够看出量级。
- `f>0.90` 直接 `exit 1`，打码条件写错（比如把单竖线写成双竖线）时平均缺失率会接近 1，这一步让作业当场失败，不会把废文件传下去。

P2 在这一条的切片上做宽松过滤，同时算个体层面的三个指标，

先把这一条切片按位点级条件宽松过滤一遍，

```bash
bcftools view -i 'F_MISSING<=0.50 && MAC>=2' qc/perchr/03.gt_masked.chr1.vcf.gz -Oz -o qc/perchr/04.preQC.chr1.vcf.gz --threads 4
```

- `F_MISSING<=0.50 && MAC>=2`，这是位点级条件，与前面 `-i` 里逐基因型的 setGT 表达式不是一回事。两条都用单竖线双与号，写错了不会报错，只会把位点数算错一个数量级。

位点级筛选做完，同样建索引：

```bash
bcftools index -c qc/perchr/04.preQC.chr1.vcf.gz
```

个体指标按染色体分开算，先建目录：

```bash
mkdir -p qc/indiv
```

再算个体层面的三个指标，

```bash
vcftools --gzvcf qc/perchr/04.preQC.chr1.vcf.gz --missing-indv --out qc/indiv/chr1_missing 2>/dev/null
```

- `--missing-indv`，每个样本的缺失位点比例。

逐染色体算个体平均深度：

```bash
vcftools --gzvcf qc/perchr/04.preQC.chr1.vcf.gz --depth --out qc/indiv/chr1_depth 2>/dev/null
```

- `--depth`，每个样本的平均深度。

逐染色体算个体杂合度：

```bash
vcftools --gzvcf qc/perchr/04.preQC.chr1.vcf.gz --het --out qc/indiv/chr1_het 2>/dev/null
```

- `--het`，每个样本的杂合度统计量。
- 三条 vcftools 命令一次只能算一个指标，在单条染色体的切片上跑还算快；换到全量 VCF 上跑就是每个指标一小时起。
- 分染色体算出来的三张表最后要加权合并，缺失率按位点数相加，平均深度按位点数加权，杂合度要把 O(HOM)、E(HOM)、N_SITES 分别相加再算 F。不能把 12 条染色体的数值直接取平均。

P3 逐染色体出核心集，直接管道到底，

```bash
vcftools --gzvcf qc/perchr/03.gt_masked.chr1.vcf.gz --remove qc/remove_samples.txt --minQ 30 --max-missing 0.80 --mac 3 --min-alleles 2 --max-alleles 2 --max-meanDP $(cat qc/maxdp.txt) --recode --recode-INFO-all --stdout 2>/dev/null | bgzip -c > qc/perchr/05.core.chr1.vcf.gz
```

- `--stdout | bgzip -c`，vcftools 的 recode 写到标准输出，bgzip 直接压。写法与 `--out` 不同，用 `--out` 会先落一个几十 G 的未压缩 VCF。
- 深度上限 `maxdp.txt` 不分染色体重算，它是基于 DP 字段算出来的，与基因型是否打码无关，全基因组一份就够。命令里用 `$(cat qc/maxdp.txt)` 直接读进来，不用手抄。
- `--remove` 的剔除名单所有染色体共用一份。名单里的样本被剔掉后，每条染色体的输出都剩同样一批样本，这是下一步能用 concat 的前提。

筛完核心位点的染色体文件建索引：

```bash
bcftools index -c qc/perchr/05.core.chr1.vcf.gz
```

合并之前先验样本数，对不上说明某条染色体没跑完，

```bash
bcftools query -l qc/perchr/05.core.chr1.vcf.gz | wc -l
```

- `query -l` 列出样本名，`wc -l` 数个数。剔了样本之后每条染色体应该都剩同样多个，对不上就是哪一条没跑完，或者用的还是旧的剔除名单。

再把 12 条都过一遍，

```bash
for f in qc/perchr/05.core.chr*.vcf.gz; do echo "$f 位点=$(bcftools index -n $f) 样本=$(bcftools query -l $f | wc -l)"; done
```

- 每条染色体的样本集一致，`bcftools concat` 就能用，比 `merge` 快得多。样本集不一致时才必须回到 merge，那一步会把缺的样本补成一堆缺失基因型，位点数一多就慢得没法接受。

各条染色体样本集一致，直接按顺序拼接，比 merge 快得多：

```bash
bcftools concat qc/perchr/05.core.chr{1,2,3,4,5,6,7,8,9,10,11,12}.vcf.gz -Oz -o qc/05.core.snp.vcf.gz --threads 8
```

- `chr{1,2,...,12}` 展开成 12 个文件名，写在一行里，顺序就是染色体顺序。
- concat 只按顺序拼，不检查样本集，所以上一步的样本数检查不能省。

全基因组核心集建 CSI 索引：

```bash
bcftools index -c qc/05.core.snp.vcf.gz
```

合并完在最终核心集上再算一遍个体指标，并汇总各染色体的小表，

```bash
vcftools --gzvcf qc/05.core.snp.vcf.gz --missing-indv --out qc/sample_missing 2>/dev/null
```

- `--missing-indv`，全基因组范围内的个体缺失率。

在全基因组核心集上再算一遍个体深度：

```bash
vcftools --gzvcf qc/05.core.snp.vcf.gz --depth --out qc/sample_depth 2>/dev/null
```

- `--depth`，个体平均深度。

以及个体杂合度：

```bash
vcftools --gzvcf qc/05.core.snp.vcf.gz --het --out qc/sample_het 2>/dev/null
```

- `--het`，个体杂合度。

把逐染色体的个体缺失率汇总起来，作为剔除样本的依据：

```bash
awk 'FNR>1{d[$1]+=$2; m[$1]+=$4} END{for(s in d) printf "%s\t%d\t%.6f\n", s, d[s], (d[s]>0? m[s]/d[s] : 0)}' qc/indiv/*_missing.imiss | sort > qc/sample_missing.imiss
```

- `FNR>1` 跳过每个文件的行首，其余按样本把各染色体的小表相加。
- 缺失率是可加项，各染色体的 `N_DATA` 与 `N_MISSING` 相加再除，得到全基因组的缺失率。直接对 12 个比例取平均会在染色体的位点数相差悬殊时算错。
- 平均深度要按位点数加权，把每行的均值深度乘以位点数再相加，最后除以总位点数；杂合度先把 `O(HOM)`、`E(HOM)`、`N_SITES` 分别相加，最后再算 `(O-E)/(N-E)`。这三个数不能先算每条染色体的值再平均。
- 这一步的输出就是决定哪些样本剔除的根据，缺失率、平均深度、杂合度三项同时异常的样本直接进 `remove_samples.txt`，再重跑一遍 P3 之后的核心集。

整条链的顺序是：12 条染色体各自走过 P1、P2、P3，然后合并，再汇总个体的三个指标。每条染色体之间没有依赖，可以随便挑一个顺序跑，合并和汇总要等 12 条都结束。

## 运行策略

- 中间文件按染色体分开写，不要试图一次合并出全量 VCF 再过滤。
- 每一步的输出都建 CSI 索引，整个项目里不出现 .tbi 文件。
- 启动前确认磁盘空间，质控输出可能上百 G。磁盘满造成的截断 VCF 很隐蔽，只有末尾的 EOF 标记检查能发现。
- 转成 PLINK 格式之后必须检查 .bim 的坐标列有没有出现负值，32 位整数会在单条染色体超过 2 Gb 时溢出。
