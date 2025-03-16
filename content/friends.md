---
title: Friends
---

Here are some high-quality blogs that I subscribed to through RSS

- [椒盐豆豉](https://blog.douchi.space)：现居美国西雅图精致码农
- [雅余](https://yayu.net/)：一位爱喝咖啡的产品经理曾经是位设计师
- [Ameow](https://ameow.xyz)：Backend engineer，《猫鱼周刊》作者
- [太隐](https://wangyurui.com)：一名终生学习者，写的文章非常有深度
- [Tony Ding's Blog](https://blog.tonyding.net/)：一个 17 岁的高二生，在公立高中国际部就读
- [Pseudoyu](https://pseudoyu.com/)：区块链开发工程师，香港大学计算机系硕士
- [Airing 的博客](https://blog.ursb.me/)：中山大学哲学硕士，原腾讯音乐高级前端工程师，毕业 4 年 T11
- [polebug's blog](https://polebug.github.io/)：保持思考｜等待｜斋戒
- [游托啤吖](https://ada3104.pages.dev/)：女权、宅、左、日饭、永远喜欢大野智、永远喜欢岚
- [This Cute World](https://thiscute.world/)：安徽建筑大学声学专业，全栈工程师
- [非理勿试](https://www.ntiy.com/)：Soulizer 运营的个人博客，专注于记录、分享和学习，倡导理性思考和原创内容
- [虹线](https://1q43.blog/)：公众号“赤潮 AKASHIO”，播客“二维吾码”主理人，面向己写作
- [Tw93](https://tw93.fun/)：来自杭州的工程师，主职前端，《潮流周刊》作者
- [槿呈 Goidea](https://justgoidea.com/)：INTJ、佛教徒和制作人，现居葡萄牙
- [DIYgod](https://diygod.cc/)：follow、RSSHub、xblog 作者，现居新加坡
- [于淼](https://yufree.cn/)：美国杰克逊实验室环境科学家
- [Randy's Blog](https://lutaonan.com/)：原广州大学华软软件学院本科生，曾就职于多个大厂的程序员
- [Owen 的博客](https://www.owenyoung.com/)：追求注意力自由、热爱闲暇时间并注重朴素生活哲学的独立博客作者
- [胡涂说](https://hutusi.com/)：现居上海的终身学习者，热爱读书、音乐、电影和编程
- [阮一峰的网络日志](https://www.ruanyifeng.com/)：《科技爱好者周刊》作者，经济学博士，CN 博客奠基人

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
