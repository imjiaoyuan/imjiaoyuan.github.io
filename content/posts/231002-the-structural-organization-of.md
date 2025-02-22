---
title: 蛋白质的结构组织层次
date: 2023-10-02
---

我们知道蛋白质是生命活动的主要承担者，而结构往往决定着功能，因此对蛋白质的研究具有十分重要的意义，不仅有助于我们了解蛋白质如何行使其生物学功能，也可以有助于我们发现功能未知或者新发现的蛋白质。最开始丹麦科学家 Linderstram 将蛋白质分子划分为一级、二级和三级结构，随后英国的 Bernal 增加了四级结构来命名蛋白质结构，但是随着科学不断进步，超二级结构、结构域等相继被发现，这预示着蛋白质具有丰富又复杂结构层次。

<!--more-->

## 一级结构（primary structure）

蛋白质的一级结构就是指氨基酸残基在肽链上的排列顺序，也就是蛋白质的序列，例如下面的黑麦草中的一个基因的蛋白一级结构

```txt
>KYUSt_chr1.28019
MHASVRLLRRLSSSSSPRSLRRLPFHPSPLPSPHPLPLPILRTRAPLPRLAGRRFSTISCASTPSLRLGECGALGTPAIPEVEKSEGEEEVDSLAARHDTDAFAAVELALDSVVKVFTVSSGPNYFLPWQNKSQRESMGSGFVISGRRIITNAHVVADHTFVLVRKHGSPTKYKAEVQAVGHECDLALLTVESEEFWEGMNSLDLGDIPFLQEAVAVVGYPQGGDNISVTKGVVSRVEPTQYAHGATQLMAIQIDAAINPGNSGGPAIMGDKVAGVAFQNLSGAENIGYIIPVPIINRFISGVEESGKYSGFCSLGISCQATENIQIRECFGMRPEMTGVLVSRINPLSDAYKVLKKDDILLEFDGVPIANDGTVPFRNRERITFDHLVSMKKPEETSVIKVLRDGKEHELTVTLRPLQPLVPVHQFDKVPSYYIFAGFVFIPLSQPYLHEFGEDWYNTSPRRLCERALRELPKKAGQQLVILSQVLMDDINVGYERLAELQVKKVNGVEVENLKHLCSIVEGCTEENLRFDLDDERVIVLKFQNAKLATSRILKRHRIPSAMSNDLFDEQGSNDAEGRGLPGALHWLRRLLFG
```

蛋白质的一级结构是后面所有高级结构的基础，也是决定更高层结构的主要因素。天然蛋白质中常见的氨基酸大概有 20 种，这些氨基酸个体通过肽键共价结合。如果两个不同的蛋白质具有相似的一级结构，那么我们可以称这两个蛋白质彼此同源（homology）。

## 二级结构（secondary structure）

蛋白质的二级结构指多肽链的主链原子在氢键作用下沿一维方向排列成具有周期性的结构构象，这是多肽链局部的空间（结构）构象。主要有α螺旋、β折叠、β转角、无规则卷曲等形式。

### α螺旋（α-helix）

蛋白质中最常见、最典型、含量最丰富的结构元件，是一种重复性结构。由于肽链中的全部肽键都可形成氢键，故α-螺旋十分稳定。

其结构特征为：
- 主链骨架围绕中心轴形成右手结构
- 螺旋每上升一圈为 3.6 个氨基酸残基，螺距为 0.54nm
- 相邻螺旋圈之间形成氢键
- 侧链基团位于螺旋外侧

不利于α螺旋形成的原因有：
- 侧链基团存在较大的氨基酸残基
- 连续存在带相同电荷的氨基酸残基
- 存在脯氨酸残基

![](https://images.yuanj.top/blog/20231002141045.png)

### β折叠（β-pleated sheet）

折叠一般有两种形式，一种为平行式，另一种自然为反平行式。两者的区别就如字面意思一样，平行β折叠即相邻肽链是同向的，反平行式为逆向的。

其结构特征为：
- 若干条肽链或肽段平行或者反平行排列成片
- 所有肽键的 C=O 和 N-H 形成链间氢键
- 侧链基团分别交替位于片层的上、下方

![](https://images.yuanj.top/blog/20231002141564.png)

### β转角（β-turn）

通常发生在多肽链 180°回折时的转角上，通常由 4 个氨基酸残基构成，借助第一和第四残基之间形成氢键，从而形成一个紧密的环。已经发现的蛋白质的抗体识别、磷酸化、糖基化和羟基化位点经常出现在转角和紧靠转交。

![](https://images.yuanj.top/blog/20231002141734.png)

### 无规卷曲（random coli）

无规卷曲就是指主链骨架无规律排列形成的构象，也泛指那些不能归入明确的二级结构的多肽区域。常出现在α螺旋与α螺旋、α螺旋与β折叠、β折叠与β折叠之间。

![](https://images.yuanj.top/blog/20231002142045.png)

### 二级结构预测

下面的三个网站都可以用于蛋白质二级结构预测

- [Psipred](http://bioinf.cs.ucl.ac.uk/psipred/)
- [Novopro](https://www.novopro.cn/tools/secondary-structure-prediction.html)
- [Prabi](https://npsa-pbil.ibcp.fr/cgi-bin/npsa_automat.pl?page=npsa_sopma.html)

以 [Novopro](https://www.novopro.cn/tools/secondary-structure-prediction.html) 网站为例，上传前面所提到的那个黑麦草的序列，得到下面的结果

![](https://images.yuanj.top/blog/20231002142555.png)

输出结果中，粉色块代表α螺旋，白色块代表卷曲，黄色块代表β折叠。还有一个更加形象的图：

![](https://images.yuanj.top/blog/20231002142971.png)

## 超二级结构和结构域

超二级结构（supersecondary structure）和（domain）是介于二级和三级结构之间的空间构象。

超二级结构为那些相邻的二级结构单元体组合在一起，排列形成具有规则的、能够在空间结构上辨识的二级结构组合体，同时又可以充当三级结构的功能部件，常见的形式由αα、ββ、βαβ等。

![](https://images.yuanj.top/blog/20231002143293.png)

结构域就是在超二级结构的基础上形成的三维局部折叠区域，通常相对独立并且具有一定的生物学功能。一个较大的蛋白质分子通常具有多个结构域。

此外我们常说的模体（motif）或者模序，它是结构域的亚单位，长度从几个氨基酸残基到几十个氨基酸残基不等，相当于超二级结构，一般为α螺旋、β折叠和环（loop）。

我们通常在基因家族鉴定中会做 domain 分析和 motif 分析实则就是将其可视化，更便于查看，可以通过 [NCBI CDD tool](https://www.ncbi.nlm.nih.gov/Structure/bwrpsb/bwrpsb.cgi) 搜索结构域，使用 [MEME 网站](https://meme-suite.org/meme/tools/meme) 查询 motif。

另外，如果使用 hmmer 做基因家族成员鉴定的话，也是通过结构域进行建模和搜索，最终初步确定家族成员的。

## 三级结构（tertiary structure）

三级结构就是指整条多肽链的三维结构，这就包括了主链骨架以及侧链在内的所有原子的空间结构。它是在二级结构的基础上进一步盘旋、折叠形成的具有一定规律的三维结构。三级结构主要通过氨基酸侧链间的疏水相互作用、氢键、范德华力、静电相互作用等来维持。假设一个蛋白质仅由一条多肽链构成，那么三级结构就为它的最高结构层次。

例如血红蛋白，由四个子单元合成的一个蛋白质

![](https://images.yuanj.top/blog/20231002144330.png)

三级结构的预测可以使用 [Swiss-model](https://swissmodel.expasy.org/)，还是使用前面的黑麦草基因为例，可以自己找到与目标序列同源的已知结构作为模板（目标序列与模板序列的一致度要 ≥ 30%）建模或者直接使用模板，时间可能会比较长，留下邮箱，完成后会发送邮件通知。

![](https://images.yuanj.top/blog/20231002144772.png)

![](https://images.yuanj.top/blog/20231002152543.png)

可以滑动查看、放大查看或者对其进行一些编辑。

![](https://images.yuanj.top/blog/20231002152690.png)

## 四级结构（Quaternary structure）

在生物体内有许多蛋白质含有 2 条或 2 条以上多肽链，才能全面地执行功能。每一条多肽链都有其完整的三级结构，称为亚基（subunit），亚基与亚基之间呈特定的三维空间分布，并以非共价键相链接，这种蛋白质分子中各亚基的空间排布及亚基接触部位的布局和相互作用，即寡聚蛋白中各亚基的空间排布，称为蛋白质的四级结构（Quaternary structure）。

## 参考资料

- [百度百科](https://baike.baidu.com/#home)
- [如何预测蛋白质三维结构（SWISS-MODEL）](https://zhuanlan.zhihu.com/p/148266792)
- [什么是蛋白质的一级结构，以胰岛素为例，描述其结构特征？](https://www.zhihu.com/question/436969178#:~:text=%E5%86%B3%E5%AE%9A%E8%9B%8B%E7%99%BD%E8%B4%A8%E4%B8%80%E7%BA%A7%E7%BB%93%E6%9E%84%E7%9A%84%E4%B8%BB%E8%A6%81%E5%8C%96%E5%AD%A6%E9%94%AE%E6%98%AF%E8%82%BD%E9%94%AE%EF%BC%8C%E5%8F%A6%E5%A4%96%E8%BF%98%E6%9C%89%E4%BA%8C%E7%A1%AB%E9%94%AE%E3%80%82%20%E4%B8%80%E7%BA%A7%E7%BB%93%E6%9E%84%E6%98%AF%E8%9B%8B%E7%99%BD%E8%B4%A8%E7%A9%BA%E9%97%B4%E6%9E%84%E8%B1%A1%E5%92%8C%E7%94%9F%E7%89%A9%E7%89%B9%E5%BC%82%E6%80%A7%E7%9A%84%E5%9F%BA%E7%A1%80%E3%80%82%20%E4%B8%8A%E5%9B%BE%E4%B8%BA%E4%BA%BA%E8%83%B0%E5%B2%9B%E7%B4%A0%E7%9A%84%E4%B8%80%E7%BA%A7%E7%BB%93%E6%9E%84%E5%9B%BE%EF%BC%8C%E5%85%B6%E4%B8%ADA%E9%93%BE21%E4%B8%AA%E6%B0%A8%E5%9F%BA%E9%85%B8%EF%BC%8CB%E9%93%BE30%E4%B8%AA%E6%B0%A8%E5%9F%BA%E9%85%B8%EF%BC%8CA%E3%80%81B%E9%93%BE%E4%B9%8B%E9%97%B4%E5%AD%98%E5%9C%A8%E4%B8%A4%E4%B8%AA%E4%BA%8C%E7%A1%AB%E9%94%AE%EF%BC%8CA%E9%93%BE%E4%B8%8A%E8%BF%98%E8%A6%81%E4%B8%80%E4%B8%AA%E4%BA%8C%E7%A1%AB%E9%94%AE%EF%BC%8C%E8%BF%99%E4%BA%9B%E6%9E%84%E6%88%90%E4%BA%86%E8%83%B0%E5%B2%9B%E7%B4%A0%E7%9A%84%E4%B8%80%E7%BA%A7%E7%BB%93%E6%9E%84%E3%80%82,%E5%8F%91%E5%B8%83%E4%BA%8E%202020-12-28%2018%3A40)

- [如何理解未折叠蛋白反应在细胞内充当的「质量控制系统」角色？](https://www.zhihu.com/question/35989229)
- [蛋白质的结构组织层次](https://zhuanlan.zhihu.com/p/476864096)