# 主成分分析(PCA)脚本
#
# 功能：对RNA-seq数据进行主成分分析并生成可视化图形
#
# 输入文件格式 (gene.counts):
# Geneid  Chr  Start  End  Strand  Length  C0_1  C0_2  C0_3  C50_1  C50_2  C50_3 ...
# gene1   1    53340  53891  +     552    233   146   195   201    189    264  ...
# gene2   1    54648  55664  -     1017   2     4     8     12     6      3    ...
#
# 输出：
# - PCA散点图，展示样本间的整体表达模式差异
# - 图形包含不同处理组的样本，使用不同颜色区分

# 清理环境并设置语言
rm(list = ls())  
Sys.setenv(LANGUAGE = "en")

# 加载必要的包
library(clusterProfiler)  # 功能富集分析
library(DESeq2)          # 差异表达分析
library(stringr)         # 字符串处理
library(ggplot2)         # 绘图
library(ggpubr)         # 图形组合
library(showtext)        # 字体设置

# 设置字体
font_add("Times_New_Roman", "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf")
showtext_auto()

# 定义数据预处理函数
preprocess_counts <- function(counts_file) {
    # 读取数据
    message("Reading count data...")
    counts <- read.csv(
        counts_file,
        header = TRUE,
        sep = '\t',
        row.names = "Geneid",
        comment.char = '#',
        check.names = FALSE
    )
    
    # 删除基因信息列
    counts <- counts[, -c(1:5)]
    
    # 过滤低表达基因
    message("Filtering low expression genes...")
    counts <- counts[rowSums(counts) > 10, ]
    
    return(counts)
}

# 定义PCA分析函数
run_pca_analysis <- function(counts, sample_info) {
    # 创建DESeq数据集
    message("Creating DESeq dataset...")
    dds <- DESeqDataSetFromMatrix(
        countData = counts,
        colData = sample_info,
        design = ~sample
    )
    
    # 运行DESeq
    message("Running DESeq...")
    dds <- DESeq(dds)
    
    # 方差稳定转换
    message("Performing variance stabilizing transformation...")
    vsd <- vst(dds, blind = FALSE)
    
    # 执行PCA
    message("Running PCA...")
    pca_data <- plotPCA(vsd, intgroup = c('sample'), returnData = TRUE)
    
    return(pca_data)
}

# 定义绘图函数
create_pca_plot <- function(pca_data) {
    # 创建PCA图
    message("Creating PCA plot...")
    pca_plot <- ggplot(pca_data) +
        geom_point(aes(PC1, PC2, color = sample), size = 2) +
        labs(x = "PC1", y = "PC2") +
        theme_light(base_size = 16) +
        theme(
            text = element_text(
                family = "Times_New_Roman",
                face = "bold",
                colour = "black",
                size = 30
            ),
            axis.title = element_text(
                family = "Times_New_Roman",
                face = "bold",
                colour = "black",
                size = 30
            ),
            axis.text = element_text(
                family = "Times_New_Roman",
                face = "bold",
                colour = "black",
                size = 30
            ),
            legend.text = element_text(
                family = "Times_New_Roman",
                face = "bold",
                colour = "black",
                size = 15
            ),
            legend.title = element_text(
                family = "Times_New_Roman",
                face = "bold",
                colour = "black",
                size = 15
            ),
            plot.title = element_text(
                family = "Times_New_Roman",
                face = "bold",
                colour = "black",
                size = 30
            )
        )
    
    return(pca_plot)
}

# 主程序
tryCatch({
    # 预处理数据
    counts <- preprocess_counts('gene.counts')
    
    # 准备样本信息
    samples <- data.frame(
        sampleID = colnames(counts),
        sample = factor(
            c(rep("sample1", 3), rep("sample2", 3), rep("sample3", 3)),
            levels = c("sample1", "sample2", "sample3")
        )
    )
    rownames(samples) <- samples$sampleID
    
    # 运行PCA分析
    pca_results <- run_pca_analysis(counts, samples)
    
    # 创建并保存图形
    pca_plot <- create_pca_plot(pca_results)
    
    # 保存图形
    message("Saving PCA plot...")
    ggsave(
        "pca_plot.png",
        pca_plot,
        width = 10,
        height = 8,
        dpi = 300
    )
    
    message("PCA analysis completed successfully!")
    
}, error = function(e) {
    message("\nError occurred: ", e$message)
}, warning = function(w) {
    message("\nWarning: ", w$message)
}, finally = {
    message("\nScript execution completed.")
})
