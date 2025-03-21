# 基因组组装比对错配率分析可视化脚本 (Genome Assembly Mismatch Analysis Plot)
#
# 功能：创建散点图比较两个基因组组装版本的错配率和错配碱基数
# 作者：JiaoYuan
# 日期：2024-03
#
# 输入文件格式示例：
# result_mismatch_t2t.txt / result_mismatch_ars.txt:
# sample  mismatch_bases  error_rate
# S001    156789         0.00156
# S002    167890         0.00167
# S003    145678         0.00145
#
# 列说明：
# - sample: 样本ID
# - mismatch_bases: 错配碱基数量
# - error_rate: 错配率
#
# 输出：
# - 四个PDF格式的散点图，包含：
#   1. error_rate_plot_v1.pdf (配色方案1的错配率图)
#   2. mismatch_bases_plot_v1.pdf (配色方案1的错配碱基数图)
#   3. error_rate_plot_v2.pdf (配色方案2的错配率图)
#   4. mismatch_bases_plot_v2.pdf (配色方案2的错配碱基数图)
#
# 配色方案：
# - 方案1: #17becf (亮蓝), #ffbb78 (橙色)
# - 方案2: #77CE61 (绿色), #FF9326 (深橙)

# 设置工作目录
setwd("D:/JiaoYuan/saas")

# 加载必要的包
library(ggplot2)
library(ggprism)
library(dplyr)

# 读取数据
t2t_data <- read.table("result_mismatch_t2t.txt")
ars_data <- read.table("result_mismatch_ars.txt")

# 设置列名
colnames(t2t_data) <- c("sample", "mismatch_bases", "error_rate")
colnames(ars_data) <- c("sample", "mismatch_bases", "error_rate")

# 添加assembly列以区分数据来源
t2t_data$assembly <- "T2T-cattle1.0"
ars_data$assembly <- "ARS-UCD2.0"

# 合并数据
combined_data <- rbind(t2t_data, ars_data)

# 定义两种配色方案
colors_1 <- c("#17becf", "#ffbb78")
colors_2 <- c("#77CE61", "#FF9326")

# 基础绘图函数
create_plot <- function(data, y_var, y_lab, colors) {
  ggplot(data, aes(x = assembly, y = !!sym(y_var), color = assembly)) +
    # 先画统计线
    stat_summary(fun.data = function(x) {
      r <- quantile(x, probs = c(0.25, 0.5, 0.75))
      names(r) <- c("ymin", "y", "ymax")
      r
    }, geom = "errorbar", width = 0.1, color = "black", size = 0.5) +
    stat_summary(fun = "median", geom = "crossbar", width = 0.1, color = "black", size = 0.3) +
    # 再画散点
    geom_jitter(size = 2, width = 0.15, alpha = 0.7) +
    # 颜色和标签
    scale_color_manual(values = colors) +
    labs(x = "", y = y_lab) +
    # 主题设置
    theme_prism() +
    theme(
      legend.position = "none",
      axis.text.x = element_text(angle = 45, hjust = 1, vjust = 1),
      plot.margin = margin(5, 5, 10, 5),
      axis.title.y = element_text(margin = margin(r = 5)),
      axis.text = element_text(size = 10)
    ) +
    # 大幅减小x轴间距
    scale_x_discrete(expand = c(0.2, 0.6))
}

# 创建四个图
p1_v1 <- create_plot(combined_data, "error_rate", "Error rate", colors_1)
p2_v1 <- create_plot(combined_data, "mismatch_bases", "Number of mismatch bases", colors_1)
p1_v2 <- create_plot(combined_data, "error_rate", "Error rate", colors_2)
p2_v2 <- create_plot(combined_data, "mismatch_bases", "Number of mismatch bases", colors_2)

# 保存图片
ggsave("error_rate_plot_v1.pdf", p1_v1, width = 3, height = 4, device = cairo_pdf)
ggsave("mismatch_bases_plot_v1.pdf", p2_v1, width = 3, height = 4, device = cairo_pdf)
ggsave("error_rate_plot_v2.pdf", p1_v2, width = 3, height = 4, device = cairo_pdf)
ggsave("mismatch_bases_plot_v2.pdf", p2_v2, width = 3, height = 4, device = cairo_pdf)
