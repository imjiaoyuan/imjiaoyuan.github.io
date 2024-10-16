---
title: 一次修改注释文件的经历
date: 2023-10-24
layout: post
---

今天有一位师姐在看到我之前的 [基因家族鉴定](https://yuanj.top/posts/2023-06-01-gene-family-identification.html) 帖子之后，请我帮忙修改一份注释文件，他们找了公司测得的文件，格式与标准的注释文件有所差别，于是我使用 Excel 和 Notepad++对文件的格式进行了修改。

在每一行后面的 ID 信息这一块，有一些符号似乎被转换成网址格式了？（例如网址里的空格会被自动转换成%20）

```txt
Arabis_paniculata_L_1-10k_transcript/0	transdecoder	gene	1	7495	.	+	.	ID=Gene.1::Arabis_paniculata_L_1-10k_transcript/0::g.1;Name=ORF%20type%3Acomplete%20len%3A2361%20(%2B)
```

使用 Notepad++批量替换：

- %20 替换成空格
- %2B 替换成+
- %3A 替换成：

然后在第一列，标准注释文件中是染色体，而这个文件是`Arabis_paniculata_L_1-10k_transcript/0`，使用 Notepad++正则匹配：

```bash
Arabis_paniculata_L_1-10k_transcript/(\d+)
```

然后替换成`($1)`，即替换成正则表达式中括号括起来的部分，这样就会把每一个`Arabis_paniculata_L_1-10k_transcript/0`替换成`0`

转念一想，`Arabis_paniculata_L_1-10k_transcript/`这里最大的数字达到了 9999，染色体怎么会有这么多？而且还有第 0 条？于是我发现，这个文件信息里貌似没有染色体位置信息 ... 于是失败，既然没有染色体位置信息，何谈染色体定位于共线性分析，遂失败。