# 进化树绘制脚本
#
# 功能：读取Newick格式的进化树文件并生成圆形进化树图
#
# 输入文件格式:
# - tree.nwk: Newick格式的进化树文件
# 示例：
# (A:0.1,B:0.2,(C:0.3,D:0.4):0.5);
#
# 输出：
# - evolutionary_tree.png: 圆形进化树图
#   - 树枝：黑色细线
#   - 标签：斜体Times New Roman字体
#   - 布局：圆形布局

# 清理环境并设置语言
rm(list = ls())  
Sys.setenv(LANGUAGE = "en")

# 加载必要的包
library(dplyr)         # 数据处理
library(ggplot2)       # 基础绘图
library(ggtree)        # 进化树绘制
library(ggtreeExtra)   # 进化树扩展
library(treeio)        # 树文件读取
library(showtext)      # 字体设置

# 设置字体
font_add("Times_New_Roman", "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf")
showtext_auto()

# 定义树的基本参数
TREE_PARAMS <- list(
    layout = "circular",    # 布局类型
    open.angle = 0,        # 开放角度
    branch_color = "black", # 分支颜色
    branch_size = 0.5,     # 分支粗细
    branch_linetype = 1    # 分支线型
)

# 定义标签参数
LABEL_PARAMS <- list(
    align = TRUE,          # 对齐标签
    linetype = 3,         # 标签连接线类型
    linesize = 0.5,       # 标签连接线粗细
    family = "Times_New_Roman", # 字体
    face = "italic",      # 字体样式
    size = 4,             # 字体大小
    color = "black"       # 字体颜色
)

# 读取和处理树文件函数
read_tree_data <- function(file_path) {
    message("Reading tree file...")
    if (!file.exists(file_path)) {
        stop("Tree file not found: ", file_path)
    }
    
    tree_data <- read.tree(file_path)
    tree <- fortify(tree_data)
    return(tree)
}

# 创建基础树图函数
create_base_tree <- function(tree_data) {
    message("Creating base tree...")
    ggtree(
        tree_data,
        mapping = NULL,
        layout = TREE_PARAMS$layout,
        open.angle = TREE_PARAMS$open.angle,
        mrsd = NULL,
        as.Date = FALSE,
        yscale = "none",
        yscale_mapping = NULL,
        ladderize = TRUE,
        right = FALSE,
        branch.length = "branch.length",
        root.position = 0,
        xlim = NULL,
        color = TREE_PARAMS$branch_color,
        size = TREE_PARAMS$branch_size,
        linetype = TREE_PARAMS$branch_linetype
    )
}

# 添加标签函数
add_tree_labels <- function(tree_plot) {
    message("Adding labels...")
    tree_plot +
        geom_tiplab(
            align = LABEL_PARAMS$align,
            linetype = LABEL_PARAMS$linetype,
            linesize = LABEL_PARAMS$linesize,
            family = LABEL_PARAMS$family,
            face = LABEL_PARAMS$face,
            size = LABEL_PARAMS$size,
            color = LABEL_PARAMS$color
        )
}

# 主程序
tryCatch({
    # 读取树文件
    tree_data <- read_tree_data("tree.nwk")
    
    # 创建基础树图
    base_tree <- create_base_tree(tree_data)
    
    # 添加标签
    final_tree <- add_tree_labels(base_tree)
    
    # 保存图形
    message("Saving tree plot...")
    ggsave(
        "evolutionary_tree.png",
        final_tree,
        width = 10,
        height = 10,
        dpi = 300
    )
    
    message("Tree plot created successfully!")
    
}, error = function(e) {
    message("\nError occurred: ", e$message)
}, warning = function(w) {
    message("\nWarning: ", w$message)
}, finally = {
    message("\nScript execution completed.")
})

# 注释掉的其他可选功能
# 如需显示节点标签，取消注释：
# geom_nodelab(mapping = aes(label=node))

# 如需添加分支标签，取消注释并修改参数：
# geom_cladelabel(node=136, label="Euarchotoglires", 
#                align=T, offset=0.32, color="red", barsize=2)
# geom_cladelabel(node=120, label="Afrotheria",
#                align=T, offset=0.32, color="blue", fontsize=6)
# geom_cladelabel(node=122, label="Marsupialia",
#                align=T, offset=0.32, color="green", angle=45)