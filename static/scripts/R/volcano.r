# 火山图绘制脚本
#
# 功能：根据差异表达分析结果绘制火山图，展示基因表达变化的显著性和倍数变化
#
# 输入文件格式 (data.txt):
# 基因ID     baseMean    log2FoldChange    lfcSE    stat    pvalue    padj
# gene1      213.08      -0.159            0.321    -0.496  0.619     1
# gene2      12.85       -0.583            0.848    -0.688  0.491     1
#
# 输出：
# - volcano.png: 火山图
#   - X轴：log2(fold change)，表示表达量变化倍数
#   - Y轴：-log10(p-value)，表示统计显著性
#   - 点的颜色：上调(红色)、下调(蓝色)、无显著变化(灰色)

# 清理环境并设置语言
rm(list = ls())  
Sys.setenv(LANGUAGE = "en")

# 加载必要的包
library(ggplot2)    # 绘图
library(showtext)   # 字体设置

# 设置字体
font_add("Times_New_Roman", "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf")
showtext_auto()

# 定义火山图参数
PVALUE_CUTOFF <- 0.05    # P值显著性阈值
LOGFC_CUTOFF <- 1        # Log2倍数变化阈值
POINT_SIZE <- 3.5        # 点的大小
POINT_ALPHA <- 0.4       # 点的透明度
COLORS <- c(             # 颜色设置
    "Up" = "#ff4757",      # 上调基因-红色
    "Down" = "#546de5",    # 下调基因-蓝色
    "No change" = "#d2dae2" # 无显著变化-灰色
)

# 数据处理函数
process_data <- function(data) {
    # 添加变化类型标记
    data$change <- ifelse(
        data$pvalue < PVALUE_CUTOFF & abs(data$log2FoldChange) >= LOGFC_CUTOFF,
        ifelse(data$log2FoldChange > LOGFC_CUTOFF, 'Up', 'Down'),
        'No change'
    )
    return(data)
}

# 创建火山图函数
create_volcano_plot <- function(data) {
    # 创建基础图形
    p <- ggplot(
        data,
        aes(
            x = log2FoldChange,
            y = -log10(pvalue),
            colour = change
        )
    ) +
        # 添加散点
        geom_point(
            alpha = POINT_ALPHA,
            size = POINT_SIZE
        ) +
        # 设置颜色
        scale_color_manual(values = COLORS) +
        # 添加阈值线
        geom_vline(
            xintercept = c(-LOGFC_CUTOFF, LOGFC_CUTOFF),
            lty = 4,
            col = "black",
            lwd = 0.8
        ) +
        geom_hline(
            yintercept = -log10(PVALUE_CUTOFF),
            lty = 4,
            col = "black",
            lwd = 0.8
        ) +
        # 设置标签
        labs(
            x = "log2(fold change)",
            y = "-log10 (p-value)"
        ) +
        # 设置主题
        theme_bw() +
        theme(
            # 坐标轴标题
            axis.title.x = element_text(
                family = "Times_New_Roman",
                face = "bold",
                colour = "black",
                size = 30
            ),
            axis.title.y = element_text(
                family = "Times_New_Roman",
                face = "bold",
                colour = "black",
                size = 30
            ),
            # 坐标轴刻度
            axis.text = element_text(
                family = "Times_New_Roman",
                face = "bold",
                colour = "black",
                size = 10
            ),
            # 图例设置
            legend.position = "right",
            legend.title = element_blank(),
            legend.text = element_text(
                family = "Times_New_Roman",
                face = "bold",
                colour = "black",
                size = 30
            )
        )
    
    return(p)
}

# 主程序
tryCatch({
    # 读取数据
    message("Reading data...")
    data <- read.table(
        'data.txt',
        header = TRUE,
        sep = '\t',
        check.names = FALSE
    )
    
    # 数据有效性检查
    if (nrow(data) == 0) {
        stop("Empty input file")
    }
    
    # 处理数据
    message("Processing data...")
    data_processed <- process_data(data)
    
    # 创建火山图
    message("Creating volcano plot...")
    volcano_plot <- create_volcano_plot(data_processed)
    
    # 保存图形
    message("Saving plot...")
    ggsave(
        "volcano.png",
        volcano_plot,
        width = 10,
        height = 6,
        dpi = 300
    )
    
    message("Volcano plot created successfully!")
    
}, error = function(e) {
    message("\nError occurred: ", e$message)
}, warning = function(w) {
    message("\nWarning: ", w$message)
}, finally = {
    message("\nScript execution completed.")
})