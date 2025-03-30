# 基因单倍型分析脚本
# 
# 功能：使用geneHapR包分析基因上不同变异位点的线性组合形式(单倍型)，
# 包括启动子、外显子、内含子和终止子区域。
#
# 分析内容：
# 1. 单倍型鉴定和结果汇总
# 2. 单倍型网络分析和可视化
# 3. 地理分布分析
# 4. 连锁不平衡分析
# 5. 表型关联分析
#
# 输入数据要求：
# 1. 基因型数据(必需)：
#    - VCF文件：二代测序变异数据
#    - Hapmap文件：基因芯片数据
#    - Plink文件：map & ped格式
#    - Fasta文件：一代测序数据
#    - 自定义表格：Chr,POS,REF,Alt,INFO等列的变异位点数据
#
# 2. 基因注释(可选)：
#    - GFF/GFF3：数据库下载的标准注释文件
#    - BED6：自定义的基因结构注释
#
# 3. 样本信息(可选)：
#    - 表型数据：用于评估优势单倍型
#    - 地理坐标：用于分析地理分布
#    - 分类信息：用于网络分析分组

# 安装依赖包
if (!requireNamespace("BiocManager", quietly = TRUE)) {
    install.packages("BiocManager")
}

BiocManager::install(c(
    "Biostrings", 
    "GenomicRanges", 
    "muscle", 
    "IRanges", 
    "rtracklayer", 
    "trackViewer"
))

install.packages("geneHapR")

# 加载包
library(geneHapR)

# 设置工作目录
setwd("/home/yuanj/work/Haplotype-analysis/")

# 导入数据
gff <- import_gff("OsGHD7.gff3")                      
bed <- import_bed("12859_2023_5318_MOESM3_ESM.bed6")      
pheno <- import_AccINFO("12859_2023_5318_MOESM4_ESM.tsv") 
AccINFO <- import_AccINFO("12859_2023_5318_MOESM5_ESM.csv", 
                         sep = ",",                      
                         na.strings = "NA")              

# 导入并过滤VCF数据
vcf <- import_vcf("OsGHD7.vcf.gz")
vcf <- filter_vcf(vcf, gff,
                 mode = "both",                       
                 start = start, end = end, Chr = Chr, 
                 type = "CDS", cusTyp = c("CDS"))     

# 基本参数设置
geneID <- "OsGHD7"      
Chr <- "Chr7"           
start <- 9152403        
end <- 9155185          
hapPrefix <- "H"        

# 单倍型鉴定
hapResult <- vcf2hap(vcf, hapPrefix = hapPrefix,
                    hetero_remove = TRUE, 
                    na_drop = TRUE) 

# 结果汇总
hapSummary <- hap_summary(hapResult, hapPrefix = hapPrefix)

# 保存结果
write.hap(hapResult, file = "GeneID.hapResult")
write.hap(hapSummary, file = "GeneID.hapSummary")

# 可视化分析
# 单倍型表格展示
plotHapTable(hapSummary,             
            hapPrefix = hapPrefix,  
            angle = 45,             
            displayIndelSize = 0,   
            title = geneID)         

# 基因模式图展示
displayVarOnGeneModel(gff = gff, hapSummary = hapSummary,
                     startPOS = start-10,
                     endPOS = end+10,
                     CDS_h = 0.05, 
                     fiveUTR_h = 0.25, 
                     threeUTR_h = 0.25,
                     cex = 0.8)

# 单倍型网络分析
hapSummary[hapSummary == "DEL"] = "N"
hapnet <- get_hapNet(hapSummary,                  
                    AccINFO = AccINFO,           
                    groupName = "Subpopulation", 
                    na.label = "Unknown")        

plotHapNet(hapnet,                          
          scale = "log2",                  
          show.mutation = 2,               
          col.link = 2, 
          link.width = 2,    
          main = geneID,                   
          pie.lim = c(0.5, 2),            
          legend_version = 1,              
          labels = TRUE,                      
          legend = c(12,0),                
          cex.legend = 0.6)                

# 地理分布分析
AccINFO$Longitude <- as.numeric(AccINFO$Longitude)
AccINFO$Latitude <- as.numeric(AccINFO$Latitude)
hapDistribution(hapResult,             
               AccINFO = AccINFO,     
               hapNames = c("H001", "H002", "H003"),  
               symbol.lim = c(3, 6),  
               LON.col = "Longitude", 
               LAT.col = "Latitude",  
               legend = "bottomleft", 
               cex.legend = 1,        
               lwd.pie = 0.2,         
               lwd = 1.5,             
               main = geneID)         

# 连锁不平衡分析
plot_LDheatmap(hap = hapResult, 
              add.map = TRUE,  
              gff = gff,       
              Chr = Chr,       
              start = start,   
              end = end)       

# 表型关联分析
hapVsPheno(hap = hapResult,       
          pheno = pheno,         
          hapPrefix = hapPrefix, 
          title = geneID,        
          minAcc = 4,            
          symnum.args = list(    
              cutpoints = c(0, 0.001, 0.01, 0.05, 1), 
              symbols = c("***", "**", "*", "ns")),
          mergeFigs = TRUE)     

# GUI界面启动
startGUI.geneHapR()