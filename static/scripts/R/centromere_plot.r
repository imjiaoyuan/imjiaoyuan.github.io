# 染色体DNA组成和长度可视化脚本
# 
# 本脚本用于绘制染色体的各类DNA分布和长度信息的双向柱状图。
# 上半部分显示以下DNA的堆叠分布：
# - 卫星DNA I (Sat I)
# - 转座子阵列 (TE array)
# - 卫星DNA II (Sat II)
# - 卫星DNA III (Sat III)
# - X染色体着丝粒 (CenX)
# - Y染色体着丝粒 (CenY)
# 下半部分显示染色体的长度。
# 
# 输入文件格式 (centromeric_regions.txt):
# chr    length      SatⅠ    TE array    Sat Ⅱ    Sat Ⅲ    CenX    CenY
# chr01  164654034   713225  293700      5501223  1566652  0       0
# chr02  148119503   683874  163189      3197626  8842096  0       0
# chr03  136070733   2.1     2.8      3.5
# ...
#
# 列说明：
# - chr: 染色体编号
# - length: 染色体长度（bp）
# - SatⅠ: 卫星DNA I的含量（bp）
# - TE array: 转座子阵列的含量（bp）
# - Sat Ⅱ: 卫星DNA II的含量（bp）
# - Sat Ⅲ: 卫星DNA III的含量（bp）
# - CenX: X染色体着丝粒的含量（bp）
# - CenY: Y染色体着丝粒的含量（bp）

# 设置工作目录
setwd("D:/JiaoYuan/saas")

# 加载必要的包
library(ggplot2)
library(dplyr)
library(tidyr)
library(patchwork)

# 读取数据
data <- read.table("centromeric_regions.txt", 
                  header=TRUE,
                  sep="\t",    
                  quote="",    
                  check.names=FALSE,
                  fileEncoding="UTF-8")  

# 检查数据
print("染色体列表：")
print(data$chr)
print("染色体长度：")
print(data$length)

# 检查并过滤数据
# 保留所有染色体，包括X和Y
data <- data %>%
  mutate(chr = factor(chr, levels = unique(chr)))  # 移除过滤，保留所有染色体

# 准备卫星DNA数据
sat_data <- data %>%
  select(chr, `SatⅠ`, `TE array`, `Sat Ⅱ`, `Sat Ⅲ`, `CenX`, `CenY`) %>%
  gather(key="type", value="value", -chr) %>%
  mutate(type = factor(type, levels = c("SatⅠ", "TE array", "Sat Ⅱ", "Sat Ⅲ", "CenX", "CenY")))

# 创建基础主题
base_theme <- theme_bw() +
  theme(
    panel.grid = element_blank(),
    axis.line.y = element_line(color="black"),
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank(),
    panel.border = element_blank(),
    axis.title.x = element_blank()
  )

# 上部分：卫星DNA和着丝粒DNA
p1 <- ggplot(sat_data) +
  geom_col(aes(x=chr, y=value/1e6, fill=type),
          position="stack", width=0.7) +
  scale_fill_manual(
    values=c(
      "SatⅠ" = "#ffbb78",   # 橙色
      "TE array" = "#c5b0d5", # 淡紫色
      "Sat Ⅱ" = "#98df8a",  # 浅绿色
      "Sat Ⅲ" = "#17becf",  # 亮蓝色
      "CenX" = "#ff9896",    # 浅红色
      "CenY" = "#9467bd"     # 深紫色
    ),
    labels = c(
      "SatⅠ" = "Sat I",
      "TE array" = "TE array",
      "Sat Ⅱ" = "Sat II",
      "Sat Ⅲ" = "Sat III",
      "CenX" = "CenX",
      "CenY" = "CenY"
    ),
    breaks = c("SatⅠ", "TE array", "Sat Ⅱ", "Sat Ⅲ", "CenX", "CenY")
  ) +
  scale_y_continuous(
    name = "DNA content (Mb)",
    breaks = seq(0, 30, by=10),
    limits = c(0, 30),
    expand = c(0.02, 0)
  ) +
  scale_x_discrete(expand = c(0.02, 0.02)) +
  base_theme +
  theme(
    legend.position = "right",
    legend.title = element_blank(),
    plot.margin = unit(c(1,1,0,1), "lines"),
    axis.text.x = element_text(angle = 90, hjust = 1, vjust = 0.5)
  )

# 中间部分：染色体标签（不再需要，因为已经在x轴显示）
chr_labels <- ggplot(data) +
  theme_void()

# 检查最大染色体长度
print("最大染色体长度(Mb)：")
print(max(data$length)/1e6)

# 下部分：染色体长度
p2 <- ggplot(data) +
  geom_col(aes(x=chr, y=length/1e6),
          fill="#7f7f7f",
          width=0.7) +
  scale_y_reverse(
    name = "Chromosome length (Mb)",
    breaks = seq(0, 165, by=40),
    limits = c(165, 0),
    expand = c(0.02, 0)
  ) +
  scale_x_discrete(expand = c(0.02, 0.02)) +
  base_theme +
  theme(
    plot.margin = unit(c(0,1,1,1), "lines")
  )  # 移除底部x轴标签显示

# 组合图形
final_plot <- p1 + 
              p2 + 
              plot_layout(ncol=1, heights=c(4, 4))

# 保存图形
ggsave("centromeric_regions_plot.pdf", 
       final_plot, 
       width = 10, 
       height = 8,
       device = cairo_pdf)  # 使用cairo_pdf设备来改善字体渲染 