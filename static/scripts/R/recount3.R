# TCGA数据获取与预处理脚本
#
# 功能：从recount3数据库下载TCGA项目的RNA-seq数据，并进行初步处理
#
# 输出目录结构:
# D:/JiaoYuan/
# ├── cache/              # recount3缓存目录
# ├── TCGA_NORMAL/       # 正常样本数据
# │   ├── CHOL_normal.csv
# │   └── HNSC_normal.csv
# └── TCGA_TUMOR/        # 肿瘤样本数据
#     ├── CHOL_tumor.csv
#     └── HNSC_tumor.csv
#
# 输出文件格式:
# - project_normal.csv, project_tumor.csv:
#   gene_id     sample1  sample2  sample3
#   gene1       100      200      150
#   gene2       300      250      350
#   ...

# 清理环境并设置语言
rm(list = ls())  
Sys.setenv(LANGUAGE = "en")

# 安装必要的包
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")
if (!requireNamespace("recount3", quietly = TRUE))
    BiocManager::install("recount3")

# 加载必要的包
library(recount3)
library(dplyr)

# 设置基础路径
base_dir <- "D:/JiaoYuan"
cache_dir <- file.path(base_dir, "cache")
normal_dir <- file.path(base_dir, "TCGA_NORMAL")
tumor_dir <- file.path(base_dir, "TCGA_TUMOR")

# 创建必要的目录
dirs <- c(cache_dir, normal_dir, tumor_dir)
sapply(dirs, dir.create, recursive = TRUE, showWarnings = FALSE)

# 设置代理和SSL选项
options(
    download.file.method = "libcurl",
    ssl.verifypeer = FALSE,
    http_proxy = "http://127.0.0.1:7897",
    https_proxy = "http://127.0.0.1:7897"
)

# 设置 recount3 参数
options(
    recount3_url = "https://recount-opendata.s3.amazonaws.com/recount3/release",
    recount3_organism = "human",
    recount3_cache = cache_dir
)

# 验证设置
message("Configuration:")
message("Cache directory: ", getOption("recount3_cache"))
message("Recount3 URL: ", getOption("recount3_url"))
message("Organism: ", getOption("recount3_organism"))

# 定义数据处理函数
process_counts <- function(count_trans, sub_proj_rse) {
    # 转换 barcode
    barcode_to_file <- sub_proj_rse@colData@listData$tcga.tcga_barcode
    names(barcode_to_file) <- sub_proj_rse@colData@listData$tcga.gdc_file_id
    colnames(count_trans) <- unlist(lapply(colnames(count_trans), function(x) barcode_to_file[x]))
    
    # 分离正常和肿瘤样本
    normal_samples <- character(0)
    tumor_samples <- character(0)
    
    for (col in colnames(count_trans)) {
        if (as.numeric(substring(col, 14, 15)) >= 10) {
            normal_samples <- c(normal_samples, col)
        } else {
            tumor_samples <- c(tumor_samples, col)
        }
    }
    
    # 提取数据
    count_trans_normal <- count_trans[, normal_samples]
    count_trans_tumor <- count_trans[, tumor_samples]
    
    return(list(normal = count_trans_normal, tumor = count_trans_tumor))
}

# 处理基因名函数
process_rownames <- function(data) {
    # 移除 PAR_Y 基因
    rows_to_drop <- grep("_PAR_Y", rownames(data))
    if (length(rows_to_drop) > 0) {
        data <- data[-rows_to_drop, ]
    }
    # 移除版本号
    rownames(data) <- gsub("\\.\\d+$", "", rownames(data))
    return(data)
}

# 主程序
tryCatch({
    # 获取可用项目
    message("Fetching available projects...")
    human_projects <- available_projects()
    
    # 筛选TCGA项目
    message("Filtering TCGA projects...")
    sub_proj <- subset(human_projects, file_source == "tcga")
    
    # 筛选目标项目
    target_projects <- c("HNSC", "CHOL")
    target_sub_proj <- sub_proj[sub_proj$project %in% target_projects, ]
    message("Target projects: ", paste(target_projects, collapse = ", "))
    
    # 处理每个项目
    for (i in 1:nrow(target_sub_proj)) {
        project <- target_sub_proj[i, ]$project
        message("\nProcessing project: ", project)
        
        # 创建RSE对象
        message("Creating RSE object...")
        sub_proj_rse <- create_rse(target_sub_proj[i, ], type = "gene")
        
        # 转换计数
        message("Transforming counts...")
        count_trans <- transform_counts(sub_proj_rse, by = "auc")
        
        # 处理数据
        message("Processing counts...")
        processed_counts <- process_counts(count_trans, sub_proj_rse)
        
        # 处理基因名
        message("Processing gene names...")
        count_trans_normal <- process_rownames(processed_counts$normal)
        count_trans_tumor <- process_rownames(processed_counts$tumor)
        
        # 保存数据
        message("Saving data...")
        write.csv(
            count_trans_normal,
            file.path(normal_dir, paste0(project, "_normal.csv"))
        )
        write.csv(
            count_trans_tumor,
            file.path(tumor_dir, paste0(project, "_tumor.csv"))
        )
        
        message("Completed processing ", project)
    }
    
    message("\nAll projects processed successfully!")
    
}, error = function(e) {
    message("\nError occurred: ", e$message)
}, warning = function(w) {
    message("\nWarning: ", w$message)
}, finally = {
    message("\nScript execution completed.")
})