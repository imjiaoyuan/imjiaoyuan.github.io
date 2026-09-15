---
title: WGS 变异检测流程
date: 2026-09-18
---

这是重测序做变异检测的常规路线，用 GATK 走 GVCF 联合分型，从原始 fastq 一直做到过滤后的 SNP，适合有参考基因组、样本量中等、需要个体级基因型的情况。基因组特别大时默认设置会直接崩，那种情况要换索引格式并按染色体拆开跑；如果做的是简化基因组或者低深度、样本上千，用 bcftools 直接检测更省事，放在最后一节。

重测序与从头组装的区别在于有一个可信的参考基因组，样本的 reads 比回去之后，差异就是变异。流程本身不长，质控、比对、去重、变异检测、过滤，但每一步都在防一类假阳性，接头污染造成假 SNP，比对错位造成假 InDel，PCR 重复造成等位基因频率虚高，样本信息缺失造成合并时错配。

## 测序质控

接头和低质量碱基在比对时会变成看起来像 SNP 的东西。接头序列如果恰好与参考的某段同源，会在样本间一致地出现，过滤时很难和真变异区分。

如果同一个样本分多次测序，拿到的会是好几个 fastq 文件。先按样本合并，把同方向的文件按文件名顺序拼成一个，脚本如下：

```python
#!/usr/bin/env python3
"""把每个样本目录下的多次测序文件按 R1/R2 合并。用法: python merge_fq.py 00.data/01.Hip_reseq"""
import gzip
import shutil
import sys
from pathlib import Path


def direction(name):
    """从文件名里取 R1/R2, 取不到返回 None"""
    for token in reversed(name.replace("_", ".").split(".")):
        if token in ("R1", "1"):
            return "R1"
        if token in ("R2", "2"):
            return "R2"
    return None


def merge(files, out):
    with gzip.open(out, "wb") as w:
        for f in files:
            with gzip.open(f, "rb") as r:
                shutil.copyfileobj(r, w)


def main(root):
    for sample in sorted(p for p in Path(root).iterdir() if p.is_dir()):
        files = sorted(f for f in sample.glob("*.f*q.gz") if not f.name.startswith("merged"))
        r1 = [f for f in files if direction(f.name) == "R1"]
        r2 = [f for f in files if direction(f.name) == "R2"]
        if not r1 or len(r1) != len(r2):
            sys.exit(f"{sample.name}: R1 {len(r1)} 个, R2 {len(r2)} 个, 数量不等, 先查文件")
        merge(r1, sample / "merged_R1.fq.gz")
        merge(r2, sample / "merged_R2.fq.gz")
        print(f"{sample.name}: 合并 {len(r1)} 对")


if __name__ == "__main__":
    main(sys.argv[1])
```

用法是把它指到数据目录：

```bash
python merge_fq.py 00.data/01.Hip_reseq
```

- 数据按样本分成子目录，每个目录里放的是该样本的全部测序文件。脚本遍历每个样本目录，把里面的 R1 按顺序拼成一个 `merged_R1.fq.gz`，R2 同样拼成 `merged_R2.fq.gz`。
- 位置参数就是上一层的数据目录，不是单个文件。
- 不合并也能跑，但同一样本会被拆成几套输出，read group 里得用不同的 ID，去重也只能在单个文件内部做，跨文件的 PCR 重复会全部留下。
- 拼接时同一个样本的几个文件必须保持 R1、R2 顺序一致。顺序错了会在下游表现为大量不配对的 read，而不是报错。

合并完先看原始数据的质量，这一步不做过滤，留一份基线：

```bash
fastqc -o qc -t 4 sample01.R1.fq.gz sample01.R2.fq.gz
```

- 位置参数是原始 FASTQ。
- `-o qc`，报告输出目录。
- `-t 4`，线程数。fastqc 本身很快，给多了也省不了多少时间。
- 这一步只看原始数据，不做过滤，先留下一份基线，后面好与过滤后对比。

基线有了再动数据，接头和低质量碱基在这一步去掉：

```bash
fastp -i sample01.R1.fq.gz -I sample01.R2.fq.gz -o clean/sample01.R1.fq.gz -O clean/sample01.R2.fq.gz -q 15 -u 40 -l 36 -w 8 -j qc/sample01.fastp.json -h qc/sample01.fastp.html
```

- `-i -I -o -O`，输入输出的 R1 和 R2。
- `-q 15`，碱基质量阈值，低于这个值的碱基算低质量。
- `-u 40`，一条 read 里允许 40% 的低质量碱基仍然保留。这个值不要压太狠，压狠了会丢掉 read 末端本来可用的碱基，覆盖度下降反而更伤变异检测。
- `-l 36`，过滤后短于 36 bp 的 read 丢掉。短读在比对时更容易贴到错误位置。
- `-w 8`，fastp 的线程数。
- `-j` 与 `-h`，分别输出 json 和 html 报告，json 便于批量提取指标。

两份报告汇总成一份，样本多了翻起来方便：

```bash
multiqc -o qc qc
```

- `-o qc`，报告写到 qc 目录。
- 最后一个位置参数是要扫描的目录，fastqc 和 fastp 的报告都放在里面，一份报告能同时看到过滤前后。
- 重点看接头含量、每碱基质量和 GC 分布。某个样本的 GC 曲线整体偏移，后面它的变异数和杂合度都会异常。

## 建参考基因组索引

三个索引各管一段，缺一个后面都会报错。先建比对用的索引，

```bash
bwa index ref/genome.fa
```

- `ref/genome.fa`，参考序列，位置参数。
- 生成 .amb、.ann、.bwt 等文件。基因组超过 4 Gb 时 bwa 无法建索引，需要按染色体拆分，见大基因组那一篇。

再建区间索引，

```bash
samtools faidx ref/genome.fa
```

- 生成 .fai，用于按区间取序列、算染色体长度。工具链里几乎所有按区间操作的程序都依赖它。

最后是 GATK 自己的序列字典，

```bash
gatk CreateSequenceDictionary -R ref/genome.fa -O ref/genome.dict
```

- `-R` 参考序列，`-O` 输出的 .dict 路径。
- GATK 只认 .dict，不认 .fai，两个都要有。

## 比对

每一条比对记录都要带上它属于哪个文库、哪个样本，这些信息写在 read group 里，GATK 靠它区分样本和文库。

```bash
bwa mem ref/genome.fa clean/sample01.R1.fq.gz clean/sample01.R2.fq.gz -t 16 -M -R '@RG\tID:sample01\tSM:sample01\tLB:sample01.lib1\tPL:ILLUMINA' -o aln/sample01.sam
```

- 前三个位置参数依次是参考、R1、R2。
- `-t 16`，比对线程数。
- `-R`，read group。ID 是这条比对记录所属的文库名，SM 是样本名，LB 是文库名，PL 是测序平台。
- `-M`，把较短的 split hit 标记为次要比对。GATK 默认会忽略这些标记不一致的记录，不加这个参数，标记体系与 GATK 的预期不一致，局部组装时可能把本来该用的 reads 排掉。
- `SM` 必须写，而且每个样本不同。GATK 靠 SM 判断哪些 BAM 属于同一个样本，写错或漏写，多个样本会被当成一个个体的多个文库，联合分型时被静默合并成一套基因型。
- `LB` 用于去重分组。同一样本的不同文库应当共用 SM 但用不同的 LB。
- `-o aln/sample01.sam`，比对结果先落成 SAM。磁盘够就分两步写，排序失败不用重新比对；磁盘紧就直接接一条管道到 sambamba sort，少一个上百 G 的中间文件。

磁盘不够时把比对和转 BAM 串成一条管道，再一步步排序、去重、建索引。这种写法在循环里用很顺手，

```bash
bwa mem -t 8 -M -R '@RG\tID:sample01\tSM:sample01\tLB:sample01.lib1\tPL:ILLUMINA\tPU:unit1' ref/genome.fa clean/sample01.R1.fq.gz clean/sample01.R2.fq.gz | samtools view -bS -h -o bam/sample01.bam -
```

- `-t 8`，比对线程数，管道里 samtools 也在占核，别把核数全占满。
- `-M`，把较短的 split hit 标记为次要比对，与 GATK 的标记体系对齐。
- `-R`，read group。ID 是这条比对记录所属的文库名，SM 是样本名，LB 是文库名，PL 是测序平台，`PU` 是 flowcell 与 lane 的信息，单样本内部区分测序批次用，写不写不影响分型，查污染时有用。
- `samtools view -bS -h -o bam/sample01.bam -`，把 SAM 转成 BAM，末尾的 `-` 表示从标准输入读，省下每个样本一个 SAM 的磁盘。

接着排序，

```bash
sambamba sort -t 16 -o bam/sample01.sorted.bam bam/sample01.bam
```

- `-t 16`，排序线程数。排序在临时目录里产生好几倍于 BAM 大小的中间文件，自己指定临时目录并把临时目录放在大磁盘上。
- `-o`，排序后的 BAM。按坐标排序后才能在文件中按位置查找，下游工具都要求有序。

再去重，

```bash
gatk MarkDuplicates -I bam/sample01.sorted.bam -O bam/sample01.markdup.bam -M qc/sample01.markdup_metrics.txt
```

- `-I` 与 `-O`，输入输出 BAM。
- `-M`，度量文件，里面有 duplicate 比例，超过 30% 就先停下来查建库。

最后建索引，

```bash
sambamba index -t 16 bam/sample01.markdup.bam
```

- `sambamba index` 建 .bai，下游按坐标取区间的工具都依赖它。

中间文件可以删了，

```bash
rm bam/sample01.bam bam/sample01.sorted.bam
```
- `rm` 删掉排序前后的中间 BAM，不删的话一个项目下来几百 G，磁盘满造成的截断文件很难排查。
- 这几条命令放在一起就是单样本的完整写法，换成循环时把 `sample01` 换成变量即可。样本名从 `sample.list` 逐行读、命令拼好重定向到 `*.sh`、检查一遍再批量跑，样本多时比手写可靠。

如果走的是先落 SAM 那条路线，排序就从 SAM 开始：

```bash
sambamba sort -t 16 -o bam/sample01.sorted.bam aln/sample01.sam
```

- `-t 16`，排序线程数。
- `-o`，输出 BAM。按坐标排序后才能在文件中按位置查找，下游工具都要求有序。
- 用 sambamba 而不是 samtools sort，大 BAM 上快不少，内存占用也更稳。

三代长读长数据用 minimap2，流程到比对这一步才开始分叉，

```bash
minimap2 -ax map-hifi -t 10 ref.mmi hifi_sample01.fasta.gz > aln/hifi_sample01.sam
```

- `-a`，输出 SAM。不加这个参数默认输出 PAF，GATK 读不了。
- `-x map-hifi`，按 PacBio HiFi 的错读模式设参数。长读长数据细分技术平台，设错会直接影响比对率和错误率。
- `-t 10`，线程数。
- `ref.mmi`，预构建的索引文件，用 `minimap2 -d ref.mmi ref/genome.fa` 生成。基因组大的话建一次就够，不要每次比对重新建。
- 后面的排序、去重、变异检测与短读长一致，只是长读长对结构变异和大的 InDel 强得多。

## PCR 重复标记

重复是同一条原始 DNA 片段经过 PCR 扩增出来的多个拷贝，它们支持同一个等位基因，会人为放大该等位基因的频率。

```bash
gatk MarkDuplicates -I bam/sample01.sorted.bam -O bam/sample01.markdup.bam -M qc/sample01.markdup_metrics.txt
```

- `-I` 与 `-O`，输入输出 BAM。去重只是给重复 reads 打标记，并不删除，这样后面还能统计重复比例。
- `-M`，输出度量文件，里面有 duplicate 比例。这个比例超过 30% 就先停下来查建库，而不是硬着头皮往下做。
- 去重必须在变异检测之前做。重复 reads 会让杂合位点的等位基因比例偏离一半，严重时把杂合位点判成纯合。

去重之后立刻建索引，后面按区间取 BAM 都靠它：

```bash
sambamba index -t 16 bam/sample01.markdup.bam
```

- `sambamba index`，建 .bai 索引，基因组单条染色体超过 2 Gb 时要用 CSI 索引。

## 变异检测与 GVCF

单个样本先写成 GVCF。GVCF 是一种特殊的 VCF，不只记录哪里变了，还记录哪里确定没变；样本齐了之后把所有的 GVCF 放在一起，重新判断每个位点在每个样本上的基因型，这叫联合分型，比单样本各跑一遍更准，尤其是低覆盖样本。

```bash
gatk --java-options -Xmx30G HaplotypeCaller -I bam/sample01.markdup.bam -R ref/genome.fa -O gvcf/sample01.g.vcf.gz --emit-ref-confidence GVCF --native-pair-hmm-threads 8
```

- `--java-options -Xmx30G`，给 JVM 设堆内存上限。这一步要同时读入参考和 BAM，内存不够会直接抛异常，而不是变慢。
- `--emit-ref-confidence GVCF`，输出 GVCF 而不是普通 VCF。不加这个参数就退化成单样本直接分型，失去联合分型的意义。
- `--native-pair-hmm-threads 8`，局部组装和配对 HMM 的线程数。HaplotypeCaller 会先做局部从头组装再判断变异，这个参数控制组装部分的并行度。
- `-ploidy`，倍性，默认 2。多倍体或单倍体样本必须显式指定。
- 每个样本一条命令，按样本逐个跑。

基因组大、或者参考还不是染色体级别的时候，一个样本按区间分成多个 GVCF，`-L` 限定这一段，

```bash
gatk --java-options -Xmx30G HaplotypeCaller -R ref/genome.fa -I bam/sample01.markdup.bam -O gvcf/sample01.h2tg000025l.g.vcf.gz -L h2tg000025l --emit-ref-confidence GVCF
```

- `-L h2tg000025l`，只跑这条序列。分段之后每条命令的处理量小，内存峰值低，出错也只需要重跑这一段。
- 输出文件名里带上区间名，合之前一眼能看出哪个文件是哪个区间的。
- 参考是 scaffold 级别时，scaffold 名字就是从 contig 列表里取的那个名字，`contig.list` 一行一个，拆开时按它循环。

把同一区间的多个 GVCF 先合成一个，再进数据库，

```bash
gatk MergeVcfs $(for i in `cat contig.list | cut -f 1`; do echo "-I gvcf/${i}.g.vcf.gz"; done) -O gvcf/merged.g.vcf
```

- `MergeVcfs`，把多个 VCF 文件拼成一个，不重新分型，比重新跑一遍快得多。
- `$(for ...)`，命令替换把 `-I 文件名` 拼成完整参数串。文件名多的时候比手写一长串可靠，但文件名里带空格会出错，所以 `cut -f 1` 只取第一列。
- 这一步只是文件级拼接，样本必须不重叠。同一个样本的两段 GVCF 要放在同一个 `-V` 列表里，不能一个文件里出现两次。

## 联合分型

样本少时直接合并 GVCF 再分型。

```bash
gatk CombineGVCFs -R ref/genome.fa -V gvcf/sample01.g.vcf.gz -V gvcf/sample02.g.vcf.gz -O gvcf/combined.g.vcf.gz
```

- `-R`，参考序列，要与各 GVCF 用的是同一份。
- `-V` 可以重复出现，每个样本一次。
- `-O`，合并后的 GVCF，位点还是各个样本原来的记录。
- 样本多或者基因组大时，CombineGVCFs 会把整个基因组读进内存，要换成下一段的按区间建库。

合并好的 GVCF 交给 GenotypeGVCFs，联合分型在这一步完成：

```bash
gatk --java-options -Xmx80g GenotypeGVCFs -R ref/genome.fa -V gvcf/combined.g.vcf.gz --include-non-variant-sites -ploidy 2 -O vcf/raw.vcf.gz
```

- `--java-options -Xmx80g`，给 JVM 的堆上限。这一步要把所有样本的基因型同时拿在内存里，样本多时默认堆不够。
- `GenotypeGVCFs` 会重新计算每个位点在每个样本上的基因型，这一步是联合分型的核心。
- `--include-non-variant-sites`，连不变位点一起输出。VCF 会大很多，但如果后面要做群体遗传统计量，比如 Fst 和位点频率谱，必须带上。
- `-ploidy 2`，二倍体。倍性写错，基因型全部是错的。

样本多、区间大时走数据库这条路，先把各样本的 GVCF 按区间导进去：

```bash
gatk GenomicsDBImport -L chr1 --genomicsdb-workspace-path gb/chr1 --sample-name-map sample.map --reader-threads 20 --batch-size 20 -R ref/genome.fa --tmp-dir tmp/gb.chr1
```

- `-L chr1`，限定区间。按染色体或更大的区间拆开，是控制内存的主要手段。
- `--genomicsdb-workspace-path`，数据库目录，一个区间一个，目录名要能看出对应哪段。
- `--sample-name-map`，两列文件，依次是样本名和 GVCF 路径。用 -V 传一堆 GVCF 时，GATK 会从文件路径猜样本名，容易出错，用映射文件显式指定更稳。
- `--tmp-dir`，临时文件目录。建库过程中会写出大量中间块文件，不指定就写在默认临时目录，把系统盘写满之后报的是写失败，不是磁盘满。这一项在样本多、区间大的项目里必须显式设置。
- `--reader-threads`，读 GVCF 的线程数。
- `--batch-size`，每批读入的样本数，样本很多时调小可以降低内存峰值。

映射文件用两行命令生成，不要在文本编辑器里手敲样本名和路径，先按样本名拼出两列，

```bash
for i in $(cat sample.list); do echo "$i gvcf/$i.g.vcf.gz"; done > sample.map
```

- `sample.list`，一行一个样本名，`gvcf/` 下是同名的 GVCF。
- `for ... done > sample.map`，先把命令拼出来再重定向，样本几百个时比手敲可靠。

生成完先看一眼，

```bash
head -2 sample.map
```

- 第一列是样本名，第二列是 GVCF 的路径，用空格分隔。
- 样本名里带空格或特殊字符时，这一列会在建库阶段才报错，所以这一步不能省。

数据库建好就可以分型，输出是逐区间的原始 VCF：

```bash
gatk GenotypeGVCFs -R ref/genome.fa -V gendb://gb/chr1 -O gb.combine.vcf/chr1_combine.vcf.gz --tmp-dir tmp/gg.chr1
```

- `gendb://`，读数据库时用这个前缀，注意是两条斜杠，写成一条会被当成相对路径。
- `--tmp-dir`，同样要显式指定。分型时会把区间内所有样本的基因型展开，临时文件比数据库本身还大。
- 这一步的输出是每个区间的原始 VCF，还没有过任何质量过滤，命名上用 `raw` 或 `combine` 区分开。
- 建库和分型都按区间做，最后把各条染色体的 VCF 合并。

## 结构变异检测

上面的流程只管 SNP 和 InDel。倒位、大片段缺失、拷贝数变化这些结构变异不靠局部组装判断，得用专门工具。delly 用双端 read 的异常插入距离和切割位点找断点，输入就是前面已经去重、建过索引的 BAM，

```bash
for i in $(cat sample.list); do
  delly call -o SV/${i}.bcf -g ref/genome.fa bam/${i}.markdup.bam
done > SV.sh
```

- `delly call`，单样本检测，输出 BCF。`-o` 是输出文件，`-g` 是参考基因组，位置参数是 BAM。
- 这里是先把每个样本的命令拼成脚本再批量跑，delly 单样本跑一条命令，几百个样本逐条手敲不现实。
- 参考要用与比对时同一份。换了参考，断点坐标全错。

拼完先看一眼再决定要不要跑，

```bash
less SV.sh
```

- 看一眼拼出来的命令，样本名、路径、参考都在再往下跑。

单样本 BCF 之间还不能直接比较，要先把所有样本的断点合并成一个位点集合，

```bash
delly merge -o SV/sites.bcf SV/*.bcf
```

- `-o`，合并后的位点集合。
- 不同样本在同一位置上的断点在这里对齐，后面才能逐位点重新分型。

再拿这份位点集合回去给每个样本定基因型，

```bash
delly call -g ref/genome.fa -v SV/sites.bcf -o SV/merged.bcf bam/*.markdup.bam
```

- `-v`，上一步的位点集合；后面跟所有样本的 BAM，在每个位点上重新判定基因型，等价于 SNP 那边的联合分型。
- 每个样本都要写全，命令行会很长，用通配符展开就行；样本多到超出命令行长度上限时改用文件列表。

最后过滤，

```bash
delly filter -f germline -o SV/germline.bcf SV/merged.bcf
```

- `-f germline`，把体细胞型、单样本型事件滤掉，留下一套可信的胚系结构变异。做植物群体时按需要改用其他过滤类型。
- 结构变异的断点精度本来就比 SNP 粗，报坐标时要连区间一起给，不要只给一个碱基位置。

## SNP 与 InDel 过滤

SNP 和 InDel 的错误来源不同，必须分开过滤。SNP 主要怕比对质量低、链偏倚和碱基质量差；InDel 主要怕比对位置的读数支持度不足。

```bash
gatk SelectVariants -select-type SNP -V vcf/raw.vcf.gz -O vcf/raw.snp.vcf.gz
```

- `-select-type SNP`，只取 SNP 记录。
- `-V` 与 `-O`，输入的原始 VCF 和输出的子集。两个类型分开取，后面才能套不同的过滤条件。

InDel 单独取一份，它的过滤条件和 SNP 不同，混在一起套不准：

```bash
gatk SelectVariants -select-type INDEL -V vcf/raw.vcf.gz -O vcf/raw.indel.vcf.gz
```

- `-select-type INDEL`，只取 InDel 记录。选出来的位点数比 SNP 少很多，这是正常的。

SNP 的过滤条件分两批跑，中间文件留着方便对结果，

```bash
gatk VariantFiltration -V vcf/raw.snp.vcf.gz -O vcf/raw.snp.f1.vcf.gz --filter-expression "QD < 2.0" --filter-name "QD2" --filter-expression "QUAL < 30.0" --filter-name "QUAL30" --filter-expression "FS > 60.0" --filter-name "FS60" --filter-expression "MQ < 40.0" --filter-name "MQ40"
```

- `-V` 与 `-O`，输入第一路的 SNP 子集，输出带 FILTER 字段的 VCF。写到 f1 而不是直接覆盖，是为了下一批还能接着跑。
- `--filter-expression` 与 `--filter-name`，成对出现，前者是表达式，后者是写进 FILTER 列的名字。名字要能看出条件，比如 QD2 就是 QD 小于 2。
- `QD`，质量深度，变异质量值除以深度。低 QD 表示支持变异的 reads 虽多但质量差。
- `QUAL`，位点质量值。
- `FS`，Fisher 精确检验的链偏倚值。测序或比对有链偏好时，变异只在正链或只在负链出现。
- `MQ`，比对质量。低于阈值说明该区域的 reads 比对不可靠，通常是重复或结构变异区。
- `--filter-expression` 可以重复出现。这里一批写完，输出里只会多出 FILTER 列，位点一条不少，真正的剔除在下一步。

第二批条件接着往 f1 上叠，SNP 的过滤到这一步结束：

```bash
gatk VariantFiltration -V vcf/raw.snp.f1.vcf.gz -O vcf/final.snp.vcf.gz --filter-expression "SOR > 3.0" --filter-name "SOR3" --filter-expression "MQRankSum < -12.5" --filter-name "MQRankSum-12.5" --filter-expression "ReadPosRankSum < -8.0" --filter-name "ReadPosRankSum-8.0"
```

- `-V`，吃上一步的输出，两批条件叠加，前面的 FILTER 标签会保留。
- `SOR`，链偏倚的对称化比值，与 FS 看的角度不同，两者都留着。
- `MQRankSum` 与 `ReadPosRankSum`，分别检验变异 reads 与参考 reads 的比对质量差、变异在 read 上的位置分布。负值偏大表示变异集中在 read 末端，多半是假阳性。
- 分成两批跑的效果与一批写完一样，好处是每批的中间文件都能单独拿出来数位点。

InDel 的阈值整条另写一遍，FS 和 SOR 都比 SNP 放宽：

```bash
gatk VariantFiltration -V vcf/raw.indel.vcf.gz -O vcf/final.indel.vcf.gz --filter-expression "QD < 2.0" --filter-name "QD2" --filter-expression "FS > 200.0" --filter-name "FS200" --filter-expression "SOR > 10.0" --filter-name "SOR10"
```

- 阈值与 SNP 不同，FS 放宽到 200，SOR 放宽到 10。InDel 的链偏倚和比对质量本来就比 SNP 差，套 SNP 的阈值会砍掉大量真 InDel。
- SNP 与 InDel 分两套条件，最后再合起来，不要用一套阈值盖两种变异。
- 这些阈值是模式化的起点，不是普适常数。先看自己数据的 QD、MQ 分布，如果整体偏低，比如参考组装比较碎，这批阈值会砍掉一半位点。

## 深度与覆盖度检查

深度是覆盖某个位点的 reads 条数，覆盖度是达到某个深度的位点比例，两者不是一回事，报的时候要一起报。深度是一个位点能不能信的唯一直接依据。

```bash
samtools depth -a bam/sample01.markdup.bam > qc/sample01.depth
```

- `-a`，包含深度为 0 的位点。不加 `-a` 只能看到有覆盖的位置，看不到缺失区域。
- 输出是每个碱基一行，文件很大，看完就删。

逐碱基的深度文件太大，换 500 kb 窗口看全基因组的深浅分布：

```bash
sambamba depth window -w 500000 bam/sample01.markdup.bam -o qc/sample01.500k_window.depth.txt
```

- `window -w 500000`，按 500 kb 窗口统计平均深度，快速看全基因组的深浅分布。
- `-o`，结果写文件，按染色体、按样本看。如果某条染色体的深度只有全基因组均值的一半，通常是这条染色体在参考里被拆成了两段，或者有塌缩重复，先查参考，别急着调过滤参数。

再看比对率、重复率和配对情况，判断这个样本能不能进下一步：

```bash
samtools flagstat bam/sample01.markdup.bam > qc/sample01.flagstat.txt
```

- 统计比对率、重复率、配对情况。这三项用来判断这个样本能不能进下一步。
- 深度异常高的区域是重复序列或拷贝数变异区，那里检测出的变异多半是假的。

## 另一条路线：bcftools 直接检测

不写 GVCF、不做联合分型，一个命令出 VCF。适合简化基因组、低深度、样本量特别大的场景，代价是没有确定没变的证据，跨样本的缺失判断更粗糙。

```bash
bcftools mpileup -f ref/genome.fa -b qc/bamlist.txt -r chr1 --threads 6 -a AD,DP -O z -o vcf/raw_chr1.pileup.vcf.gz
```

- `-f`，参考序列。
- `-b`，BAM 列表文件，每行一个路径。
- `-r`，染色体或区间。按染色体拆分是控制内存的主要方式。
- `--threads 6`，压缩线程数。
- `-a AD,DP`，输出等位基因深度和总深度，一定要加。后面按等位基因平衡做质控、判断杂合是否可信全靠这两个字段，不写就再也没有机会补回来。
- 有了 AD 才能算 VAF，也就是某个位点上支持变异的 reads 数除以总 reads 数。杂合位点的 VAF 应当接近 0.5，明显偏离就说明这个基因型不可信。
- `-O z`，输出压缩的 VCF。mpileup 和 call 分两步跑时中间文件会大一些，换来的是每一步都能单独重跑。

mpileup 的输出交给 call 出基因型，按染色体一片一片跑：

```bash
bcftools call -m -v --threads 2 -O z -o vcf/raw_chr1.vcf.gz vcf/raw_chr1.pileup.vcf.gz
```

- `-m`，多等位模型。
- `-v`，只输出变异位点。
- 位置参数就是上一步的 mpileup 结果，位点文件按染色体一片一片出。

各染色体的 VCF 合并起来，样本集不一致时用按位置合并而不是拼接：

```bash
bcftools merge --force-samples vcf/raw_chr1.vcf.gz vcf/raw_chr2.vcf.gz -O z -o vcf/raw_all.vcf.gz
```

- `--force-samples`，按位置合并多个 VCF，样本集不一致时用这个参数而不是 concat，缺的样本会补成缺失基因型。
- `-O z` 与 `-o`，合并结果压缩输出，得到全基因组的原始 VCF。

最后按类型、质量和缺失率筛一遍，得到可以入库的 SNP 集：

```bash
bcftools filter -i 'TYPE="snp" && QUAL>=20 && F_MISSING<0.5' -O z -o vcf/snps_filtered.vcf.gz vcf/raw_all.vcf.gz
```

- `-i '...'`，保留满足表达式的位点。
- `TYPE="snp"`，只要 SNP，把 InDel 和混合位点放在一边。
- `QUAL>=20`，位点质量下限，比 GATK 那套宽松，低深度数据上不要卡太严。
- `F_MISSING<0.5`，缺失率上限，一个位点超过一半样本没有基因型就丢掉。
- 表达式里的运算符按 bcftools 文档写，`&` 是同一条件内的与。写成记录级布尔运算时条件会恒真或恒假，结果看起来正常但等于没过滤。
