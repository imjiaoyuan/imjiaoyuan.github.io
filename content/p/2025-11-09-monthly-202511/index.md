---
title: 我们都是加拉格
date: 2025-11-09
---

本篇是对 2025 年 9 月至 11 月的记录与思考。

这一个月其实就是在四处奔波，忙着做老师安排的课题，中途还去彭州和乐山出了两次外业，前两天才回来，在峨眉山的观音湖旁边采样，一整天都在山上跑，虽然很累，但是好在和师兄们聊天很有意思，那里的风景也不错。

![](assets/20251109231241.webp)

## 无耻之徒

《无耻之徒》这部美剧，我早有耳闻，但真正观看时，内心依然受到了巨大的震撼。它所展现的生存法则与生命状态，以及其中折射出的中美价值观的巨大差异，都远超我的想象。
我未曾踏足美国，对其社会的了解多半源于新闻或影视作品的有限描摹。但《无耻之徒》却撕开了一道口子，让人窥见一个无比真实的美国底层社会。或许有人觉得剧情夸张，但回想 2020 年美国大选的种种闹剧——游行、抗议、对峙与撕裂，其刺激程度远超任何剧本。那些在我们看来近乎天方夜谭的景象，在彼岸却是真实上演的日常。
大多数影视剧描绘的是我们遥不可及的人生：医生、律师、精英、英雄……我们沉迷其中，是为了体验一种幻想。但《无耻之徒》却将镜头对准了我们自己——挣扎的普通人。我们真正的生活是什么样的？

- 是像 Frank 一样，在得过且过中苟且偷生；
- 是像 Fiona 一样，背负着不知从何而来的沉重责任；
- 是像 Lip 一样，被原生环境拽离本应璀璨的人生轨道；
- 是像 Ian 一样，在真爱与沉沦的边缘无助摇摆；
- 是像 Debbie 一样，看似勇敢却无力承受自己选择的后果；
- 是像 Carl 一样，企图拥抱邪恶，却无法欺骗那颗悲悯之心；
- 是像 Liam 一样，身处这个操蛋的世界，却依然感受着爱与被爱。

我们，都是 Gallaghers。生活或多或少地击败了我们每一个人。很多时候，我们想不通，或者即便明白所有道理，依旧过不好这一生。但我们唯一确信的是，无论如何，都必须走下去。

## 博客再改版

自大一开始，我就开始写博客了，但前面很多的时间都花在寻找一个合适的博客上面，最初我使用的是博客园，虽然博客园的界面看上去比较古老，但它却实在是国内技术论坛中的一股清流，当 CSDN 等大肆塞入广告、会员机制的时候，博客园始终如一，所以大一的时候我将使用 Linux 的经历和学习 Python 的笔记都放在上面了，但后来发现，还是有一些弊端，后来使用华为云开发者社区、腾讯云开发者社区等，都有同样的一些问题：

- 文章需要审核
- 界面无法自定义个性化（博客园可以自定义 css）
- 无法设置自定义域名
- 只能在网页上写，且体验一般

于是乎，就走上了自建博客之路。

---

在学长的推荐下，第一次使用了 Hexo 博客框架，最初使用的是一款仙人掌主题 [hexo-theme-cactus](https://github.com/probberechts/hexo-theme-cactus)，简约大气，但还是有一些问题：

- 评论系统只有 disqus 和 utterances
- 加载速度很慢（当时不会自己加速静态资源）
- 代码高亮很丑

当时为了加载速度快，我使用的是 gitee pages，每次都要自己手动刷新网页，很不爽，而且速度貌似也不是那么的快，如果静态资源太多，还是依旧的慢。

后来又用了一段时间的 [stellar](https://github.com/xaoxuu/hexo-theme-stellar) 和 [keep](https://github.com/XPoet/hexo-theme-keep) 主题，但似乎加载速度都不是很如意，加上当时水平差，不会对一些 css、js 文件进行加速，导致问题无法解决。不过一个进步就是，从最初的 gitee pages 换成了 GitHub + Vercel + 自定义域名。

---

再到后来就是 Butterfly 主题了，从最初只会改默认配置到后面逐渐学会自己写 css 修改样式、自建了图床保证稳定性、使用国内 npm 镜像源对静态资源进行加速等，学会了很多东西，也将博客收录到百度、必应和谷歌，到现在这个博客仍未下线，还可以打开，不过过段时间还是要下线了，在 Blog 还能查看。不过这个博客还是有一些不如意的地方：

- 运维困难，每篇文章都有一个封面图+顶部图，感觉麻烦
- hexo 编译速度很慢
- hexo 本地调试每次都需要 hexo cl && hexo g && hexo s，不能实时预览
- 不够极简
- 版本依赖严重，更换 cdn 时版本号有一点点差别都不能用

综合以上原因，我放弃了 hexo 博客。

---

在看到少数派的一篇文章 [浅谈我为什么从 HEXO 迁移到 HUGO](https://sspai.com/post/59904#!) 之后，我试了一下 hugo 博客，使用的是 LoveIt 主题，感觉很不错，自己修改了一些个样式，让其保证极简，评论系统用的是 waline，个人认为 hugo 的优点有下面几个：

- 编译速度快，得益于 go 语言
- 不依赖 nodejs
- 网页的速度也比较快（个人感觉）
- 界面简洁大方
- 各式的模板很好用

综合以上特点，我最终使用了 hugo 博客。博客的框架为极狐 Gitlab 代码托管 + Vercel 部署 + Cloudflare DNS 解析，由于国内 GitHub 被墙，经常 push 不上去，我那个时候也不常开梯子，所以用极狐 Gitlab 的 CI/CD 功能，部署博客到 Vercel。

---

后来极狐 Gitlab 全部收费，我只能放弃，直接用 GitHub，框架还是 hugo，不过更简单粗暴，直接用 Action 部署到 GitHub pages，主题也用 [Mainroad](https://github.com/Vimux/Mainroad)，根据 [云风 blog](https://blog.codingnow.com/) 魔改，这一用就是两年多，后面进行了一些小的修改，比如加上不蒜子统计和基于 js 重写的搜索功能等。

![](assets/20251109235041.webp)

（公众号上扒下来的图片，上面是自己改的 Hexo 主题，下面是自己改的 Hugo 主题，模糊到看不清了😂）

---

我的域名也进行了几次更换，从 hieroglyphs.top -> yuanj.top -> jiaoyuan.org 后面会在`jiaoyuan.org`下面放上个人主页。

---

前段时间我在学基因组选择育种，其中涉及到很多公式，我发现主题就有问题了，许多公式无法正确解析，甚至会出现内容溢出的问题。我实在厌倦了这种反反复复的修补工作，现在其实我完全可以用 Python 加一个前端框架很轻易地写出一个博客框架，但是没有意义，反而我需要因为各种各样的问题不断地修改，实在是太耗精力了。所以我想，直接用 GitHub Issues 当博客吧，用 Python 来创建新文章，并且为了本地化编写和使用盘古插件，我的思路是在本地写博客，然后推送到仓库使用 Actions 转为 issue 进行展示，GitHub 的渲染效果很好，简单大方也很漂亮。而且 commit 也可以直接用 [RSS](https://github.com/imjiaoyuan/blog/commits.atom) 来订阅，感觉什么都准备好了，评论和补充内容直接在 issues 下面追更或者创建 sub-issue 就行，很省心了，以后就打算一直用 issues 了。为了使得修改文章方便，创建新文章的时候，会为文章创建一个 6 位数 id 作为 issues 的唯一标识。我的博客在 [此仓库](https://github.com/imjiaoyuan/blog/issues)。

---

这里我写的东西实际上并没什么技术含量，只是我自己的一些思考、记录什么的，我也欢迎有朋友来一起交流一些思考或者技术相关的东西。我也希望这里写下的这些东西能够为后来的朋友提供一些思路与想法，尽量少走弯路，当然，这里的东西大多都是我自己的看法罢了。

我在网上看到过很多博客，大部分都是写了没多久就不再更了，只留下一些以前的东西飘荡在互联网上，希望自己能坚持下去吧，我比较喜欢文字的东西，而博客正好可以让我施展一番。期待多年以后的自己还在这个地方写东西。

## WSL 再见

终究还是换掉了 WSL2，因为现在我恍然发现，我似乎并没有必须要使用 WSL2 的必要了，那自然也不必要浪费那么多硬盘和内存去跑一个虚拟机了，WSL2 目前还是有不少问题的：

- WSL2 的 DNS 解析设置在`/etc/resolv.conf`文件中，在 WSL2 启动时自动生成，但是近期老是会出现网络无法正常解析的情况，其实把自动生成关掉，改为自己指定 DNS 解析地址就行了。新建文件`/etc/wsl.conf`，设置`generateResolvConf`为`false`，然后把`resolv.conf`的内容改成谷歌或者 Cloudflare 的 DNS 解析地址。
- WSL2 的硬盘占用问题，设置了稀疏矩阵之后可以回收一部分空间，但是不能完全收回，并且设置了稀疏矩阵后就不能手动扩大或者压缩 vhd 了 ... 这也太抽象了。
- WSL2 的 CPU 和内存占用问题，自从 [2.0.0](https://github.com/microsoft/WSL/releases/tag/2.0.0) 版本就增加了实验性的内存回收功能，现在依然是一坨，设置了自动回收，依然会占用很多内存，即使什么都不运行 ... Hyper-V 都比它好得多。

现在的 WSL2 能带给我的就是一个熟悉和舒适的环境，转念一想，现在分析都在实验室的服务器跑了，自个也没必要弄本地 Linux 环境了，索性换掉了，后面如果本地需要，开一个 Hyper-V 虚拟机也能很舒服的用。搭建的 Windows 开发环境中，多数的软件和应用还是由 scoop 安装的，这个之前说过就不多说了，主要又用了下面几个工具，让 Windows 下写代码变得很舒服：

- uv，scoop 中安装的 Python 是最新版，安装很多 pip 包的时候经常要编译，老出问题，而且 Python 安装的时候会卡很久，所以我直接删掉了，用 uv 来管理 Python 的版本和第三方库，用什么东西直接`uv pip install xxx`，指定虚拟环境运行 py 脚本也很方便。
- gow：专为 Windows 系统设计的轻量级命令行工具集，定位为 Cygwin 的替代方案，通过集成 Linux 环境工具扩展 Windows 命令行功能。让我在 powershell 里面也能用 awk、grep、plink、sed、tar、vim、wc 等 unix 命令，虽然 git bash 也自带了，但是不能在 powershell 里面用，所以 gow 发挥了很大作用。
- rtools，编译安装 R 包，scoop 安装的 R 也是最新版，所以很多 R 包可能会需要用 GitHub 编译安装。

不过 Windows 下写代码还是面临一些让人很恶心的问题：

- 令人难受的反斜杠，用习惯了 bash 的`/`作为路径划分，ps 的`\`看着实在是难受。
- Windows 的变态路径，默认路径不分大小写、可以有空格，但是代码里面不行 ... 还是得注意这个问题。

总的来说，除了 powershell 还是一如既往的难用之外，其他的还是蛮好的。哦对，在我的印象中，Windows11 上的 powershell 已经是很好用的了，1809 那时候的 ps 简直难用的要命，虽然还是比 bash 差很远，但是已经好多了，我一直不理解为什么 ps 的命令行参数要那么长 ... 虽然补全地不错，但是看着就很头大。

```powershell
PS D:\Projects> neofetch
        ,.=:!!t3Z3z.,                  JiaoYuan@DESKTOP-DMFFQUF
       :tt:::tt333EE3                  ------------------------
       Et:::ztt33EEEL @Ee.,      ..,   OS: Windows (Unknown) x86_64
      ;tt:::tt333EE7 ;EEEEEEttttt33#   Uptime: 2 days, 20 hours, 34 mins
     :Et:::zt333EEQ. $EEEEEttttt33QL   Shell: bash 5.2.37
     it::::tt333EEF @EEEEEEttttt33F    DE: Aero
    ;3=*^```"*4EEV :EEEEEEttttt33@.    WM: Explorer
    ,.=::::!t=., ` @EEEEEEtttz33QF     WM Theme: Custom
   ;::::::::zt33)   "4EEEtttji3P*      Terminal: Windows Terminal
  :t::::::::tt33.:Z3z..  `` ,..g.      CPU: Intel Ultra 7 155H (22) @ 3.000GHz
  i::::::::zt33F AEEEtttt::::ztF       Memory: 14455MiB/32373MiB
 ;:::::::::t33V ;EEEttttt::::t3
 E::::::::zt33L @EEEtttt::::z3F
{3=*^```"*4E3) ;EEEtttt:::::tZ`
             ` :EEEEtttt::::z7
                 "VEzjt:;;z>*`

PS D:\Projects>
```

## 再谈使用 Linux 的经历

前几天和朋友聊天，正好聊起这个问题，不免又想回顾一下这么多年用 Linux 的经历😂，之前其实写过，但是这里想再写一些新的感受：

- [使用 Linux 三年以来的感受](https://github.com/imjiaoyuan/blog/issues/16)

记得大一那年，想自己决定系统的模样，于是盯上了 Linux。当时去加入计算机社团，还想着学下 Linux，后来慢慢发现，学长们懂得是如何用 Linux 编程，而非了解 Linux 发行版，他自己可能都不知道 Ubuntu 上可以安装原生的腾讯会议，还是我后来告诉他的 ... 最开始装的发行版我记得是 Ubuntu，傻瓜式安装，点点点就行，甚至双系统也能由安装介质自动划分，但是当时没搞明白包管理器这些东西，对 Linux 还没有个系统的认识，只是有什么问题就打开百度搜，深受 CSDN 上垃圾内容的影响，输入法都装的很困难。后面又试了 deepin，但是我在应用商店安装应用总是会出现问题，当时并不清楚是源的问题，我只能四处搜索，搜不到就重装系统。deepin 之后就是优麒麟，这个纯垃圾，我都不想多说，deepin 是国内开源之光。最初用 Ubuntu 和 deepin 纯纯是因为网络上到处都推荐这俩，而且简中互联网能搜到的文档资料（shit）也最多，可以说是深受荼毒了。

后来也装了 Debian、Fedora、linux mint 啥的，但是装啥其实都不咋好用，因为没有基础知识啊，所以都没用多久，倒是 manjaro 坚持了一段时间。后面发现，这样不行啊，天天装系统算怎么回事，当时了解到 WSL，于是这一用就是三四年，安安稳稳的，可以用 Windows，还能用 Linux，何乐而不为？当时我记得照着 Arch Wiki 折腾了很久 Arch WSL🤣QQ 群里老问别人问题，人家都烦了，劝我直接物理机上 Arch，但是我当时很虚啊，学长说 Arch 很容易滚挂，用起来很累，其实我现在想想，他当时可能都没装上 ... 只是看网上这么说而已，毕竟他自己笔记本都用着 360，满屏幕都是广告。

记得当时我也折腾了虚拟机，有一次碰巧去听了一会计算机学院的算法课，我看老师是用 Xshell 连接 VMware 里的 CentoOS7 来写代码的（刚开始不知道，搜了很久才知道），但是苦在轻薄本配置太低，试了很多个 VMware 的版本，选了 VMware11，功能够用，冷启动也够快，分了 1GB 给 CentOS7，用了一段时间还是换掉了，因为很难受啊，所有操作都得在命令行里，当时也不知道用 VScode 去 ssh，所以兜兜转转还是用了 WSL2。

WSL 用的久了，慢慢的对 Linux 的各种知识也就多了起来，逐渐就知道该怎么用了，所以当大三我组了台式机之后，立马先装了 Debian，出乎意料，很成功，各种软件都搞起来了，用了蛮久一段时间，之前的博客和 B 站也发过：

- [当我换上了 Debian12 Linux](https://github.com/imjiaoyuan/blog/issues/12)
- [Debian+cinnamon 真香](https://www.bilibili.com/video/BV1n5411B7Lz/?spm_id_from=333.1387.homepage.video_card.click&vd_source=f785a7035a51b96b9abcf6b14d1036ea)

Debian 用了一段时间，我又不满足了，尝试装了 Arch，也很成功，而且有一说一，Arch 虽然安装麻烦，但是安装的过程中确实对系统有了很深的了解，装好之后，出现什么问题自己都能解决，哪怕进不了系统，插上 live CD 一样可以修好。并且用了 Arch 之后我就不再会去网络上乱搜东西了，全部查 Wiki，英文 Wiki 其实很全，基本上什么都有。当时也将这些过程写了下来：

- [Arch 下的应用方案](https://github.com/imjiaoyuan/blog/issues/26)
- [Arch 安装记录](https://github.com/imjiaoyuan/blog/issues/14)

后面我在原先的笔记本上又试了 Arch、linux mint 和 lmde6，我很倾向于使用 lmde，结合了 Debian 和 linux mint 的优点，但是无奈后面办公需要 Windows，只能格盘换回了 LTSC 2021。

考研前夕，我又换了新电脑，最开始还是安装了 Arch Linux，那会觉得 Windows11 实在太难用了，还是喜欢 Arch，但是遇到很多问题，那时候也忙着复习，实在不想太浪费时间，所以换了 Windows 10 一直用着。毕业后，暑假回家了一段时间，我又拾起了这个想法，最后成功解决了所有问题，但是似乎，心累了？我突然觉得，继续折腾下去更像是一种执念。在实际工作和学习中，许多软件在 Windows 下确实有更好的体验，我没有必要为此委屈自己，所以最终用了 Windows11，可能是年龄大了点，现在读研后更没有心思折腾，Windows11 用到底了，不知道这是进步还是倒退。

## obsidian

最近新学期了，要学习很多东西，所以肯定需要一个好的记事本来记下东西，找来找去，还是 obsidian 最合适，记得之前用 obsidian 也是大二的时候，那时候各种乱七八糟的东西都记在 obsidian，但是我当时觉得 ob 用起来麻烦，各种功能花里胡哨的我用不上，所以转用 VScode。现在不知道为什么，忽然觉得，obsidian 很舒服，搭配 git 私有仓库，简直很完美，我需要的各种功能都有，配置好一次之后就不需要再管了，git 可以版本管理，每次写完后点一下就能同步，实在很好用。不知道当时我是怎么想的，可能人长大了就是会变得不一样吧。obsidian 里面我主要用下面几个插件：

- PanGu，强迫症必需了吧，格式化 markdown 文档内容
- Custom Attachment Location，自定义文档附件的位置和文件名格式
- Git，为 obsidian 提供图形化的版本管理
- Mermaid Tools，让 obsidian 文档可以解析 mermaid 图表
- Mindmap NextGen，让 obsidian 支持 markmap 思维导图

![](assets/20251109231054.webp)

## 主动地接受信息

我一直以来都是很喜欢用 RSS，因为这样可以避免推荐算法带来繁杂的信息，让我不用从各种渠道眼花缭乱的信息中找出我所需要的，这是一个主动获取信息的过程。我用了很多 RSS 客户端，但是觉得很多都很繁琐，这个软件并没有必要很复杂，所以我觉得，不如自己写一个，于是有了 [feeds](https://github.com/imjiaoyuan/feeds)，使用 GitHub Actions 定时运行 Python 脚本来抓取 RSS，并且通过 QQ 邮箱发送到我手机上的 Gmail。

使用很简单，fork 仓库，将代码 clone 下来，修改`config.py`：

```python
import os

RSS_FEEDS = {
    'Blog Posts': [
        "https://blog.ursb.me/feed.xml",
        "https://thiscute.world/index.xml",
        "https://polebug.github.io/atom.xml",
        "https://hellogithub.com/rss",
        "https://www.longluo.me/atom.xml",
        "https://1q43.blog/feed/",
        "https://manateelazycat.github.io/feed.xml",
        "https://www.ntiy.com/feed",
        "https://feeds.feedburner.com/ruanyifeng",
        "https://cyp0633.icu/index.xml",
        "https://lutaonan.com/rss.xml",
        "https://idealclover.top/feed",
        "https://www.eaimty.com/rss.xml",
        "https://www.xheldon.com/feed.xml",
        "https://diygod.cc/feed",
        "https://www.darknavy.org/zh/index.xml",
        "https://tw93.fun/feed.xml",
        "https://blog.ferstar.org/atom.xml",
        "https://blog.lilydjwg.me/feed",
        "https://forums.debiancn.org/c/5-category/5.rss",
        "https://www.lainme.com/feed",
        "https://szclsya.me/zh-cn/index.xml",
        "https://bigeagle.me/index.xml",
        "https://yufree.cn/cn/index.xml",
        "https://www.tianxianzi.me/index.xml",
        "https://thirdshire.com/index.xml",
        "https://wangyurui.com/feed.xml"
    ],
}

RECEIVER_EMAILS_LIST = [
    "imjiaoyuan@gmail.com",
]

EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER'),
    'smtp_port': int(os.getenv('SMTP_PORT', 465)),
    'sender_email': os.getenv('SENDER_EMAIL'),
    'sender_password': os.getenv('SENDER_PASSWORD'),

    'receiver_emails': RECEIVER_EMAILS_LIST
}
```

`RSS_FEEDS`是 RSS 订阅源地址，`RECEIVER_EMAILS_LIST`就是接收 RSS 的邮箱地址，可以设置多个，`EMAIL_CONFIG`则是 GitHub Actions 的仓库密钥，这里填入 QQ 邮箱的 SMTP 服务器信息和授权码即可，每天早上六点钟就会抓取新的 RSS 发送到邮箱。

## 阅读

- [我们在造神运动中，失去的是理性与常识](https://wangyurui.com/posts/zao-shen-yun-dong-da-fen-qi-ru-he-cheng-wei-wan-3ecc0de5)
- [在加拿大办理 Q2 回国探亲签证](https://thirdshire.com/china-visa/)
- [文字的魔障](https://wangyurui.com/posts/yin-shuo-no-10-wen-zi-de-mo-zhang-c9421d90)
- [Kindle 中国拾遗](https://1q43.blog/post/12078/)
- [天才的重量](https://wangyurui.com/posts/shui-zai-shen-hua-da-fen-qi-72407f4c)
- [DNA reveals the real killers that brought down Napoleon’s army](https://www.gavi.org/vaccineswork/dna-reveals-real-killers-brought-down-napoleons-army)
- [Making a micro Linux distro](https://popovicu.com/posts/making-a-micro-linux-distro/)
- [The Linux Boot Process: From Power Button to Kernel](https://www.0xkato.xyz/linux-boot/)

## GitHub

- bio-ontology-research-group/deepgoplus: DeepGO with GOPlus axioms
- 666ghj/BettaFish: 微巢：人人可用的多 Agent 与舆情分析助手，打破信息茧房，还原舆情原貌，预测未来走向，辅助决策！
- sambecker/exif-photo-blog: Photo blog, reporting EXIF camera details (aperture, shutter speed, ISO) for each image.
- huiyadanli/RevokeMsgPatcher: A hex editor for WeChat/QQ/TIM - PC 版微信/QQ/TIM 防撤回补丁（我已经看到了，撤回也没用了）
- idinging/freemail: Cloudflare 域名邮箱系统搭建 domain mail tempmail
- plutov/gitprint: Convert Github repositories to PDF books
- RohanAdwankar/oxdraw: Diagram as Code Tool Written in Rust with Draggable Editing
- chaitin/PandaWiki: PandaWiki 是一款 AI 大模型驱动的开源知识库搭建系统，帮助你快速构建智能化的产品文档、技术文档、FAQ、博客等系统，借助大模型的力量为你提供 AI 创作、AI 问答、AI 搜索等能力
- Cloufield/gwaslab: A Python package for handling and visualizing GWAS summary statistics.
- puppeteer/puppeteer: JavaScript API for Chrome and Firefox
- jgm/pandoc: Universal markup converter
- browseros-ai/BrowserOS: The open-source Agentic browser; privacy-first alternative to ChatGPT Atlas, Perplexity Comet, Dia.
- docling-project/docling: Get your documents ready for gen AI
- zyedidia/eget: Easily install prebuilt binaries from GitHub.
- SteamRE/DepotDownloader: Steam depot downloader utilizing the SteamKit2 library.
- Hzao/PocketChest: Secure, serverless file and text sharing built on Cloudflare with large file support.
- microsoft/win32-app-isolation: Tools and documentation for Win32 app isolation
- lxgw/LxgwWenKai: An unprofessional open-source Chinese font derived from Fontworks' Klee One. 一款非专业的开源中文字体，基于 FONTWORKS 出品字体 Klee One 衍生
- nickrunning/wechat-selkies: 基于 Selkies 的 Linux 网页版微信/QQ，支持本地中文输入法，支持 AMD64 和 ARM64

## 音乐

- 谢谢你的爱 - 金润吉
- 恋愛サーキュレーション - Renai Circulation
- 回不去的夏天 - 夏日入侵企画
- 这是我一生中最勇敢的瞬间 - 棱镜
- 只是太爱你 - 张敬轩
- 枫 - 周杰伦
- Letting Go - 蔡健雅
- 水中花 - 谭咏麟
- 水中花 (Live) - 郁可唯
- 风吹麦浪 - 李健
- 梦醒 - Handsome Lau, Hypeezy 和冯泳
- 入秋 - T-BONE, 江南江和 TRAKINXRAMBO GANG
- 如果爱忘了 (Live) - 汪苏泷和单依纯
- 你是我的风景 - 何洁
- 染缸 - 楊和蘇 KeyNG 和 JinJiBeWater_隼
- 需要人陪 - 王力宏
- 月球上的人 - 陈奕迅