---
title: 挖掘 TFBS 的利器--DAP-Seq
date: 2024-03-29
---

转录因子是能够特异性地与 DNA 上的顺式作用元件相互作用的蛋白质，它们对基因的转录起到激活或抑制的作用。在植物的生长发育和对逆境的应对中，转录因子扮演着关键的调控角色。转录因子结合位点是转录因子在调节基因表达时与其互作的 DNA 片段，通常位于基因的模板链上，并具有 5 到 20 个碱基对的长度。一个转录因子能够同时调控多个基因，尽管这些基因的 TFBS 在序列上保持一定的保守性，但也存在差异。

<!--more-->

在基因组学和表观遗传学的研究中，识别和分析 TFBS 一直是研究的热点。虽然传统的染色质免疫共沉淀测序（ChIP-seq）方法在高质量抗体的条件下能有效鉴定 TFBS，但制备高质量抗体常常具有挑战性，这限制了 ChIP-seq 技术的广泛应用。

2016 年 5 月，美国 Salk 研究所的研究者在《Cell》期刊上发表了题为 [《Cistrome and Epicistrome Features Shape the Regulatory DNA Landscape》](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4907330/) 的研究论文。该研究介绍了一种名为 DAP-Seq（DNA 亲和纯化测序）的技术，该技术能迅速描绘出蛋白质结合的靶向 DNA 区域的图谱，即顺反组（cistrome）中的蛋白质结合区域。为了深入探究生长发育、行为和疾病的复杂转录调控网络，构建完整的顺反组和表观组图谱（epicistrome maps）至关重要。

DAP-Seq 技术结合了蛋白质的体外表达和高通量测序，无需为每个转录因子制备特异性抗体。因此，它具备快速、高通量和成本效益的特点，并且比 ChIP-seq 技术更容易扩展。该方法适用于大部分植物，为科学家提供了一种研究调控序列中的遗传或表观遗传变异如何影响植物性状和机制的途径。

## DAP-seq 实验原理

体外表达的蛋白和 DNA 进行亲和纯化，将与蛋白结合的 DNA 洗脱后进行高通量测序。其基本过程是将编码转录因子的 CDS 序列构建到含有亲和标签（Halo-Tag）的载体中，构建蛋白表达载体，进行体外蛋白表达，形成转录因子和亲和标签的融合蛋白；提取样品的基因组 DNA，构建 DNA 文库，然后将体外表达的带有亲和标签的转录因子和 DNA 文库进行结合，随后把结合的 DNA 洗脱后上机测序。

!![](https://images.yuanj.top/202403301006664.png)

## DAP-seq 实验流程

主要步骤包括 DNA 文库构建、蛋白表达、蛋白与文库的结合反应、文库 PCR 加接头及定量检测、上机测序、生信分析等。

- 文库构建与基因组 DNA 提取：从组织材料中提取全基因组 DNA 后，对 DNA 进行片段化处理，接着，将这些片段化的 DNA 连接到基于 Illumina 的测序接头上，以此构建基因组 DNA 文库。这一步骤是为了后续进行蛋白质结合和测序分析
- 蛋白表达与亲和标签构建：为体外表达特定的转录因子，将该转录因子的编码区序列（CDS）克隆入带有 Halo Tag 的表达载体中，通过例如使用麦胚系统等蛋白质表达流程，生产出带有 Halo Tag 的转录因子融合蛋白，便于后续的亲和纯化
- 亲和纯化与结合实验：将体外表达并纯化得到的转录因子-Halo Tag 融合蛋白与基因组 DNA 文库共孵育，利用融合蛋白的特异性结合能力与基因组 DNA 上的特定序列结合，随后，使用 Halo Tag 特异性磁珠对蛋白-DNA 复合物进行亲和纯化，并通过洗涤步骤去除非特异性结合的物质，从而获得纯净的目的蛋白-DNA 复合物
- PCR 扩增与测序准备：对纯化后的 DNA 片段进行 PCR 扩增，并添加必要的接头序列，以便后续上机测序
- 测序与数据分析：对经过 PCR 扩增的 DNA 片段进行 Illumina 测序，测序完成后的序列读数与参考基因组比对分析，以此确定转录因子的具体结合位点，进一步揭示其在基因组中的调控功能

!![](https://images.yuanj.top/202403301008921.png)

## 麦胚无细胞蛋白表达系统

DAP-seq 技术中，常用的体外蛋白表达方法是小麦胚芽无细胞蛋白表达系统（Wheat germ cell-free protein synthesis system, WGCF）。该系统基于外源 DNA 或 mRNA 模板，在细胞提取物提供的细胞器和多种酶的协同作用下，通过添加氨基酸、T7 聚合酶及能量再生物质，实现蛋白质的体外合成。这些细胞提取物可来源于多种细胞类型，如大肠杆菌、小麦胚芽、兔网织红细胞、酵母和昆虫细胞等。与传统的细胞内蛋白表达系统相比，无细胞蛋白表达系统显示出多项优势：蛋白质表达快速且准确，表达与修饰过程易于调控，且不受细胞生长代谢的干扰。此外，该系统还能合成具有细胞毒性、低丰度或含有非天然氨基酸的特殊蛋白质。

小麦胚芽（麦胚）是小麦籽粒中生命活动最为活跃的部分，它拥有蛋白质合成所需的全套要素，包括合成场所、蛋白质因子以及必要的酶系。因此，科学家们利用小麦胚芽建立了无细胞蛋白表达系统。相较于大肠杆菌无细胞系统，WGCF 更适合表达真核基因，能够高效地体外合成复杂的真核蛋白，并确保其正确折叠。

!![](https://images.yuanj.top/202403301028671.png)

## 适用范围

- 抗体难以获得的样本——有些物种（尤其是植物）中的转录因子没有对应的 ChIP 级别抗体或者没有成熟的转基因体系无法使用标签抗体，而自制抗体周期较长且难度较大
- 染色质提取困难的样本——有些植物的果实、花、茶叶等糖酚含量较高，提取染色质难度较大
- 蛋白表达丰度低的样本——植物中的转录因子表达微弱且存在时空表达特性

## DAP-seq 的优缺点

优点：

- 磁珠富集方法相较于传统的免疫共沉淀（IP）实验（依赖抗原-抗体反应）更为简便，因此更适合进行大规模的应用
- 无需使用抗体，便能开展转录因子结合位点的研究。这对于非模式物种的研究来说，是一个显著的优势
- 尽管这是一项体外实验，但它能够部分地保留 DNA 甲基化等表观遗传修饰对转录因子结合的影响

缺点：

- 实验操作失误，可以通过优化实验步骤来降低失误率
- 蛋白体外表达困难，编码基因过长导致蛋白难以体外表达，可能需要借助分子生物学技术来解决
- TF 蛋白在体外无法正常工作，可能是因为缺乏必要的配体蛋白协助或蛋白质无法正确折叠形成活性结构，针对这一问题，可以通过筛选或工程改造 TF 蛋白，以提高其在体外环境下的稳定性与功能性
- 体外实验的局限性，无法研究核小体和组蛋白修饰的影响，由于核小体在体外容易解离，DAP-seq 技术无法有效检测到这些结构对 TF 结合的影响，这限制了 DAP-seq 在某些表观遗传学研究中的应用

## 参考资料

- [一文搞懂 DAP-seq 技术实验流程和原理](https://zhuanlan.zhihu.com/p/628437832)
- [鉴定转录因子结合位点的新技术——DAP-seq](https://mp.weixin.qq.com/s/zPmljYi99-duOeyRS-3ONQ)
- [Mapping genome-wide transcription-factor binding sites using DAP-seq](https://www.nature.com/articles/nprot.2017.055)
- [Cistrome and Epicistrome Features Shape the Regulatory DNA Landscape](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4907330/)