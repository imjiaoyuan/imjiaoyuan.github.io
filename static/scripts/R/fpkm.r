# FPKM标准化脚本
#
# 功能：将原始counts矩阵转换为FPKM (Fragments Per Kilobase Million) 标准化矩阵
#
# 输入文件格式 (counts):
# Geneid  Chr  Start  End  Strand  Length  Sample1  Sample2  Sample3  ...
# gene1   chr1 2983   3268 +       2935    748     711      802      ...
# gene2   chr1 11218  12060 +       1127    0       1        1       ...
#
# 输出文件格式 (fpkm):
# Geneid  Sample1_FPKM  Sample2_FPKM  Sample3_FPKM  ...
# gene1   254.8         242.2         273.2         ...
# gene2   0.0           0.9           0.9           ...
#
# FPKM计算公式：
# FPKM = (reads_count * 10^9) / (total_reads * gene_length)

# 清理环境并设置语言
rm(list = ls())
Sys.setenv(LANGUAGE = "en")

# 定义FPKM计算函数
calculate_fpkm <- function(counts_data) {
    # 参数检查
    required_cols <- c("Length")
    if (!all(required_cols %in% colnames(counts_data))) {
        stop("Missing required columns: Length")
    }
    
    # 获取样本列（排除基因信息列）
    sample_cols <- colnames(counts_data)[6:ncol(counts_data)]
    if (length(sample_cols) == 0) {
        stop("No sample columns found")
    }
    
    # 计算每个样本的总读数
    message("Calculating library sizes...")
    depths <- colSums(counts_data[, sample_cols])
    
    # 创建结果数据框
    message("Calculating FPKM values...")
    result <- data.frame(Geneid = counts_data$Geneid)
    
    # 对每个样本计算FPKM
    for (sample in sample_cols) {
        # 计算FPKM
        fpkm_col <- paste0(sample, "_FPKM")
        result[[fpkm_col]] <- (counts_data[[sample]] * 10^9) / 
                             (counts_data$Length * depths[sample])
    }
    
    return(result)
}

# 主程序
tryCatch({
    message("Reading count data...")
    counts <- read.table(
        'counts',
        header = TRUE,
        sep = '\t',
        comment.char = '#',
        check.names = FALSE
    )
    
    # 数据有效性检查
    if (nrow(counts) == 0) {
        stop("Empty input file")
    }
    
    message("Processing FPKM calculation...")
    fpkm_data <- calculate_fpkm(counts)
    
    # 处理极小值
    message("Handling small values...")
    numeric_cols <- sapply(fpkm_data, is.numeric)
    fpkm_data[, numeric_cols] <- lapply(
        fpkm_data[, numeric_cols],
        function(x) ifelse(x < 1, x + 1, x)
    )
    
    # 保存结果
    message("Saving results...")
    write.table(
        fpkm_data,
        file = 'fpkm',
        sep = '\t',
        row.names = FALSE,
        quote = FALSE
    )
    
    message("FPKM calculation completed successfully!")
    
}, error = function(e) {
    message("\nError occurred: ", e$message)
}, warning = function(w) {
    message("\nWarning: ", w$message)
}, finally = {
    message("\nScript execution completed.")
})