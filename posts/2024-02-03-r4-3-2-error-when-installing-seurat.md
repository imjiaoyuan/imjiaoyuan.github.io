---
title: R4.3.2 安装 Seurat 报错
date: 2024-02-03
layout: post
---

今天在 Debian 上安装 Seurat 报错，说是缺少依赖的 R 包，但是安装依赖的两个 R 包又报错。

报错：

```r
ERROR: dependencies ‘igraph’, ‘leiden’ are not available for package ‘Seurat’
* removing ‘/home/yuanj/R/x86_64-pc-linux-gnu-library/4.3/Seurat’

The downloaded source packages are in
	‘/tmp/Rtmp23Tloi/downloaded_packages’
Warning messages:
1: In install.packages("Seurat") :
  installation of package ‘igraph’ had non-zero exit status
2: In install.packages("Seurat") :
  installation of package ‘leiden’ had non-zero exit status
3: In install.packages("Seurat") :
  installation of package ‘Seurat’ had non-zero exit status
```

于是安装依赖 R 包：

```r
install.packages(c("igraph", "leiden"))
```

又报错，报错信息忘记了，问了一下 GPT，补上两个系统的库：

```bash
sudo apt-get install libglpk-dev libxml2-dev
```

再重新安装 igraph 和 leiden，安装完成，报错解决。