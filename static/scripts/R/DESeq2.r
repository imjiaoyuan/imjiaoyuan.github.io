# 差异表达分析脚本 (DESeq2)
#
# 功能：使用DESeq2对FPKM标准化后的数据进行差异表达分析
#
# 输入文件格式 (fpkm_output):
# Geneid  Normal-1-1_FPKM  Normal-1-2_FPKM  Normal-1-3_FPKM  HS-1-1_FPKM ...
# gene1   254.8            242.2            273.2            587.0       ...
# gene2   0.0              0.9              0.9              1.7         ...
#
# 输出文件:
# 1. sample1_vs_sample2.DESeq2.txt - 第一组比较结果
# 2. sample3_vs_sample4.DESeq2.txt - 第二组比较结果
#
# 输出格式:
# GeneID  baseMean  log2FoldChange  lfcSE  stat   pvalue    padj
# gene1   1234.56   2.34           0.23   10.2   1e-10     5e-10
# gene2   567.89    -1.45          0.34   -4.3   2e-5      8e-5

# 清理环境并设置语言
rm(list = ls())  
Sys.setenv(LANGUAGE = "en")

# 加载必要的包
library(DESeq2)    # 差异分析

# 定义分析参数
ANALYSIS_PARAMS <- list(
    min_count = 10,        # 最小计数阈值
    fit_type = "mean",     # 拟合类型
    min_replicates = 7,    # 最小重复数
    run_parallel = FALSE   # 是否并行计算
)

# 定义样本分组
SAMPLE_GROUPS <- list(
    group1 = c(
        "Normal-1-1_FPKM", "Normal-1-2_FPKM", "Normal-1-3_FPKM",
        "HS-1-1_FPKM", "HS-1-2_FPKM", "HS-1-3_FPKM"
    ),
    group2 = c(
        "Normal-2-1_FPKM", "Normal-2-2_FPKM", "Normal-2-3_FPKM",
        "HS-2-1_FPKM", "HS-2-2_FPKM", "HS-2-3_FPKM"
    )
)

# 数据预处理函数
preprocess_data <- function(data) {
    message("Preprocessing data...")
    
    # 将数据四舍五入为整数
    data_int <- round(data)
    
    # 处理小于1的值
    numeric_cols <- sapply(data_int, is.numeric)
    data_int[numeric_cols] <- lapply(
        data_int[numeric_cols],
        function(x) ifelse(is.numeric(x) & x < 1, x + 100, x)
    )
    
    # 确保所有数值都是整数
    data_int[-1, ] <- apply(data_int[-1, ], 2, as.integer)
    
    # 移除包含NA的行
    data_clean <- na.omit(data_int)
    
    return(data_clean)
}

# 准备DESeq2数据集函数
prepare_deseq_data <- function(count_data, sample_info) {
    message("Preparing DESeq2 dataset...")
    dds <- DESeqDataSetFromMatrix(
        countData = count_data,
        colData = sample_info,
        design = ~sample
    )
    
    # 过滤低表达基因
    keep <- rowSums(counts(dds)) >= ANALYSIS_PARAMS$min_count
    dds <- dds[keep,]
    
    return(dds)
}

# 运行DESeq2分析函数
run_deseq2 <- function(dds) {
    message("Running DESeq2 analysis...")
    dds <- DESeq(
        dds,
        fitType = ANALYSIS_PARAMS$fit_type,
        minReplicatesForReplace = ANALYSIS_PARAMS$min_replicates,
        parallel = ANALYSIS_PARAMS$run_parallel
    )
    return(dds)
}

# 获取差异分析结果函数
get_results <- function(dds, contrast_pairs) {
    message("Extracting results...")
    results_list <- list()
    
    for (pair in contrast_pairs) {
        message(sprintf("Processing contrast: %s vs %s", pair[1], pair[2]))
        
        res <- results(
            dds,
            contrast = c("sample", pair[1], pair[2])
        )
        
        results_list[[paste(pair[1], "vs", pair[2])]] <- 
            data.frame(res, stringsAsFactors = FALSE, check.names = FALSE)
    }
    
    return(results_list)
}

# 主程序
tryCatch({
    # 读取数据
    message("Reading FPKM data...")
    fpkm <- read.csv(
        'fpkm_output',
        header = TRUE,
        sep = '\t',
        row.names = "Geneid",
        comment.char = '#',
        check.names = FALSE
    )
    
    # 数据预处理
    fpkm_processed <- preprocess_data(fpkm)
    
    # 准备样本信息
    samples <- data.frame(
        sampleID = c(SAMPLE_GROUPS$group1, SAMPLE_GROUPS$group2),
        sample = factor(
            c(rep("sample1", 3), rep("sample2", 3),
              rep("sample3", 3), rep("sample4", 3)),
            levels = c("sample1", "sample2", "sample3", "sample4")
        )
    )
    rownames(samples) <- samples$sampleID
    
    # 准备DESeq2数据集
    dds <- prepare_deseq_data(fpkm_processed, samples)
    
    # 运行DESeq2分析
    dds_analyzed <- run_deseq2(dds)
    
    # 定义对比组
    contrasts <- list(
        c("sample1", "sample2"),
        c("sample3", "sample4")
    )
    
    # 获取结果
    results <- get_results(dds_analyzed, contrasts)
    
    # 保存结果
    message("Saving results...")
    for (name in names(results)) {
        output_file <- paste0(gsub(" ", "", name), ".DESeq2.txt")
        write.table(
            results[[name]],
            output_file,
            col.names = NA,
            sep = '\t',
            quote = FALSE
        )
    }
    
    message("Analysis completed successfully!")
    
}, error = function(e) {
    message("\nError occurred: ", e$message)
}, warning = function(w) {
    message("\nWarning: ", w$message)
}, finally = {
    message("\nScript execution completed.")
})