from __future__ import annotations

import html
import json
from urllib.parse import quote

from models import ContentItem, SiteConfig


def _head(cfg: SiteConfig, page_title: str, has_math: bool) -> str:
    full_title = html.escape(cfg.title) if not page_title else f"{html.escape(page_title)} | {html.escape(cfg.title)}"
    atom_url = f"{cfg.domain.rstrip('/')}/atom.xml"
    math_block = ""
    if has_math:
        math_block = """
<link rel="preload" href="/assets/jots/vendor/katex/fonts/KaTeX_Main-Regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/jots/vendor/katex/fonts/KaTeX_Math-Italic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/jots/vendor/katex/fonts/KaTeX_Main-Bold.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/jots/vendor/katex/fonts/KaTeX_Size1-Regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/jots/vendor/katex/fonts/KaTeX_Size2-Regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/jots/vendor/katex/fonts/KaTeX_Size3-Regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/jots/vendor/katex/katex.min.css">
<style>
@font-face{font-family:KaTeX_Main;font-style:normal;font-weight:400;font-display:swap;src:url("/assets/jots/vendor/katex/fonts/KaTeX_Main-Regular.woff2") format("woff2")}
@font-face{font-family:KaTeX_Main;font-style:normal;font-weight:700;font-display:swap;src:url("/assets/jots/vendor/katex/fonts/KaTeX_Main-Bold.woff2") format("woff2")}
@font-face{font-family:KaTeX_Math;font-style:italic;font-weight:400;font-display:swap;src:url("/assets/jots/vendor/katex/fonts/KaTeX_Math-Italic.woff2") format("woff2")}
@font-face{font-family:KaTeX_Size1;font-style:normal;font-weight:400;font-display:swap;src:url("/assets/jots/vendor/katex/fonts/KaTeX_Size1-Regular.woff2") format("woff2")}
@font-face{font-family:KaTeX_Size2;font-style:normal;font-weight:400;font-display:swap;src:url("/assets/jots/vendor/katex/fonts/KaTeX_Size2-Regular.woff2") format("woff2")}
@font-face{font-family:KaTeX_Size3;font-style:normal;font-weight:400;font-display:swap;src:url("/assets/jots/vendor/katex/fonts/KaTeX_Size3-Regular.woff2") format("woff2")}
</style>
<script defer src="/assets/jots/vendor/katex/katex.min.js"></script>
<script defer src="/assets/jots/vendor/katex/auto-render.min.js"></script>
<script>
document.addEventListener("DOMContentLoaded",()=>{
  if(!window.renderMathInElement)return;
  window.renderMathInElement(document.body,{
    delimiters:[
      {left:"$$",right:"$$",display:true},
      {left:"\\\\[",right:"\\\\]",display:true},
      {left:"$",right:"$",display:false},
      {left:"\\\\(",right:"\\\\)",display:false}
    ],
    throwOnError:false
  });
});
</script>
"""
    return f"""<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<title>{full_title}</title>
<meta name="description" content="{html.escape(cfg.description)}">
<link rel="icon" href="{html.escape(cfg.icon)}">
<link rel="alternate" type="application/atom+xml" title="{html.escape(cfg.title)} Atom Feed" href="{html.escape(atom_url)}">
<script>
(()=>{{
  const saved=localStorage.getItem("jots-theme");
  if(saved==="light"||saved==="dark")document.documentElement.setAttribute("data-theme",saved);
}})();
</script>
<link rel="stylesheet" href="/assets/jots/style.css">
{math_block}
</head>"""


def _header(cfg: SiteConfig) -> str:
    nav = "".join(
        f'<a href="{html.escape(str(item.get("url", "#")))}">{html.escape(str(item.get("name", "")))}</a>'
        for item in cfg.menu
    )
    return f"""<header class="top">
<a class="brand" href="/">{html.escape(cfg.title)}</a>
<nav>{nav}</nav>
</header>"""


def render_shell(
    cfg: SiteConfig, page_title: str, main_html: str, has_math: bool, show_top: bool = False
) -> str:
    top_button = '<button type="button" class="tool-btn" id="to-top">Top</button>' if show_top else ""
    return f"""<!doctype html>
<html lang="en" dir="auto">
{_head(cfg, page_title, has_math)}
<body>
{_header(cfg)}
<main>{main_html}</main>
<div class="floating-tools">
{top_button}
<button type="button" class="tool-btn" id="theme-toggle"></button>
</div>
<div id="email-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:999;align-items:center;justify-content:center" onclick="if(event.target===this)this.style.display='none'">
<div style="background:var(--bg);padding:20px 28px;border-radius:8px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,0.15)">
<p style="margin:0 0 10px;font-size:15px">imjiaoyuan@gmail.com</p>
<button class="tool-btn" onclick="navigator.clipboard.writeText('imjiaoyuan@gmail.com')">Copy</button>
<button class="tool-btn" onclick="this.closest('#email-modal').style.display='none'">Close</button>
</div>
</div>
<script>
(()=>{{
  const root=document.documentElement;
  const topBtn=document.getElementById("to-top");
  const themeBtn=document.getElementById("theme-toggle");
  const notifyThemeChange=(theme)=>window.dispatchEvent(new CustomEvent("jots:theme-change",{{detail:{{theme}}}}));
  const currentTheme=()=>{{
    const saved=root.getAttribute("data-theme");
    if(saved==="light"||saved==="dark")return saved;
    return window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";
  }};
  const syncThemeLabel=()=>{{
    if(!themeBtn)return;
    const current=currentTheme();
    themeBtn.textContent=current==="dark"?"Light":"Dark";
  }};
  topBtn?.addEventListener("click",()=>window.scrollTo({{top:0,behavior:"smooth"}}));
  themeBtn?.addEventListener("click",()=>{{
    const current=currentTheme();
    const next=current==="dark"?"light":"dark";
    root.setAttribute("data-theme",next);
    localStorage.setItem("jots-theme",next);
    notifyThemeChange(next);
    syncThemeLabel();
  }});
  window.matchMedia?.("(prefers-color-scheme: dark)")?.addEventListener?.("change",()=>{{
    const saved=root.getAttribute("data-theme");
    if(saved==="light"||saved==="dark")return;
    notifyThemeChange(currentTheme());
  }});
  syncThemeLabel();
  document.querySelector('a[href^="mailto"]')?.addEventListener('click',function(e){{e.preventDefault();document.getElementById('email-modal').style.display='flex'}});
}})();
</script></body>
</html>"""


def render_post(cfg: SiteConfig, item: ContentItem) -> str:
    repo = cfg.theme_options.get("comment_repo", "imjiaoyuan/imjiaoyuan.github.io") if cfg.theme_options else "imjiaoyuan/imjiaoyuan.github.io"
    new_issue_url = f"https://github.com/{repo}/issues/new?title={quote(item.title)}&labels=comment"
    js_title = json.dumps(item.title)
    comment_html = f"""<section class="comments">
<p><a class="comment-btn" href="{new_issue_url}" target="_blank">Go to GitHub issues to discuss with me</a></p>
</section>
<script>
(function() {{
  var title = {js_title};
  var btn = document.querySelector('.comment-btn');
  if (!btn) return;
  var q = encodeURIComponent(title) + '+in:title+repo:{repo}+is:issue';
  fetch('https://api.github.com/search/issues?q=' + q, {{
    headers: {{'Accept': 'application/vnd.github.v3+json'}}
  }})
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{
      if (data.total_count > 0) {{
        btn.href = data.items[0].html_url;
        btn.textContent = 'Go to GitHub issues to discuss with me';
      }}
    }})
    .catch(function() {{}});
}})();
</script>"""
    body = f"""<article class="single">
<h1>{html.escape(item.title)}</h1>
<div class="date">{html.escape(item.date)}</div>
<div class="content">{item.body_html}</div>
</article>
{comment_html}"""
    return render_shell(cfg, item.title, body, has_math=item.has_math, show_top=True)


def render_page(cfg: SiteConfig, item: ContentItem) -> str:
    body = f"""<article class="single">
<h1>{html.escape(item.title)}</h1>
<div class="content">{item.body_html}</div>
</article>"""
    return render_shell(cfg, item.title, body, has_math=item.has_math, show_top=False)


def render_home(cfg: SiteConfig, posts: list[ContentItem], page_no: int, total_pages: int) -> str:
    intro = html.escape(cfg.description)
    items = "".join(
        f'<li><a href="{p.rel_url}">{html.escape(p.title)}</a><time>{html.escape(p.date)}</time></li>'
        for p in posts
    )
    scroll = ""
    if page_no == 1 and total_pages > 1:
        scroll = f"""<div id="scroll-sentinel" style="height:1px"></div>
<script>
(function() {{
  let page = 1;
  const total = {total_pages};
  const sentinel = document.getElementById('scroll-sentinel');
  const list = document.querySelector('.post-list');
  let loading = false;
  if (!sentinel || total <= 1) return;
  const obs = new IntersectionObserver(function(entries) {{
    if (entries[0].isIntersecting && !loading && page < total) {{
      loading = true;
      page++;
      fetch('/page/' + page + '/')
        .then(function(r) {{ return r.text(); }})
        .then(function(html) {{
          const doc = new DOMParser().parseFromString(html, 'text/html');
          const items = doc.querySelector('.post-list');
          if (items) {{
            while (items.firstChild) {{
              list.appendChild(items.firstChild);
            }}
          }}
          loading = false;
        }})
        .catch(function() {{ loading = false; }});
    }}
  }});
  obs.observe(sentinel);
}})();
</script>"""
    body = f"""<section class="home-intro">
<p>{intro}</p>
</section>
<ul class="post-list">{items}</ul>
{scroll}"""
    return render_shell(cfg, "", body, has_math=False, show_top=False)


def render_logs(cfg: SiteConfig, title: str, logs: list[ContentItem], page_no: int, total_pages: int) -> str:
    blocks = "".join(
        f'<article class="log-item"><h2>{html.escape(i.date)}</h2><div class="content log-content">{i.body_html}</div><button type="button" class="log-toggle" hidden>Read more</button></article>'
        for i in logs
    )
    scroll = ""
    if page_no == 1 and total_pages > 1:
        scroll = """<div id="scroll-sentinel" style="height:1px"></div>
<script>
(function() {
  let page = 1;
  const total = %d;
  const sentinel = document.getElementById('scroll-sentinel');
  const section = document.querySelector('section');
  let loading = false;
  if (!sentinel || total <= 1) return;
  const obs = new IntersectionObserver(function(entries) {
    if (entries[0].isIntersecting && !loading && page < total) {
      loading = true;
      page++;
      fetch('/logs/page/' + page + '/')
        .then(function(r) { return r.text(); })
        .then(function(html) {
          var parser = new DOMParser();
          var doc = parser.parseFromString(html, 'text/html');
          var items = doc.querySelectorAll('.log-item');
          items.forEach(function(el) {
            section.appendChild(el);
          });
          initLogToggles();
          loading = false;
        })
        .catch(function() { loading = false; });
    }
  });
  obs.observe(sentinel);
})();
</script>""" % total_pages
    body = "<section><h1>%s</h1>%s</section>\n%s\n<script>\n(function() {\n  const maxLines = 12;\n  window.initLogToggles = function(container) {\n    (container || document).querySelectorAll(\".log-item\").forEach(function(item) {\n      const content = item.querySelector(\".log-content\");\n      const toggle = item.querySelector(\".log-toggle\");\n      if (!content || !toggle) return;\n      if (item.classList.contains(\"is-initialized\")) return;\n      item.classList.add(\"is-initialized\");\n      const style = window.getComputedStyle(content);\n      let lineHeight = Number.parseFloat(style.lineHeight);\n      if (!Number.isFinite(lineHeight)) {\n        lineHeight = Number.parseFloat(style.fontSize) * 1.55;\n      }\n      const collapsedHeight = Math.max(1, Math.round(lineHeight * maxLines));\n      content.style.setProperty(\"--log-collapsed-height\", collapsedHeight + \"px\");\n      content.classList.add(\"is-collapsed\");\n      if (content.scrollHeight <= collapsedHeight + 1) {\n        content.classList.remove(\"is-collapsed\");\n        toggle.remove();\n        return;\n      }\n      toggle.hidden = false;\n      toggle.textContent = \"Read more\";\n      toggle.addEventListener(\"click\", function() {\n        const expanded = content.classList.toggle(\"is-collapsed\");\n        toggle.textContent = expanded ? \"Read more\" : \"Collapse\";\n      });\n    });\n  };\n  initLogToggles();\n})();\n</script>""" % (html.escape(title), blocks, scroll)
    has_math = any(i.has_math for i in logs)
    return render_shell(cfg, title, body, has_math=has_math, show_top=True)
