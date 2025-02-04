---
title: 关于博客更新的三两事
date: 2023-10-09
---

写博客这么久了，还是挺有感触的，记录一下写博客的一些经历。

<!--more-->

## 开始

自大一开始，我就开始写博客了，但前面很多的时间都花在寻找一个合适的博客上面，最初我使用的是博客园，虽然博客园的界面看上去比较古老，但它却实在是国内技术论坛中的一股清流，当 CSDN 等大肆塞入广告、会员机制的时候，博客园始终如一，所以大一的时候我将使用 Linux 的经历和学习 Python 的笔记都放在上面了，但后来发现，还是有一些弊端，后来使用华为云开发者社区、腾讯云开发者社区等，都有同样的一些问题：

- 文章需要审核
- 界面无法自定义个性化（博客园可以自定义 css）
- 无法设置自定义域名
- 只能在网页上写，且体验一般

于是乎，就走上了自建博客之路。

## Hexo 博客

在一位计算机学长的推荐下，第一次使用了 Hexo 博客框架，最初使用的是一款仙人掌主题 [hexo-theme-cactus](https://github.com/probberechts/hexo-theme-cactus)，简约大气，但还是有一些问题：

- 评论系统只有 disqus 和 utterances
- 加载速度很慢（当时不会自己加速静态资源）
- 代码高亮很丑

---

当时为了加载速度快，我使用的是 gitee pages，每次都要自己手动刷新网页，很不爽，而且速度貌似也不是那么的快，如果静态资源太多，还是依旧的慢。

---

后来又用了一段时间的 [stellar](https://xaoxuu.com/wiki/stellar/) 和 [keep 主题](https://github.com/XPoet/hexo-theme-keep)，但似乎加载速度都不是很如意，加上当时水平差，不会对一些 css、js 文件进行加速，导致问题无法解决。不过一个进步就是，从最初的 gitee pages 换成了 GitHub+Vercel+自定义域名。

再到后来就是 Butterfly 主题了，从最初只会改默认配置到后面逐渐学会自己写 css 修改样式、自建了图床保证稳定性、使用国内 npm 镜像源对静态资源进行加速等，学会了很多东西，也将博客收录到百度、必应和谷歌，到现在这个博客仍未下线，还可以打开，不过过段时间还是要下线了，在 [Blog](https://blog.yuanj.top/) 还能查看。不过这个博客还是有一些不如意的地方：

- 运维困难，每篇文章都有一个封面图+顶部图，感觉麻烦
- hexo 编译速度很慢
- hexo 本地调试每次都需要 hexo cl && hexo g && hexo s，不能实时预览
- 不够极简
- 版本依赖严重，更换 cdn 时版本号有一点点差别都不能用

综合以上原因，我放弃了 hexo 博客。

## GitHub issue 博客

看到 GitHub 上一位用户使用了 GitHub issue 的方式写博客：[gitblog](gitblog)，然后使用 GitHub 的 API 及 Action 自动将标题添加到 README，感觉思路很不错，主要的优点有：

- GitHub issue 搜索权重高
- 不需要额外准备图床
- 不需要本地环境

但是由于 GitHub 被墙的原因，它的缺点也很突出，那就是不开梯子很难打开，我自己日常也不太喜欢一直开着梯子，so 只能再想办法了。

## Hugo 博客

在看到少数派的一位作家写的文章 [浅谈我为什么从 HEXO 迁移到 HUGO](https://sspai.com/post/59904#!) 之后，我试了一下 hugo 博客，使用的是 [LoveIt 主题](https://hugoloveit.com/zh-cn/about/)，感觉很不错，自己修改了一些个样式，让其保证极简，评论系统用的是 [waline](https://waline.js.org/)，个人认为 hugo 的优点有下面几个

- 编译速度快，得益于 go 语言
- 不依赖 nodejs
- 网页的速度也比较快（个人感觉）
- 界面简洁大方
- 各式的模板很好用

综合以上特点，我最终使用了 hugo 博客。

博客的框架为极狐 Gitlab 代码托管+Vercel 部署+Cloudflare 域名解析，由于国内 GitHub 被墙，经常 push 不上去，我也不常开梯子，所以用极狐 Gitlab 的 CI/CD 功能，部署博客到 Vercel，CI/CD 的配置文件`.gitlab-ci.yml`内容如下

```yml
default:
  image: ubuntu:latest

vercel_deploy:
  stage: deploy
  only:
    - main
  script:
    - sed -i 's@//.*archive.ubuntu.com@//mirrors.ustc.edu.cn@g' /etc/apt/sources.list
    - apt-get update && apt-get install -y hugo curl
    - curl -sL https://deb.nodesource.com/setup_18.x | bash -
    - apt-get update && apt-get install -y nodejs build-essential
    - npm install --global vercel
    - vercel link --project=homepage --yes --token=$VERCEL_TOKEN
    - vercel pull --yes --environment=production --token=$VERCEL_TOKEN
    - vercel build --prod --token=$VERCEL_TOKEN
    - vercel deploy --prebuilt --prod --token=$VERCEL_TOKEN
```

---

**2023/10/09 更新**

Vercel 似乎已经被墙，国内使用问题很大，于是迁移到 Netlify，并且不再使用 Gitlab CI/CD 进行部署，而是使用 Gitlab 把仓库镜像到 GitHub，再导入 Netlify 进行更新部署。

博客主题使用了更加简洁的 [cocoa](https://github.com/nishanths/cocoa-hugo-theme) 主题，并且进行了一些自定义，删掉了友链页面，域名也由 yuanj.top 换成了 yuanj.top。

**2023/10/14 更新**

根据主题 Mainroad，仿照云风的 blog 进行魔改。

## 碎碎念

这个博客也不是什么大佬的技术博客，只是我个人的一些记录、感想及碎碎念，如果其中有一些内容能够帮助到大家，那我自然也很开心，我也乐意去帮助大家。最后，欢迎各位与我讨论各种问题，在各种问题中共同进步，也欢迎各位向我提出意见、问题、建议，我会很乐意解决。