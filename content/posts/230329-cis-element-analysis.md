---
title: 顺式作用元件分析
date: 2023-03-29
---

顺式作用元件 (cis-acting element) 存在于基因旁侧序列中能影响基因表达的序列。

<!--more-->

顺式作用元件包括启动子、增强子、调控序列和可诱导元件等，它们的作用是参与基因表达的调控。顺式作用元件本身不编码任何蛋白质，仅仅提供一个作用位点，要与反式作用因子相互作用而起作用。

## 所需工具及文件

Gff3 注释文件、基因组全部序列、TBtools、plantcare 网站

## 提取启动子区域

首先要做的第一步是提取所有基因的 CDS 序列

提取时需要在初始化后将 TBtools 的设置改为如下配置

![](https://images.yuanj.top/blog/20230329211100.png)

然后提取目标基因的启动子序列，打开 TBtools 的 Fasta Extract or Filter，设置好序列文件、输出文件、基因 ID，点击 start 开始

![](https://images.yuanj.top/blog/20230329211136.png)

## 转换大小写

打开 Sequenxe Manipulate 工具，将提取出来的所有序列复制进去，全部转为大写

![](https://images.yuanj.top/blog/20230329211229.png)

新建文本文档保存转换后的序列

## 上传至 plantcare 网站

现在需要打开网站 http://bioinformatics.psb.ugent.be/webtools/plantcare/html/ 将刚刚保存的序列上传进行顺势作用元件预测

![](https://images.yuanj.top/blog/20230329211337.png)

![](https://images.yuanj.top/blog/20230329211353.png)

等待一会后会收到网站发出的一封邮件，下载邮件中的附件然后解压，解压之后得到一个拓展名为 tar 的文件，再进行解压

![](https://images.yuanj.top/blog/20230329211417.png)

## 整理网站返回信息

用 excel 打开解压出来的 tab 文件，此时 excel 中显示的就是这些基因的元件信息

![](https://images.yuanj.top/blog/20230329211509.png)

筛选我们需要的物种，这里我选择了水稻

![](https://images.yuanj.top/blog/20230329211536.png)

删除元件名称、元件序列、增减个数、加/减、物种等我们不需要的信息，然后为了保证最后的图片可看，这里需要扩大一下起始位置，较大的可以减少 20，较小的可以增大 20。并且需要将含有空白信息的项删除，不然 TBtools 会报错。最终整理成如下格式：

![](https://images.yuanj.top/blog/20230329211727.png)

## 新建序列长度文件

下面需要再新建一个关于序列长度的文件，格式如下：

![](https://images.yuanj.top/blog/20230329211747.png)

## 可视化

打开 TBtools 的 Simple BioSequence Viewer 功能，导入长度信息文件和元件信息，点击 start 开始

![](https://images.yuanj.top/blog/20230329211757.png)

最终得到可视化结果

![](https://images.yuanj.top/blog/20230329211815.png)