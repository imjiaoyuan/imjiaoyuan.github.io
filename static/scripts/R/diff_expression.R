# 差异表达基因分析脚本
#
# 功能：对TCGA项目的正常组和肿瘤组样本进行差异表达分析
#
# 输入文件格式:
# - normal_file.csv: 正常样本的表达矩阵
# - tumor_file.csv: 肿瘤样本的表达矩阵
# 格式示例:
#           sample1  sample2  sample3
# gene1     10       20       15
# gene2     30       25       35
# ...
#
# 输出:
# - project_deg.csv: 差异分析结果表格
# - project_volcano.png: 火山图
# - project_heatmap.png: 热图(Top 50差异基因)

# 清理环境并设置语言
rm(list = ls())
Sys.setenv(LANGUAGE = "en")

# 加载必要的包
library(edgeR)      # 差异分析
library(ggplot2)    # 绘图
library(pheatmap)   # 热图
library(showtext)   # 字体设置

# 设置字体
font_add("Times_New_Roman", "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf")
showtext_auto()

# 定义差异分析主函数
run_deg = function(normal_file, tumor_file, output_name, output_dir) {
    # 参数说明:
    # normal_file: 正常样本表达矩阵文件路径
    # tumor_file: 肿瘤样本表达矩阵文件路径
    # output_name: 输出文件前缀(项目名)
    # output_dir: 输出目录
    
    # 读取数据
    normal = read.csv(normal_file, row.names = 1)
    tumor = read.csv(tumor_file, row.names = 1)
    
    # 合并数据并整理行名
    merged_data <- merge(normal, tumor, by = 'row.names')
    rownames(merged_data) <- merged_data$Row.names
    merged_data <- merged_data[, -1]
    
    # 设置分组信息
    normal_g = rep("Normal", dim(normal)[2])
    tumor_g = rep("Tumor", dim(tumor)[2])
    group = factor(c(normal_g, tumor_g))
    
    # 创建 DGEList 对象并进行标准化
    y <- DGEList(counts = merged_data, group = group)
    
    # 过滤低表达基因
    keep_exprs <- filterByExpr(y, group = group)
    y <- y[keep_exprs, , keep.lib.sizes = FALSE]
    y <- normLibSizes(y)
    
    # 差异分析
    design <- model.matrix(~group)
    y <- estimateDisp(y, design)
    fit <- glmQLFit(y, design)
    qlf <- glmQLFTest(fit, coef = 2)
    
    # 获取差异分析结果
    diff = topTags(qlf, n = nrow(y), sort.by = 'logFC')
    diff = as.data.frame(diff)
    result = merge(diff, merged_data, by = 'row.names')
    rownames(result) <- result$Row.names
    result <- result[, -1]
    result = result[row.names(diff),]
    
    # 创建火山图主题
    volcano_theme <- theme(
        axis.title = element_text(family = "Times_New_Roman", face = "bold", size = 12),
        axis.text = element_text(family = "Times_New_Roman", size = 10),
        plot.title = element_text(family = "Times_New_Roman", face = "bold", size = 14),
        legend.title = element_text(family = "Times_New_Roman", size = 10),
        legend.text = element_text(family = "Times_New_Roman", size = 9),
        panel.background = element_rect(fill = "white"),
        panel.grid = element_line(color = "grey90")
    )
    
    # 绘制火山图
    volcano_plot <- ggplot(result, aes(x = logFC, y = -log10(FDR))) +
        geom_point(aes(color = abs(logFC) > 1 & FDR < 0.05), size = 1) +
        scale_color_manual(
            values = c("grey60", "red2"),
            labels = c("Non-significant", "Significant"),
            name = "Differential Expression"
        ) +
        theme_minimal() +
        volcano_theme +
        labs(
            title = paste(output_name, "Volcano Plot"),
            x = "log2 Fold Change",
            y = "-log10 FDR"
        )
    
    # 保存火山图
    ggsave(
        file.path(output_dir, paste0(output_name, "_volcano.png")),
        volcano_plot,
        width = 8,
        height = 6,
        dpi = 300
    )
    
    # 准备热图数据
    top_genes <- head(rownames(result[order(result$FDR), ]), 50)
    heatmap_data <- merged_data[top_genes, ]
    heatmap_data <- t(scale(t(heatmap_data)))  # 数据标准化
    
    # 准备热图注释
    annotation_col <- data.frame(
        Group = factor(c(rep("Normal", dim(normal)[2]), rep("Tumor", dim(tumor)[2])))
    )
    rownames(annotation_col) <- colnames(heatmap_data)
    
    # 设置热图颜色
    ann_colors <- list(
        Group = c(Normal = "#3CB371", Tumor = "#CD4F39")
    )
    
    # 绘制热图
    png(
        file.path(output_dir, paste0(output_name, "_heatmap.png")),
        width = 2000,
        height = 3000,
        res = 300
    )
    pheatmap(
        heatmap_data,
        annotation_col = annotation_col,
        annotation_colors = ann_colors,
        show_colnames = FALSE,
        main = paste(output_name, "Top 50 DEGs"),
        fontsize = 8,
        fontfamily = "Times_New_Roman",
        color = colorRampPalette(c("navy", "white", "firebrick3"))(50)
    )
    dev.off()
    
    # 保存差异分析结果
    write.csv(
        result,
        file.path(output_dir, paste0(output_name, "_deg.csv"))
    )
}

# 定义要分析的项目
projects <- c("CHOL", "HNSC")

# 设置输入输出路径
base_dir <- "D:/JiaoYuan"
normal_dir <- file.path(base_dir, "TCGA_NORMAL")
tumor_dir <- file.path(base_dir, "TCGA_TUMOR")
output_dir <- file.path(base_dir, "DEG")

# 创建输出目录
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

# 遍历每个项目进行差异分析
for (project in projects) {
    message(paste("Processing", project))
    
    # 构建文件路径
    normal_file <- file.path(normal_dir, paste0(project, "_normal.csv"))
    tumor_file <- file.path(tumor_dir, paste0(project, "_tumor.csv"))
    
    # 检查输入文件是否存在
    if (!all(file.exists(normal_file, tumor_file))) {
        warning(paste("Missing input files for", project))
        next
    }
    
    # 运行差异分析
    tryCatch({
        run_deg(normal_file, tumor_file, project, output_dir)
        message(paste("Completed", project))
    }, error = function(e) {
        warning(paste("Error processing", project, ":", e$message))
    })
}