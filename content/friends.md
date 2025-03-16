---
title: Friends
---

Here are some high-quality blogs that I subscribed to through RSS

- [椒盐豆豉](https://blog.douchi.space)
- [雅余](https://yayu.net/)
- [Ameow](https://ameow.xyz)
- [太隐](https://wangyurui.com)
- [DDW2019](https://ddw2019.com)
- [Tony Ding's Blog](https://blog.tonyding.net/)
- [Eric's Blog](https://wsdjeg.net/)
- [Pseudoyu](https://pseudoyu.com/)
- [Airing 的博客](https://blog.ursb.me/)
- [卖坚果的怪叔叔](https://cuixinxin.cn/)
- [polebug's blog](https://polebug.github.io/)
- [游托啤吖](https://ada3104.pages.dev/)
- [This Cute World](https://thiscute.world/)
- [非理勿试](https://www.ntiy.com/)
- [虹线](https://1q43.blog/)
- [Tw93](https://tw93.fun/)
- [槿呈 Goidea](https://justgoidea.com/)
- [DIYgod](https://diygod.cc/)
- [于淼](https://yufree.cn/)
- [Randy's Blog](https://lutaonan.com/)
- [Owen 的博客](https://www.owenyoung.com/)
- [胡涂说](https://hutusi.com/)
- [阮一峰的网络日志](https://www.ruanyifeng.com/)

## Add me

```yml
name: JiaoYuan's blog
URL: https://yuanj.top
logo: https://yuanj.top/favicon.ico
description: 思绪来得快去得也快，偶尔会在这里停留
```

<div class="widget comments-widget">
  <h4 class="widget__title">Add Friend Link Request</h4>
  <div id="comments" class="widget__content">
    <div id="comment-form">
      <a href="https://github.com/imjiaoyuan/imjiaoyuan.github.io/issues/new?title=Friend Link Request" 
         target="_blank"
         class="comment-link">
         Go to Issues to View or Add Friend Link Request
      </a>
    </div>
  </div>
</div>

<style>
.comments-widget {
  margin-top: 2rem;
}

#comment-form {
  text-align: center;
  padding: 10px 17px 10px 2px;
}

.comment-link {
  color: #333;
  text-decoration: underline;
}

.comment-link:hover {
  color: #666;
}
</style>

<script>
document.addEventListener('DOMContentLoaded', function() {
  const owner = 'imjiaoyuan';
  const repo = 'imjiaoyuan.github.io';
  const issueTitle = 'Friend Link Request';
  const btn = document.querySelector('.comment-link');

  async function checkIssue() {
    try {
      const response = await fetch(`https://api.github.com/search/issues?q=repo:${owner}/${repo}+"${issueTitle}"+in:title`);
      const data = await response.json();
      
      if (data.items && data.items.length > 0) {
        btn.href = data.items[0].html_url;
      }
    } catch (error) {
      console.error('Error checking issue:', error);
    }
  }

  checkIssue();
});
</script>
