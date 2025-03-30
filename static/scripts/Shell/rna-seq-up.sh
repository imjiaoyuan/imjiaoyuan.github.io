#!/bin/bash

# RNA-seq数据分析流程脚本
# 从原始数据到表达量定量的RNA-seq数据处理流程
#
# 流程包含以下步骤：
# 1. SRA数据下载
# 2. SRA转FASTQ
# 3. 质量控制(FastQC + MultiQC)
# 4. 数据过滤(Trim_galore)
# 5. 比对到参考基因组(HISAT2)
# 6. SAM/BAM处理和排序
# 7. 转录本组装(StringTie)
# 8. 表达量定量(featureCounts)
#
# 使用方法：
# 1. 准备SRR_Acc_List.txt文件，每行一个SRR号
# 2. 准备参考基因组文件和注释文件
# 3. 修改脚本中的参数
# 4. 运行脚本: bash rna-seq-up.sh

# 严格模式设置
set -e  # 遇到错误立即退出
set -u  # 使用未定义的变量时报错
set -o pipefail  # 管道中的任何错误都会导致退出

# 配置参数
THREADS=4  # 线程数
MEMORY="20G"  # 内存限制
GENOME_PATH="../oryza_sativa.fa"  # 基因组文件路径
GTF_PATH="../oryza_sativa.gff3"   # 注释文件路径
SPECIES="oryza_sativa"  # 物种名称

# 激活conda环境
source ~/.bashrc  # 确保conda命令可用
conda activate RNA-seq || {
    echo "Error: Could not activate conda environment 'RNA-seq'"
    exit 1
}

# 创建项目目录结构
PROJECT_DIR="./project"
mkdir -p "${PROJECT_DIR}"/{sra,fastq_gz,fastqc_reports,clean,sorted,genome_index,compared,counts,assembled}

# 检查输入文件
if [ ! -f "SRR_Acc_List.txt" ]; then
    echo "Error: SRR_Acc_List.txt not found"
    exit 1
fi

if [ ! -f "$GENOME_PATH" ]; then
    echo "Error: Genome file not found at $GENOME_PATH"
    exit 1
fi

if [ ! -f "$GTF_PATH" ]; then
    echo "Error: GTF/GFF file not found at $GTF_PATH"
    exit 1
fi

# 下载SRA数据
echo "Downloading SRA files..."
cat SRR_Acc_List.txt | while read id; do
    if [ ! -f "./sra/${id}.sra" ]; then
        prefetch -O ./sra "$id"
    fi
done

# SRA转FASTQ
echo "Converting SRA to FASTQ..."
parallel -j $THREADS "fastq-dump --gzip --split-3 -O ./fastq_gz {}" ::: ./sra/*.sra

# FastQC质量控制
echo "Running FastQC..."
mkdir -p fastqc_reports
fastqc -t $THREADS -o ./fastqc_reports ./fastq_gz/*.fastq.gz
multiqc ./fastqc_reports -o ./fastqc_reports

# Trim_galore过滤
echo "Filtering reads with Trim_galore..."
cat SRR_Acc_List.txt | while read id; do
    trim_galore \
        -q 20 \
        --length 36 \
        --max_n 3 \
        --stringency 3 \
        --fastqc \
        --paired \
        --cores $THREADS \
        -o ./clean/ \
        "./fastq_gz/${id}_1.fastq.gz" \
        "./fastq_gz/${id}_2.fastq.gz"
done

# 建立基因组索引
echo "Creating genome index..."
cd genome_index
if [ ! -f "${SPECIES}.1.ht2" ]; then
    cp "$GENOME_PATH" .
    hisat2-build -p $THREADS "${SPECIES}.fa" "${SPECIES}"
fi
cd ..

# 比对到参考基因组
echo "Aligning reads to reference genome..."
cat SRR_Acc_List.txt | while read id; do
    hisat2 \
        -x "./genome_index/${SPECIES}" \
        -p $THREADS \
        -1 "./clean/${id}_1_val_1.fq.gz" \
        -2 "./clean/${id}_2_val_2.fq.gz" \
        2> "./compared/${id}.log" \
        | samtools view -bS - > "./compared/${id}.bam"
done

# SAM排序
echo "Sorting BAM files..."
cat SRR_Acc_List.txt | while read id; do
    samtools sort \
        -@ $THREADS \
        -m $MEMORY \
        "./compared/${id}.bam" \
        -o "./sorted/${id}.sorted.bam"
done

# 转录本组装
echo "Assembling transcripts..."
cat SRR_Acc_List.txt | while read id; do
    stringtie \
        -p $THREADS \
        -G "$GTF_PATH" \
        -o "./assembled/${id}.gtf" \
        "./sorted/${id}.sorted.bam"
done

# 表达量定量
echo "Quantifying expression..."
cd sorted
bam_files=$(ls *.sorted.bam)
featureCounts \
    -T $THREADS \
    -t exon \
    -g Parent \
    -a "$GTF_PATH" \
    -o ../counts/counts.txt \
    -p $bam_files

echo "Pipeline completed successfully!"