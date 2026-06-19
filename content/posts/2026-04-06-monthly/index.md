---
title: 春风解客愁
date: 2026-04-06
---

本篇是对 2026 年 3 月至 4 月的记录与思考。

**撑着油纸伞，独自**
**彷徨在悠长、悠长**
**又寂寥的雨巷，**
**我希望飘过，**
**一个丁香一样的，**
**结着愁怨的姑娘。**

彭州站的夜晚，周围一片漆黑，只有温室里的暖光灯，在给杨树补充光照的同时也给暗夜里的精灵带来一丝明亮。最近总是在出野外，去彭州、去峨眉山，虽然路途上比较累，但是沿途看到的风景甚是抚慰人心。

![](https://static.jiaoyuan.org/blog/images/c2210a6d.webp)

![](https://static.jiaoyuan.org/blog/images/76ad8afc.webp)

三月的成都终于迎来了朝气蓬勃的春天，天空中温暖的阳光屡次照射在大地上，仿佛天色也知晓了春天的到来，想给这片土地上的花草和人们多一些希望，山上花朵竞相绽放，想要展现自己迷人的姿态。同时也宣告着寒冷阴郁的冬天暂时告一段落。成都的人们也争先恐后地享受这来之不易的暖春，想在寒冬告别之后，盛夏来临之前，紧紧抓住这一段宜人的时节。

![](https://static.jiaoyuan.org/blog/images/bc1c4a43.webp)

## MCP、Agent、Skills

最近 Agent 和 Skill 很火，你可能想问，这些都是什么？去年老听到的 MCP 又是什么意思？下面听我给你慢慢道来。

MCP 全称 Model Context Protocol，由 Anthropic 于 2024 年 11 月发布并开源，目前已捐赠给 Linux 基金会旗下的 Agentic AI Foundation（AAIF） 进行中立治理。MCP 是大语言模型与外部工具之间的标准化对接协议。可以这样设想，你开了一家公司，你作为老板肯定需要安排手下人去干活，但是你招的这些人来自不同的地方，有四川人、有甘肃人、有东北人、有广东人、有福建人，他们说的都是不同的方言，你要向他们发号施令，但是他们说不同的方言，像什么四川话、粤语啥的，你总不能把这些方言全部学会吧？于是乎，普通话来了，你不需要学四川话，也不需要学粤语，统一用普通话去和他们交流，这样就方便许多了吧。这里你就是 LLM，这些员工就是外部工具，而普通话就是 MCP。那 Agent 和 Skills 呢？Agent Skills 是由 Anthropic 原创、现已开放为行业标准的知识与能力打包格式，官方规范发布于 agentskills.io，代码托管于 [Agent Skills](https://github.com/agentskills/agentskills) 仓库。还是一样的例子，你的公司做大做强了，你不可能什么事情都一一去告诉他们怎么做，所以你把公司分成了几个部门，比如策划部、研发部、市场部等，并且任命了一个总经理，现在你要做一个产品，你告诉总经理你的大概意图，比如你说你要做一个送外卖的 APP，总经理思考了一下要怎么做，然后告诉市场部去调研现有 APP 的功能、优缺点等，策划部根据市场部的调研结果来设计 APP 的功能、界面要求等，将报告交给研发部，研发部根据要求开始开发 APP。这个场景中，总经理就是 Agent，相当于大脑，他只负责拆解任务并且通过普通话（MCP）向下级不同部门下达任务，不同的部门根据自己的职能去做不同的事情，这个就是 Skills。

切换到现实里 Agent 的使用也是一样的，我们只需要告诉 Agent 我们要做什么，我们有什么要求，Agent 会拆解任务，然后调用不同的 Skills 去执行任务。目前已采用 Agent Skills 标准的工具包括：Claude Code、OpenClaw、OpenCode、Cursor、VS Code、GitHub Copilot、OpenAI Codex、Gemini CLI、Amp、goose、Letta、Roo Code、Mistral Vibe、Manus 等，越来越多。

最近我也在用 Agent 了，我用 copilot-cli 将之前整理的一些 Python 分析脚本整理成一个标准的 pip 库，这样就可以直接安装然后通过命令行调用，不需要再通过路径去调用了，基本上几轮对话就可以敲定方案，然后 AI 自动化完成编码和打包测试。

![](https://static.jiaoyuan.org/blog/images/d577c311.webp)

用了 Agent 感觉就是纯让 AI 去写代码了，不需要自己再编辑了，而且现在的 Agent 也聪明了不少，体验还是比以前 cursor 之类的 AI 编辑器好很多。

此外，Agent 也不仅仅是在开发方面了，最近《Nature Methods》发布了一篇非常值得关注的工作：[CellVoyager: AI CompBio agent generates new insights by autonomously analyzing biological data](https://www.nature.com/articles/s41592-026-03029-6)。只需要输入单细胞数据和相关背景说明，它就会全自动探索。首先会结合背景自主提出新假设、规划步骤并生成代码，且自带“自我反思”机制提前排查逻辑错误；然后在专用的编程环境中运行代码，遇到报错会自动尝试修复，如果代码运行成功，生成数据图表，它就会调用视觉大模型识别阅读图像，并据此思考下一步该怎么深入挖掘，如此自动连贯推演多步（单次约 15 到 30 分钟）；最终，会整理交出一份包含所有代码、图表和详细文字解释的完整分析报告，人类只需审查报告，并用大白话对其提出修改意见，还可以继续调整优化。

**由此可见，现在编码工作的重心在逐渐从写代码向产品设计倾斜了。**

还有一件事情，前两天阿里通义千问发布了 qwen 3.6 plus，国产终于有了首个原生多模态+1M 上下文的模型，至于什么评分啥的就不说了，好歹是有了很大进步。

## Linux 桌面现状

笔记本装了 ArchLinux 这也已经小一年了，说下感受吧，还是老样子，该夸夸，该喷喷。

首先夸一下：

- Linux 桌面在写代码跑分析这方面自然没的说，那比 Windows 好了不止一星半点，尤其现在跑 Agent，Linux 下应该是最完美的，目前还没遇到什么不兼容的。Bash 比 PS 好用太多，也不用关心反斜杠和编码的问题。
- docker 和 k8s 已经是现代软件部署的事实标准了，windows 怎么用？别和我说 docker for windows。
- 不需要强行吞下微软塞的💩，Windows11 里面那都整了些啥 ... Linux 里你想干嘛就干嘛没人管你。
- 可以完全自定义，你喜欢什么样的桌面就有什么样的，实在不行你也可以自己用窗口管理器或者平铺管理器加点组件自己创造一个。
- 最大程度可控，微信爱扫盘？那就给你套上 bwrap。
- 更加简洁，更快，系统资源利用更有效率。
- dae、awk、Bash 这样优秀的工具很多。
- 只要你不想，系统永远不会自动更新。
- 远离国产毒瘤，你的电脑永远不会弹出 本次开机打败了全国 xx%的人 xx 新闻 一刀 999 之类的东西。
- I use Arch BTW

当然，喷，也是有必要的：

- 虽然提供了很多选项，但是各家应用和服务割裂比较严重，X11 兼容性好、稳定，但是不支持高分屏；Wayland 流畅，是新一代协议，但是很多桌面环境还没有正式支持（cinnamon 和 xfce4）。Plasma 和 lxqt 使用 Qt 界面，GNOME 系使用 GTK 界面，很多软件也都是不同的技术栈，所以在统一样式等方面还是有问题 ...
- 桌面软件生态还是不够，不过感谢信创，一些必须的国产软件在 Linux 算是比较好用的状态了（点名腾讯）。
- 运维门槛更高，毕竟没有人连 Windows 都不会用。
- 大部分相关资料都是英文，不要尝试在简中圈内找到答案，这也是一种门槛。
- 打游戏不友好，不过现在有 steam 的 proton 加持，常见游戏已经没什么问题，当然，腾讯的这些国产游戏除外。
- 细节上的小问题较多，并且不知道什么时候能修，用了开源软件，没人会为此必须负责。

本科的时候我一直用 GNOME，那时候不用滚动发行版，所以也觉得还好，现在用 Arch，动不动更新就会掉插件，比较难受。后来换了 cinnamon，简洁稳定且好用，强烈安利，但是现在还没有正式支持 Wayland，所以对高分屏不太友好。现在我一直用 KDE Plasma，已经没有换的欲望了。之前尝试了平铺桌面 hyprland 和 niri，配置起来实在折腾，而且有时候也想用鼠标点点点，遂弃用。还尝试了 labwc，是根据 openbox 二次开发的 Wayland 版，但是触控板啥的支持不太好，遂弃用。

现在用 KDE Plasma，既可以使用鼠标操作，也可以用触控板代替鼠标，实在香。

## 心理学治不了时代的病

读自太隐的文章 [心理学治不了时代的病](https://wangyurui.com/posts/xin-li-xue-zhi-bu-liao-shi-dai-de-bing-3c3e340a)，摘抄一段个人比较喜欢的：

> 所以，很多人说自己倒霉啊等等的时候，真的是在抱怨自己的运气吗？
>
> 并不是。
>
> 其实人们的本质上是在说，这套游戏规则本身就对我不利，可所有人都在告诉我是我玩得不好。换句话说，就是把一个本该追问社会的问题，变成了一个让个体自己消化的心理调节问题。
>
> 这的确是我们学习、认知及应用心理学时候，首先要搞清楚的事情。这也是开头所说的“社会问题心理化”最危险的地方。只要你认为是自己的心理问题，那么你就会把所有力气花在跟自己较劲上，再也没有精力去追问那些真正应该被追问的事情。这就让心理学就从一种帮助工具，变成了一种让人认命的话术。
>
> 当然，话说到这里，也必须诚实地面对一个反方向的问题。如果说“把所有问题都归结为个人心理”是一种危险的简化，那么“把所有问题都推给社会结构”同样是另一种简化，也会变成另一种逃避。
>
> 所以我要说的不是“全是社会的错”，而是在一个不断把社会结构的矛盾伪装成个人心理问题的环境中，我们首先要具有区分两者的能力。哪些痛苦来自自己的选择和习惯，哪些痛苦来自我无法左右的外部条件，这条线我们必须要搞清楚，如果画不清这条线，我们无论往哪个方向偏，都会让人陷入另一种形式的陷阱中。

## Vibe Coding

- 此前我用 AI 写了个简单的 RSS 页面 [feeds](https://github.com/imjiaoyuan/feeds)，使用 GitHub actions 定时运行 Python 脚本抓取 RSS 然后发送到邮箱，后来觉得天天收邮件有点烦，改成写入网页了，使用 GitHub pages 部署。
- 我一直比较喜欢看小说，暑假的时候写了 [books](https://github.com/imjiaoyuan/books)，也是使用 Python 将 epub 转为 html 然后整理部署到 GitHub pages，使用浏览器的记住阅读进度功能就可以实现看书了，用了几个月感觉还是很舒服，想看什么自己找资源就行，并且我还写了编辑书名、目录和压缩 epub 的功能，后面也会重构为 pip 库，完善一下功能，使用起来更舒服。
- 我将一些常用的生信脚本等整理了起来放在了 GitHub 仓库 [jutils](https://github.com/imjiaoyuan/jutils)，并且使用 Agent 重构为了 pip 库，后面也会不断完善。

## 文章

- [你不知道的大模型训练：原理、路径与新实践](https://tw93.fun/2026-04-03/llm.html)
- [AI 会成为下一代的书、歌和海报吗？](https://manateelazycat.github.io/2026/03/25/ai-book-song-poster/)
- [杀死那个手工程序员](https://tw93.fun/2026-03-30/kill.html)
- [月刊（第 34 期）：创造的快乐](https://ursb.me/posts/weekly-34/)
- [AI 干活的三件套：CLI、MCP 和 Skill 到底是什么？](https://blog.devtang.com/2026/04/03/cli-mcp-skill/)

## GitHub

- zou-group/CellVoyager: (No description provided)
- agentskills/agentskills: Specification and documentation for Agent Skills
- CherryHQ/cherry-studio: AI productivity studio with smart chat, autonomous agents, and 300+ assistants. Unified access to frontier LLMs
- langgenius/dify: Production-ready platform for agentic workflow development.
- nanbingxyz/5ire: 5ire is a cross-platform desktop AI assistant, MCP client. It compatible with major service providers, supports local knowledge base and tools via model context protocol servers .
- manateelazycat/cctui: 真正好用的命令行 AI 供应商切换程序
- dreddnafious/thereisnospoon: A machine learning primer built from first principles. For engineers who want to reason about ML systems the way they reason about software systems.
- mylinuxforwork/dotfiles: The ML4W OS - Dotfiles for Hyprland - An advanced and full-featured configuration for the dynamic tiling window manager Hyprland. Ready to install from a Live ISO or with the Dotfiles Installer app...
- Raina-M/HoloRecomb_project: Custom scripts for the project of Rhynchospora recombination comparison
- tanghaibao/jcvi: Python library to facilitate genome assembly, annotation, and comparative genomics
- justlovemaki/openclaw-docker-cn-im: OpenClaw 的中国 IM 平台整合 Docker 版本，预装并配置了飞书、钉钉、QQ 机器人、企业微信等主流中国 IM 软件的插件，让您可以快速部署一个支持多个中国 IM 平台的 AI 机器人网关
- cloudflare/moltworker: Run OpenClaw, (formerly Moltbot, formerly Clawdbot) on Cloudflare Workers
- niri-wm/niri: A scrollable-tiling Wayland compositor.
- aidenlab/JuiceboxGUI: Juicebox GUI for visualization of Hi-C data
- nx10/httpgd: Asynchronous HTTP/WebSocket graphics device for R with an interactive plot viewer
- winapps-org/winapps: Run Windows apps such as Microsoft Office/Adobe in Linux (Ubuntu/Fedora) and GNOME/KDE as if they were a part of the native OS, including Nautilus integration. Hard fork of https://github.com/Fmst...
- jeanp413/open-remote-ssh: VSCode Remote Development: Open any folder on a remote machine using SSH.
- dwzhu-pku/PaperBanana: PaperBanana: Automating Academic Illustration For AI Scientists
- Nextomics/NextPolish: Fast and accurately polish the genome generated by long reads.
- ThePrimeagen/99: Neovim AI agent done right
- openclaw/openclaw: Your own personal AI assistant. Any OS. Any Platform. The lobster way. 🦞
- mikolmogorov/Flye: De novo assembler for single molecule sequencing reads using repeat graphs
- neovim/neovim: Vim-fork focused on extensibility and usability
- gdlc/BGLR-R: Bayesian Generalized Linear Regression
- arch4edu/arch4edu: Arch Linux Repository for Education
- plotly/plotly.R: An interactive graphing library for R
- notscuffed/repkg: Wallpaper engine PKG extractor/TEX to image converter
- wyp1125/MCScanX: MCScanX: Multiple Collinearity Scan toolkit X version. The most popular synteny analysis tool in the world!
- MareesAT/GWA_tutorial: A comprehensive tutorial about GWAS and PRS
- ctan2020/Arabidopsis_Cell_Atlas: A comprehensive single-cell transcriptomic atlas of Arabidopsis
- genetics-statistics/GEMMA: Genome-wide Efficient Mixed Model Association
- vinceliuice/McMojave-kde: MacOSX Mojave like theme for KDE Plasma
- keeferrourke/la-capitaine-icon-theme: La Capitaine is an icon pack designed to integrate with most desktop environments. The set of icons takes inspiration from the latest iterations of macOS and Google's Material Design.
- kstreet13/slingshot: Functions for identifying and characterizing continuous developmental trajectories in single-cell data.
- chenlianfu/geta: Gene Expression Trends Analysis
- netptop/siteproxy: reverse proxy, online proxy, 反向代理，免翻墙访问 Youtube/Twitter/Google, 支持 github 和 telegram web 登录(请注意不要通过不信任的代理进行登录)。支持 DuckDuckGo AI Chat(可免费访问 chatGPT3.5 和 Claude3)
- PrismLauncher/PrismLauncher: A custom launcher for Minecraft that allows you to easily manage multiple installations of Minecraft at once (Fork of MultiMC)
- RikkaApps/Shizuku: Using system APIs directly with adb/root privileges from normal apps through a Java process started with app_process.
- Tencent-Hunyuan/HY-Motion-1.0: HY-Motion model for 3D human motion or 3D character animation generation.
- giscus/giscus: A commenting system powered by GitHub Discussions. 💬 💎
- andrew/nesbitt.io: Personal blog built with Jekyll and hosted on GitHub Pages. I write about package management, software supply chain security, and open source infrastructure.
- net4people/bbs: Forum for discussing Internet censorship circumvention
- bestruirui/octopus: One Hub All LLMs For You | 为个人打造的 LLM API 聚合服务

## 音乐

- 拯救 - 孫楠
- 最長的電影 - 周杰倫
- 別怕變老 - 王以太 & 艾熱 AIR
- 清明雨上 - 許嵩
- 后會無期 (feat. 汪蘇瀧) - 徐良
- 如果當時 - 許嵩
- 下完這場雨 - 後弦
- 香水有毒 - 胡楊林
- 等一分钟 Wait One Minute - 徐譽滕 Xu Yu Teng
- 秋天不回來 - 王強
- 丁香花 - 唐磊
- 不為誰而作的歌 - 林俊傑
- 在你身邊 - 徐夢圓
- China-X - 徐夢圓
- 南鑼鼓巷 - 接個吻，開一槍 & Clare
- 失眠飛行 - 接個吻，開一槍, 沈以誠 & 薛黛霏
- 無名的人 (電影《雄獅少年》主題曲) - 毛不易
