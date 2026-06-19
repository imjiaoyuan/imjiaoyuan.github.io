---
title: Vibe Coding 了一个博客框架
date: 2026-04-24
---

从 2022 年自己搭建博客至今，中间折腾了不少东西，框架换来换去，记录在这里 [博客再改版](/8ukmv/) 但是没有一个让我自己最满意的。而为了写个博客去学习它的模板语法、配置方式，感觉很麻烦，一直都想自己写一个，直到最近才抽空用 copilot 写了一个基于 python 的框架，核心代码就几百行，不依赖任何外部库，自己控制所有逻辑，想咋样就咋样，出问题也知道去哪修。

这个博客框架有以下几个我比较喜欢的特性：

**短链**

`_slug_hash` 函数根据每个文章的文件夹名称，使用 CRC24 哈希并通过 base36 输出 5 位全小写短链，直接映射到主域名下面，比如 https://jiaoyuan.org/5xbok/，既干净又便于分享，也不会产生冲突。

```python
BASE62 = "0123456789abcdefghijklmnopqrstuvwxyz"
RESERVED_SLUGS = frozenset({"assets", "logs", "readme", "page", "atom", "posts"})

def _crc24(data: bytes) -> int:
    crc = 0xB704CE
    for b in data:
        crc ^= b << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= 0x1864CFB
    return crc & 0xFFFFFF

def _slug_hash(name: str) -> str:
    val = _crc24(name.encode())
    result = []
    while val > 0:
        result.append(BASE62[val % len(BASE62)])
        val //= len(BASE62)
    return "".join(reversed(result)).rjust(5, "0")
```

`load_posts` 读取文章时自动计算短链，并且通过 `used` 集合做唯一性检查，撞了自动加后缀：

```python
def load_posts(cfg, engine):
    used = set()
    for folder in sorted(posts_dir.iterdir()):
        slug = _slug_hash(folder.name)
        if slug in used or slug in RESERVED_SLUGS:
            i = 1
            while f"{slug}-{i}" in used:
                i += 1
            slug = f"{slug}-{i}"
        used.add(slug)
```

**渲染优化**

现在很多博客框架我觉得都太复杂，为了适应大多数人的要求，加入了很多冗余的功能，我这里想办法减少了前端渲染和 js 的加载。Markdown 的渲染是自己写的，没有用任何现有的解析器。支持的语法包括标题、段落、列表、引用、表格、代码块、行内样式这些常用功能，日常写文章完全够用。

代码块这里支持 bash、python、c、r、html、css、c# 这些语言的语法高亮，由 `_highlight_source` 方法在构建时即直接渲染为带 token 类名的 HTML 标签，不加载任何 JS，速度快了很多，并且适配暗色和亮色模式。

```python
def _highlight_source(self, code: str, lang: str) -> str:
    kw = {"python": {"def", "class", "if", "else", "for", ...}, ...}
    token_re = re.compile(
        r"(?P<comment>#..."
        r")|(?P<string>\"...\")"
        r"|(?P<keyword>\b...\b)"
        r"|(?P<number>\b\d+\.?\d+\b)"
    )
    for m in token_re.finditer(code):
        if m.lastgroup == "keyword":
            out.append(f'<span class="tok-k">{text}</span>')
        elif m.lastgroup == "string":
            out.append(f'<span class="tok-s">{text}</span>')
```

CSS 变量根据主题切换，无需额外 JS 处理高亮颜色：

```css
:root {
  --tok-k: #0550ae; /* keyword */
  --tok-s: #0a3069; /* string */
  --tok-c: #6e7781; /* comment */
}
[data-theme="dark"] {
  --tok-k: #79c0ff;
  --tok-s: #a5d6ff;
  --tok-c: #8b949e;
}
```

页面生成后直接写静态 HTML 文件，Nginx 直出，不需要任何后端处理或数据库查询：

```python
def _write(public_dir: Path, rel_out_dir: str, html_text: str) -> None:
    out = public_dir / rel_out_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html_text, encoding="utf-8")
```

数学公式渲染用的 KaTeX，通过正则检测文中是否包含 `$...$` 或 `$$...$$` 或者 front matter 是否声明 `math: true`，只有在需要的时候才加载 KaTeX 的 CSS 和 JS：

```python
MATH_RE = re.compile(r"\$\$.*?\$\$|\$[^$\n]+\$", re.DOTALL)

def _load_markdown_file(path, rel_url, out_dir, is_log, engine):
    body = ...
    has_math = bool(MATH_RE.search(body)) or bool(meta.get("math"))
    return ContentItem(has_math=has_math, ...)
```

**评论系统**

评论基于 GitHub Issues。每篇文章底部有一个按钮，默认链接到新建 issue 页面，标题已经预填好。同时页面加载后会通过 GitHub API 搜索匹配该标题的现有 issue，如果找到就直接把按钮链接跳转过去，不需要建一堆重复的讨论。

```python
# config 里配置评论仓库
cf = {"comment_repo": "imjiaoyuan/imjiaoyuan.github.io"}

# 渲染评论区域
btn = f'<a href="https://github.com/{repo}/issues/new?title={title}">...</a>'

# 加载后自动匹配已有 issue
fetch("https://api.github.com/search/issues?q=" + q)
  .then(r => r.json())
  .then(data => {
    if (data.total_count > 0) btn.href = data.items[0].html_url
  })
```

不用额外注册任何第三方评论服务，仓库的 Issues 就是数据库。

---

整个博客就一个 GitHub 仓库，内容、源码、生成的静态文件都在里面。提交后 GitHub Actions 会自动执行构建，生成 HTML 然后部署到 Pages。整个过程全自动，不用手动敲命令，也不用登录什么后台。本地构建的时候可以使用 `run.py`，其包含三个命令：

```
python run.py -d            # 构建静态站点到 public/
python run.py -s            # 构建并启动开发服务器（热重载）
python run.py -n post-name  # 创建新文章
```

---

写博客对我来说就是一种记录，把脑子里的东西倒出来整理一下。很多东西不记下来很快就忘了，写下来还能回头看看当时的自己是怎么想的，也挺有意思。
