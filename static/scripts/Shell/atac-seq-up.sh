#!/bin/bash

# ATAC-seq数据分析流程脚本
# 从原始数据到比对后的BAM文件的ATAC-seq数据处理流程
#
# 流程包含以下步骤：
# 1. SRA数据下载
# 2. SRA转FASTQ
# 3. 质量控制(FastQC + MultiQC)
# 4. 数据过滤(Fastp)
# 5. 比对到参考基因组(BWA)
# 6. SAM/BAM处理和排序
# 7. 去除PCR重复
# 8. 创建索引
# 9. 生成bigwig文件
#
# 使用方法：
# 1. 准备SRR_Acc_List.txt文件，每行一个SRR号
# 2. 准备参考基因组文件
# 3. 修改脚本中的参数
# 4. 运行脚本: bash atac-seq-up.sh

# 严格模式设置
set -e  # 遇到错误立即退出
set -u  # 使用未定义的变量时报错
set -o pipefail  # 管道中的任何错误都会导致退出

# 配置参数
THREADS=4  # 线程数
MEMORY="20G"  # 内存限制
GENOME_PATH="../oryza_sativa.fa"  # 基因组文件路径
SPECIES="oryza_sativa"  # 物种名称

# 激活conda环境
source ~/.bashrc  # 确保conda命令可用
conda activate ATAC-seq || {
    echo "Error: Could not activate conda environment 'ATAC-seq'"
    exit 1
}

# 创建项目目录结构
PROJECT_DIR="./project"
mkdir -p "${PROJECT_DIR}"/{sra,fastq_gz,fastqc_reports,clean,sorted,genome_index,compared,rdup,sam_index,bigwig}

# 检查输入文件
if [ ! -f "SRR_Acc_List.txt" ]; then
    echo "Error: SRR_Acc_List.txt not found"
    exit 1
fi

if [ ! -f "$GENOME_PATH" ]; then
    echo "Error: Genome file not found at $GENOME_PATH"
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

# Fastp过滤
echo "Filtering reads with Fastp..."
cat SRR_Acc_List.txt | while read id; do
    fastp \
        -i "./fastq_gz/${id}_1.fastq.gz" \
        -I "./fastq_gz/${id}_2.fastq.gz" \
        -o "./clean/${id}_1.clean.fastq.gz" \
        -O "./clean/${id}_2.clean.fastq.gz" \
        -f 16 \
        -t $THREADS \
        -h "./clean/${id}_fastp.html" \
        -j "./clean/${id}_fastp.json" \
        -w $THREADS
done

# 建立基因组索引
echo "Creating genome index..."
cd genome_index
if [ ! -f "${SPECIES}.fa.bwt" ]; then
    cp "$GENOME_PATH" .
    bwa index -a bwtsw "${SPECIES}.fa"
fi
cd ..

# 比对到参考基因组
echo "Aligning reads to reference genome..."
cat SRR_Acc_List.txt | while read id; do
    bwa mem \
        -t $THREADS \
        "./genome_index/${SPECIES}.fa" \
        "./clean/${id}_1.clean.fastq.gz" \
        "./clean/${id}_2.clean.fastq.gz" \
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

# 去除PCR重复
echo "Removing PCR duplicates..."
cat SRR_Acc_List.txt | while read id; do
    sambamba markdup \
        -r \
        -t $THREADS \
        "./sorted/${id}.sorted.bam" \
        "./rdup/${id}.rdup.bam"
done

# 创建索引
echo "Creating BAM indexes..."
cat SRR_Acc_List.txt | while read id; do
    samtools index -@ $THREADS "./rdup/${id}.rdup.bam"
    mv "./rdup/${id}.rdup.bam.bai" "./sam_index/"
done

# 生成bigwig文件
echo "Generating bigwig files..."
cat SRR_Acc_List.txt | while read id; do
    bamCoverage \
        -b "./rdup/${id}.rdup.bam" \
        -o "./bigwig/${id}.bw" \
        -p $THREADS \
        --normalizeUsing RPKM
done

echo "Pipeline completed successfully!"