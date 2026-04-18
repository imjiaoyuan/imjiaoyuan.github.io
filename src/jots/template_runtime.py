from __future__ import annotations

import html

from .models import ContentItem, SiteConfig


def _head(cfg: SiteConfig, page_title: str, has_math: bool, has_code: bool) -> str:
    full_title = html.escape(cfg.title) if not page_title else f"{html.escape(page_title)} | {html.escape(cfg.title)}"
    atom_url = f"{cfg.domain.rstrip('/')}/atom.xml"
    math_block = ""
    if has_math:
        math_block = """
<script>
window.MathJax = {tex:{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]}};
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" onerror="this.onerror=null;this.src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.min.js';"></script>
"""
    code_block = ""
    if has_code:
        code_block = """
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css" media="(prefers-color-scheme: light)">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css" media="(prefers-color-scheme: dark)">
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script>
 document.addEventListener("DOMContentLoaded",()=>{
  if(!window.hljs)return;
  const alias={conf:"ini",shell:"bash",sh:"bash",zsh:"bash",yml:"yaml"};
  const known=new Set(["bash","python","json","yaml","toml","ini","r","sql","javascript","typescript","html","xml","css","markdown","text","plaintext"]);
  document.querySelectorAll("pre code").forEach(el=>{
    const cls=[...el.classList].find(c=>c.startsWith("language-"));
    if(!cls){el.classList.add("nohighlight");return;}
    let lang=cls.slice(9).toLowerCase();
    lang=alias[lang]||lang;
    el.classList.remove(cls);
    if(!known.has(lang)){el.classList.add("nohighlight");return;}
    el.classList.add("language-"+lang);
    hljs.highlightElement(el);
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
<link rel="stylesheet" href="/assets/jots/jots.css">
{math_block}
{code_block}
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
    cfg: SiteConfig, page_title: str, main_html: str, has_math: bool, has_code: bool, show_top: bool = False
) -> str:
    top_button = '<button type="button" class="tool-btn" id="to-top">top</button>' if show_top else ""
    return f"""<!doctype html>
<html lang="en" dir="auto">
{_head(cfg, page_title, has_math, has_code)}
<body>
{_header(cfg)}
<main>{main_html}</main>
<div class="floating-tools">
{top_button}
<button type="button" class="tool-btn" id="theme-toggle"></button>
</div>
<script>
(()=>{{
  const root=document.documentElement;
  const topBtn=document.getElementById("to-top");
  const themeBtn=document.getElementById("theme-toggle");
  const currentTheme=()=>{{
    const saved=root.getAttribute("data-theme");
    if(saved==="light"||saved==="dark")return saved;
    return window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";
  }};
  const syncThemeLabel=()=>{{
    if(!themeBtn)return;
    const current=currentTheme();
    themeBtn.textContent=current==="dark"?"light":"dark";
  }};
  topBtn?.addEventListener("click",()=>window.scrollTo({{top:0,behavior:"smooth"}}));
  themeBtn?.addEventListener("click",()=>{{
    const current=currentTheme();
    const next=current==="dark"?"light":"dark";
    root.setAttribute("data-theme",next);
    localStorage.setItem("jots-theme",next);
    syncThemeLabel();
  }});
  syncThemeLabel();
}})();
</script>
</body>
</html>"""


def render_post(cfg: SiteConfig, item: ContentItem) -> str:
    giscus_html = ""
    giscus = (cfg.theme_options or {}).get("giscus", {})
    if giscus:
        giscus_html = f"""<section class="comments" id="comments"></section>
<script>
(()=>{{
  const s=document.createElement("script");
  s.src="https://giscus.app/client.js";
  s.setAttribute("data-repo","{html.escape(str(giscus.get('repo', '')))}");
  s.setAttribute("data-repo-id","{html.escape(str(giscus.get('repo_id', '')))}");
  s.setAttribute("data-category","{html.escape(str(giscus.get('category', 'General')))}");
  s.setAttribute("data-category-id","{html.escape(str(giscus.get('category_id', '')))}");
  s.setAttribute("data-mapping","{html.escape(str(giscus.get('mapping', 'pathname')))}");
  s.setAttribute("data-strict","{html.escape(str(giscus.get('strict', '1')))}");
  s.setAttribute("data-reactions-enabled","{html.escape(str(giscus.get('reactions_enabled', '0')))}");
  s.setAttribute("data-emit-metadata","{html.escape(str(giscus.get('emit_metadata', '0')))}");
  s.setAttribute("data-input-position","{html.escape(str(giscus.get('input_position', 'bottom')))}");
  s.setAttribute("data-theme","preferred_color_scheme");
  s.setAttribute("data-lang","{html.escape(str(giscus.get('lang', 'en')))}");
  s.setAttribute("crossorigin","anonymous");
  s.async=true;
  document.getElementById("comments")?.appendChild(s);
}})();
</script>"""
    body = f"""<article class="single">
<h1>{html.escape(item.title)}</h1>
<div class="date">{html.escape(item.date)}</div>
<div class="content">{item.body_html}</div>
</article>
{giscus_html}"""
    return render_shell(cfg, item.title, body, has_math=item.has_math, has_code=item.has_code, show_top=True)


def render_page(cfg: SiteConfig, item: ContentItem) -> str:
    body = f"""<article class="single">
<h1>{html.escape(item.title)}</h1>
<div class="content">{item.body_html}</div>
</article>"""
    return render_shell(cfg, item.title, body, has_math=item.has_math, has_code=item.has_code, show_top=False)


def render_home(cfg: SiteConfig, posts: list[ContentItem], page_no: int, total_pages: int) -> str:
    theme_opts = cfg.theme_options or {}
    intro = html.escape(cfg.description)
    socials = theme_opts.get("socials", [])
    social_html = "".join(
        f'<a class="icon" href="{html.escape(str(s.get("url", "#")))}">{html.escape(str(s.get("name", "")))}</a>'
        for s in socials
    )
    items = "".join(
        f'<li><a href="{p.rel_url}">{html.escape(p.title)}</a><time>{html.escape(p.date)}</time></li>'
        for p in posts
    )
    pager = ""
    if total_pages > 1:
        prev_link = "/" if page_no <= 2 else f"/page/{page_no-1}/"
        next_link = f"/page/{page_no+1}/"
        prev_html = f'<a href="{prev_link}">Prev</a>' if page_no > 1 else "<span></span>"
        next_html = f'<a href="{next_link}">Next</a>' if page_no < total_pages else "<span></span>"
        pager = f'<div class="pager">{prev_html}{next_html}</div>'
    body = f"""<section class="home-intro">
<p>{intro}</p>
<div class="icons">{social_html}</div>
</section>
<ul class="post-list">{items}</ul>
{pager}"""
    return render_shell(cfg, "", body, has_math=False, has_code=False, show_top=False)


def render_logs(cfg: SiteConfig, title: str, logs: list[ContentItem], page_no: int, total_pages: int) -> str:
    blocks = "".join(
        f'<article class="log-item"><h2>{html.escape(i.date)}</h2><div class="content">{i.body_html}</div></article>'
        for i in logs
    )
    pager = ""
    if total_pages > 1:
        prev_link = "/logs/" if page_no <= 2 else f"/logs/page/{page_no-1}/"
        next_link = f"/logs/page/{page_no+1}/"
        prev_html = f'<a href="{prev_link}">Prev</a>' if page_no > 1 else "<span></span>"
        next_html = f'<a href="{next_link}">Next</a>' if page_no < total_pages else "<span></span>"
        pager = f'<div class="pager">{prev_html}{next_html}</div>'
    body = f"<section><h1>{html.escape(title)}</h1>{blocks}{pager}</section>"
    has_math = any(i.has_math for i in logs)
    return render_shell(cfg, title, body, has_math=has_math, has_code=False, show_top=True)
