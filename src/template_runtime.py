from __future__ import annotations

import html
import json
import re
from pathlib import Path

from models import ContentItem, SiteConfig

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_TEMPLATE_CACHE: dict[str, str] = {}
_PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


def _extract_description(body_html: str) -> str:
    text_only = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", body_html))
    return text_only[:160].strip() + ("..." if len(text_only) > 160 else "")


def clear_cache() -> None:
    _TEMPLATE_CACHE.clear()


def _load_template(name: str) -> str:
    if name not in _TEMPLATE_CACHE:
        path = _TEMPLATE_DIR / name
        _TEMPLATE_CACHE[name] = path.read_text(encoding="utf-8")
    return _TEMPLATE_CACHE[name]


def _render_template(name: str, context: dict[str, str]) -> str:
    template = _load_template(name)

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            available = ", ".join(sorted(context.keys()))
            raise KeyError(
                f"Missing template value: '{key}' in '{name}'. "
                f"Available: {available if available else '(none)'}"
            )
        return context[key]

    return _PLACEHOLDER_RE.sub(replace, template)


def _jsonld_blog_post(cfg: SiteConfig, item: ContentItem) -> str:
    post_url = f"{cfg.domain.rstrip('/')}{item.rel_url}"
    obj = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": item.title,
        "datePublished": item.date,
        "dateModified": item.date,
        "author": {"@type": "Person", "name": cfg.title},
        "url": post_url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": post_url},
    }
    body = json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")
    return f'<script type="application/ld+json">{body}</script>'


def _head(cfg: SiteConfig, page_title: str, has_math: bool, description: str = "", url: str = "", og_type: str = "website", jsonld: str = "") -> str:
    full_title = html.escape(cfg.title) if not page_title else f"{html.escape(page_title)} | {html.escape(cfg.title)}"
    atom_url = html.escape(f"{cfg.domain.rstrip('/')}/atom.xml")
    page_desc = html.escape(description) if description else html.escape(cfg.description)
    page_url = html.escape(f"{cfg.domain.rstrip('/')}{url}" if url else cfg.domain.rstrip("/"))
    math_block = _load_template("math_block.html") if has_math else ""
    return _render_template(
        "head.html",
        {
            "full_title": full_title,
            "page_desc": page_desc,
            "page_url": page_url,
            "og_type": html.escape(og_type),
            "site_title": html.escape(cfg.title),
            "icon": html.escape(cfg.icon),
            "atom_url": atom_url,
            "math_block": math_block,
            "jsonld": jsonld,
        },
    )


def _header(cfg: SiteConfig) -> str:
    items: list[str] = []
    for item in cfg.menu:
        url = html.escape(item.get("url", "#"))
        name = html.escape(item.get("name", ""))
        target = item.get("target")
        target_attr = f' target="{html.escape(target)}"' if target else ""
        items.append(f'<a href="{url}"{target_attr}>{name}</a>')
    return _render_template("header.html", {"site_title": html.escape(cfg.title), "nav": "".join(items)})


def render_shell(
    cfg: SiteConfig,
    page_title: str,
    main_html: str,
    has_math: bool,
    description: str = "",
    url: str = "",
    og_type: str = "website",
    jsonld: str = "",
) -> str:
    return _render_template(
        "shell.html",
        {
            "head": _head(cfg, page_title, has_math, description, url, og_type, jsonld),
            "header": _header(cfg),
            "main": main_html,
        },
    )


def render_post(cfg: SiteConfig, item: ContentItem) -> str:
    comment_html = _render_template("comment.html", {"email": html.escape(cfg.email)})
    body = _render_template(
        "post.html",
        {
            "title": html.escape(item.title),
            "date": html.escape(item.date),
            "body": item.body_html,
            "comment_html": comment_html,
        },
    )
    description = _extract_description(item.body_html)
    jsonld = _jsonld_blog_post(cfg, item)
    return render_shell(cfg, item.title, body, has_math=item.has_math, description=description, url=item.rel_url, og_type="article", jsonld=jsonld)


def render_page(cfg: SiteConfig, item: ContentItem) -> str:
    body = _render_template(
        "page.html",
        {
            "title": html.escape(item.title),
            "body": item.body_html,
        },
    )
    description = _extract_description(item.body_html)
    return render_shell(cfg, item.title, body, has_math=item.has_math, description=description, url=item.rel_url, og_type="article")


def render_404(cfg: SiteConfig) -> str:
    body = _load_template("404.html")
    return render_shell(cfg, "404", body, has_math=False, description="Page not found", url="/404.html")


def render_home(cfg: SiteConfig, page: ContentItem | None = None) -> str:
    if page is None:
        body = ""
        has_math = False
        description = ""
    else:
        body = f'<div class="content">{page.body_html}</div>'
        has_math = page.has_math
        description = _extract_description(page.body_html)
    return render_shell(cfg, "", body, has_math=has_math, description=description)


def render_posts_list(cfg: SiteConfig, posts: list[ContentItem]) -> str:
    items = "\n".join(
        f'<li><a href="{p.rel_url}">{html.escape(p.title)}</a> {html.escape(p.date)}</li>'
        for p in posts
    )
    body = f"<h1>Blog</h1>\n<ul>\n{items}\n</ul>"
    return render_shell(cfg, "Blog", body, has_math=False)
