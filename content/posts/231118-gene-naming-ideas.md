---
title: 基因命名思路
date: 2023-11-18
---

最近在做黑麦草基因的项目，要对一个基因家族进行命名，与一些老师讨论后有了一个大致的思路。

<!--more-->

首先第一种方法是由我自己想的，很简单，就是对基因整体进行一个排序，用 excel 表格排为一个升序列表，这样是按照基因在染色体上的位置和基因 ID 中的数字编码进行排序：

```txt
KYUSt_chr1.6353
KYUSt_chr2.2084
KYUSt_chr2.46575
KYUSt_chr2.49361
KYUSt_chr3.42373
KYUSt_chr3.48134
KYUSt_chr4.26949
KYUSt_chr5.22446
KYUSt_chr5.27891
KYUSt_chr5.34402
KYUSt_chr6.8642
```

根据做的基因染色体定位来看，后面的这些数字也是跟基因在染色体上的位置相关的，但也会有一些基因不是这样的。

问了一些老师，说这样似乎是可以的，在文末注明即可。

第二种方法参考的是华中农业大学的文章 [Integrated Bioinformatics Analyses of PIN1, CKX, and Yield-Related Genes Reveals the Molecular Mechanisms for the Difference of Seed Number Per Pod Between Soybean and Cowpea](https://www.frontiersin.org/articles/10.3389/fpls.2021.749902/full)。

他们在大豆基因家族中加入了拟南芥的同源基因进行进化树分析，然后根据拟南芥所在的亚族或聚类进行命名：

![](https://images.yuanj.top/blog/20231118204673.png)

这种方法就是根据模式植物进行命名，也是很常用的一种方法。

第三种方法便是根据课题组黄老师的建议来做的，做出进化树，然后根据各个基因的亲缘关系来进行命名。而本项目中也使用的是这种方法，为了方便，我用 [iTOL](https://itol.embl.de/) 将进化树做成无根的叶子图，这样的话亲缘关系更加明显，也更方便于命名。

![](https://images.yuanj.top/blog/20231118205289.png)