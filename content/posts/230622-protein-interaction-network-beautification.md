---
title: 蛋白互作网络美化
date: 2023-06-22
---

String 数据库默认的图片并不是太美观，使用 Cytoscape 软件可以对其数据进行一些简单修改并对图片进行美化。

<!--more-->

## 软件安装

首先要安装 Cytoscape，而 Cytoscape 又需要 Java 环境，可以从下面的链接进行下载，先安装 Java，再安装 Cytoscape 即可

Java：https://www.123pan.com/s/JYtA-QeW0v.html

Cytoscape：https://www.123pan.com/s/JYtA-EeW0v.html

## 准备数据

数据还是来自于 [String 数据库](https://cn.string-db.org/cgi/input?sessionId=bT1CE6WmOKVU&input_page_show_search=on)，获得蛋白互作网络之后，以 tsv 格式导出

![](https://images.yuanj.top/blog/20230622085919.png)

## 进行美化

先将数据导入到软件中

![](https://images.yuanj.top/blog/20230622090044.png)

![](https://images.yuanj.top/blog/20230622090204.png)

我们可以先对每个蛋白的形状和字体进行一定的调整，点击左边栏的 style 选项卡，选择 node（node 就是蛋白，edge 就是蛋白之间的连接线），在 shape 栏中选择图形应用，一般的话都是圆形

![](https://images.yuanj.top/blog/20230622090329.png)

选了圆形之后我们发现它变成了椭圆，这实际上是因为软件为了使图形与名称对应，在左侧调整图形的宽度和高度，两个值设为一样的数字就变成圆形了

![](https://images.yuanj.top/blog/20230622090824.png)

高度和宽度的数值大小我们可以先改一个数字，后面把其它属性调整好之后再改

再来调整字体，点击左上方的 proerites，勾选 Label Font Face

![](https://images.yuanj.top/blog/20230622091054.png)

点击 A 图标，选择字体后应用，一般我个人比较喜欢新罗马字体

![](https://images.yuanj.top/blog/20230622091207.png)

现在再调整连接线，切换到 edge 选项卡

![](https://images.yuanj.top/blog/20230622091403.png)

点击 width 这里第二个框，Column 选择 combined_score，Mapping Tyep 选择 Continuous Napping，可以看到右边的图形已经变化了，这是根据蛋白之间作用强度的关系来规定连接线的粗细，但是它貌似太粗了，我们可以调整一下上下限

![](https://images.yuanj.top/blog/20230622091525.png)

双击左边的图形，在弹出的窗口中调整上下限，这时候就根据自身情况进行调整，怎么样好看怎么样来

![](https://images.yuanj.top/blog/20230622091858.png)

我这个图中，蛋白的形状有点大，我将它调整小一点，然后把字体再放大一点

![](https://images.yuanj.top/blog/20230622092111.png)

然后我们可以使用软件自带的一些布局调整蛋白的位置摆放，点击菜单栏中的 Layout，下面有一些可以选择的布局，可以自己调整着试一试

![](https://images.yuanj.top/blog/20230622092229.png)

另外，这里还有一些样式可以参考，不过个人认为不是很好看，所以我就用默认的

![](https://images.yuanj.top/blog/20230622092402.png)

![](https://images.yuanj.top/blog/20230622092414.png)

我们还可以对形状的颜色、蛋白的名称进行调整

调整颜色在左边 Fill color 这一栏，第一个框内是对整体颜色进行调整

![](https://images.yuanj.top/blog/20230622092552.png)

对单独几个蛋白的颜色进行调整的时候，按住 shift 键，再用鼠标左键可以多选蛋白，然后再 Fill color 第三个框内选择颜色确定即可

![](https://images.yuanj.top/blog/20230622092817.png)

## 重命名、添加

在下栏，可以对蛋白进行重命名，选中一个蛋白，在下栏修改名称

![](https://images.yuanj.top/blog/20230622092939.png)

在空白处点击右键，Add 选择 node 可以添加蛋白

![](https://images.yuanj.top/blog/20230622093132.png)

选中刚刚添加的蛋白，点击右键，Add 选择 edge 再选择要与这个蛋白相连接的蛋白可以为此蛋白与其它蛋白添加连接线

![](https://images.yuanj.top/blog/20230622093213.png)

## 导出

点击菜单栏的 File，Export as Image 即可导出图片

![](https://images.yuanj.top/blog/20230622093412.png)
