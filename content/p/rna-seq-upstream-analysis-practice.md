---
title: RNA-Seq 上游分析实践
date: 2024-03-30
---

之前那一篇文章主要讲的是一些知识与工具的用法，这次用六组数据进行分析，得到基因表达矩阵。

<!--more-->

首先从 NCBI SRA 数据库搜索合适的数据，查看数据是双端测序的数据之后，多选条目，直接生成 Accession list。

![](/i/20230908203392.jpg)

我使用的是下列数据：

```txt
SRR25907783
SRR25907784
SRR25907785
SRR25907786
SRR25907787
SRR25907788
```

使用 sra-tools 工具批量下载测序数据，并且使用 nohup 把程序挂在后台下载：

```bash
nohup prefetch --option-file acc_list.txt &
```

再使用脚本进行拆分。注意，必须等待上一步的`prefetch`下载任务完成后再执行。

```bash
#!/bin/bash
# 创建输出目录
mkdir -p sra_files fastq_files

# 将下载好的 sra 文件（位于以各自 ACC ID 命名的子目录中）移动到统一的 sra_files 目录
cat acc_list.txt | while read id; do
    mv ./${id}/${id}.sra ./sra_files/
done

# 批量转换 sra 为 fastq.gz
cd sra_files || exit
for sra_file in *.sra; do
    fastq-dump --gzip --split-files "$sra_file" -O ../fastq_files
done
```

这里千万不要在程序没有运行完成的时候就进行下一步操作。使用 `top` 或 `ps -u $USER` 可以查看后台进程：

![](/i/20230908204934.jpg)

当程序运行完成后便可看到后台任务中已经没有前面运行的程序了：

![](/i/20230908205137.jpg)

同一目录下的 `nohup.out` 文件中是后台进程的运行记录。

拆分完成后就需要进行质量检测，使用通配符批量检测，并且将检测报告放在单独一个文件夹以便后面进行合并：

```bash
mkdir fastqc_report
fastqc ./fastq_files/*.fastq.gz -o ./fastqc_report
```

完成之后，将检测报告进行合并，以便查看：

```bash
multiqc ./fastqc_report
```

依据检测报告对序列进行过滤，参数之前已经讲过，这里数据比较多，写一个 bash 脚本的 for 循环：

```bash
#!/bin/bash
# 切换到包含原始 fastq 文件的目录
cd fastq_files || exit

# 循环处理每一对文件
for i in {3..8}; do
    trimmomatic PE \
        -threads 4 \
        -phred33 \
        SRR2590778${i}_1.fastq.gz SRR2590778${i}_2.fastq.gz \
        SRR2590778${i}_1P.fastq.gz SRR2590778${i}_1U.fastq.gz \
        SRR2590778${i}_2P.fastq.gz SRR2590778${i}_2U.fastq.gz \
        -summary ../SRR2590778${i}.summary \
        LEADING:3 TRAILING:3 SLIDINGWINDOW:5:20 HEADCROP:15 MINLEN:36
done
```

这里是对 SRR25907783 到 SRR25907788 的数据进行处理，根据自己数据的情况将这里进行修改即可。

下载水稻的参考基因组和注释文件进行 hisat2 比对：

```bash
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-57/fasta/oryza_sativa/dna/Oryza_sativa.IRGSP-1.0.dna.toplevel.fa.gz
wget https://ftp.ensemblgenomes.ebi.ac.uk/pub/plants/release-57/gff3/oryza_sativa/Oryza_sativa.IRGSP-1.0.57.gff3.gz
```

把下载的文件解压后重命名，方便使用：

```bash
gzip -d Oryza_sativa.IRGSP-1.0.dna.toplevel.fa.gz
mv Oryza_sativa.IRGSP-1.0.dna.toplevel.fa oryza_sativa.fa

gzip -d Oryza_sativa.IRGSP-1.0.57.gff3.gz
mv Oryza_sativa.IRGSP-1.0.57.gff3 oryza_sativa.gff3```

先构建 hisat2 索引：

```bash
hisat2-build oryza_sativa.fa oryza_sativa
```

构建完成之后开始将 reads 比对到参考基因组，还是写成脚本进行：

```bash
#!/bin/bash
# 假设质控后的文件在 fastq_files/ 目录下
cd fastq_files || exit

for i in {3..8}
do
    hisat2 -x ../oryza_sativa -p 5 -1 SRR2590778${i}_1P.fastq.gz -2 SRR2590778${i}_2P.fastq.gz -S ../SRR2590778${i}.sam
done
```

接着对比对结果进行排序，还是写成 bash 脚本一键进行：

```bash
#!/bin/bash
for i in {3..8}
do
    samtools sort -@ 5 SRR2590778${i}.sam -o SRR2590778${i}.sorted.bam
done
```

最后一步使用 featureCounts 生成基因计数表：

```bash
#!/bin/bash
# 确保在包含 BAM 文件的目录中运行
bam_files=(*.sorted.bam)  # 将所有的 sorted bam 文件作为变量，输入给 featureCounts

if [ ${#bam_files[@]} -gt 0 ]; then
    featureCounts -T 5 -p -t exon -g gene_id -a oryza_sativa.gff3 -o gene.counts.txt "${bam_files[@]}"
else
    echo "No sorted BAM files found in the current directory."
fi
```

至此完成，拿到基因表达矩阵。

个人习惯完成分析后把文件进行一下归类：

![](/i/20230908205327.jpg)

最后将数据下载到本地进行下游分析：

![](/i/20230908205772.jpg)
