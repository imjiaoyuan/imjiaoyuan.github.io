# GO/KEGG富集分析气泡图绘制脚本
# 
# 功能：创建GO/KEGG富集分析的气泡图可视化
#
# 输入文件格式 (data.txt):
# Term               Fold.Enrichment  PValue    Counts
# mRNA processing    0.0619          1.19E-58  298
# RNA splicing       0.0557          1.48E-48  268
# ...
#
# 列说明：
# - Term: 富集条目名称
# - Fold.Enrichment: 富集倍数
# - PValue: 显著性P值
# - Counts: 基因数量
#
# 输出：
# - bubble.png: 气泡图，包含富集条目、富集倍数、显著性和基因数量信息

# 清理环境并设置语言
rm(list = ls())  
Sys.setenv(LANGUAGE = "en")

# 加载必要的包
library(stats)
library(base)
library(showtext)
library(dplyr)
library(ggplot2)
library(ggrepel)

# 设置字体
font_add("Times_New_Roman", "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf")
showtext_auto()

# 读取数据
Enriched_data <- read.table(
    './data.txt',
    header = TRUE,
    sep = '\t',
    stringsAsFactors = FALSE
)

# 按P值排序
Enriched_data <- arrange(Enriched_data, Enriched_data[,3])

# 转换Term为因子并反转顺序
Enriched_data$Term <- factor(Enriched_data$Term, levels = rev(Enriched_data$Term))

# 创建主题
mytheme <- theme(
    axis.title = element_text(
        family = "Times_New_Roman", 
        face = "bold", 
        size = 50, 
        colour = "black"
    ),
    axis.text = element_text(
        family = "Times_New_Roman", 
        face = "bold", 
        size = 45, 
        colour = "black"
    ),
    axis.line = element_line(
        size = 0.2, 
        colour = "black"
    ),
    panel.background = element_rect(colour = "black"),
    legend.key = element_blank(),
    legend.title = element_text(
        family = "Times_New_Roman", 
        face = "bold", 
        size = 45
    ),
    legend.text = element_text(
        family = "Times_New_Roman", 
        face = "bold", 
        size = 45
    )
)

# 创建气泡图
p <- ggplot(
    Enriched_data,
    aes(
        x = Fold.Enrichment,
        y = Term, 
        colour = 1*log10(PValue),
        size = Counts
    )
) +
    geom_point() +
    scale_size(range = c(1, 4)) +
    scale_colour_gradient(low = "blue", high = "red") +
    theme_bw() +
    ylab("Terms") +
    xlab("Fold.Enrichment") +
    labs(color = expression(-log[10](PValue))) +
    theme(
        legend.title = element_text(margin = margin(r = 20)),
        axis.title.x = element_text(margin = margin(t = 20))
    ) +
    theme(
        axis.text.x = element_text(
            family = "Times_New_Roman",
            face = "bold",
            colour = "black",
            angle = 0,
            vjust = 1
        )
    )

# 添加主题并绘图
plot <- p + mytheme

# 保存图片
ggsave(
    plot,
    filename = "bubble.png",
    width = 6,
    height = 6,
    dpi = 600
)