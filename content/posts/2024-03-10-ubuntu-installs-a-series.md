---
title: Ubuntu 安装一系列 R 包
date: 2024-03-10
---

Ubuntu 安装 R 包的时候总会有一堆的错误，无非就是缺少一些库，使得 R 包或者 R 包依赖的 R 包安装不上，补上库和 R 包就可以了。

<!--more-->

## languageserver

先安装需要的库：

```bash
sudo apt-get install libxml2-dev openssl libssl-dev libcurl4-openssl-dev
```

然后安装：

```r
install.packages('languageserver')
```

## tidyverse

需要的库：

```bash
sudo apt-get install libfreetype6-dev libharfbuzz-dev libfribidi-dev libfreetype6-dev libpng-dev libtiff5-dev libjpeg-dev libfontconfig1-dev
```

安装依赖的 R 包：

```r
install.packages("sysfonts")
install.packages("textshaping")
install.packages("ragg")
```

最后安装：

```r
install.packages("tidyverse")
```

## ggplot2/ggrepel

直接安装即可：

```r
install.packages("ggrepel")
install.packages("ggplot2")
```

## ChIPseeker&DESeq2

安装库：

```bash
sudo apt-get install libglpk-dev
```

安装依赖 R 包：

```r
install.packages("igraph")

install.packages("devtools")
remotes::install_github('YuLab-SMU/ggtree')
BiocManager::install("enrichplot")
```

然后安装：

```r
devtools::install_github("YuLab-SMU/ChIPseeker")
BiocManager::install("DESeq2")
```

## geneHapR

先安装库和依赖：

```bash
sudo apt-get install libudunits2-dev cmake libgdal-dev
```

再安装依赖 R 包：

```r
BiocManager::install("Gviz")
BiocManager::install("trackViewer")
BiocManager::install(c("Biostrings", "GenomicRanges", "muscle", "IRanges", "rtracklayer", "trackViewer"))
```

然后从 repo 安装：

```r
devtools::install_git("https://gitee.com/zhangrenl/genehapr")
```