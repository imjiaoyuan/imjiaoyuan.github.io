---
title: 使用 HMMER 网页工具进行结构域分析
date: 2023-10-11
---

由于数据库之间的差异，使用 [NCBI CDD Search](https://www.ncbi.nlm.nih.gov/Structure/bwrpsb/bwrpsb.cgi) 搜索结构域有时候并不能满足我们的需要，比如我们通常使用 HMMER 来鉴定同一家族的基因并且需要进行结构域可视化，但 HMMER 所使用的数据都来自 [pfam](http://pfam-legacy.xfam.org/)，它的数据库可能与 NCBI 的不同，因此而造成结果上的差异。

<!--more-->

有的时候这种情况会影响我们后面的研究，于是，使用 [hmmer 网页工具](https://www.ebi.ac.uk/Tools/hmmer/) 来进行结构域分析可能会更好。

打开 [hmmer 网页工具](https://www.ebi.ac.uk/Tools/hmmer/)，还是一样，上传序列，写下邮件地址，然后提交

![](/images/20231011172604.jpg)

完成后会收到邮件

![](/images/20231011172724.jpg)

将邮件末尾的结构域信息保存到文本文件中

![](/images/20231011172858.jpg)

使用 TBtools 的 Visualize Pfam Domain Pattern 工具进行可视化，导入刚刚保存的结构域信息、蛋白序列（前面上传的）和基因 ID 列表，点击 start 出图即可

![](/images/20231011172904.jpg)

保存时建议保存为 svg 格式，更加清晰，也更方便二次修改。