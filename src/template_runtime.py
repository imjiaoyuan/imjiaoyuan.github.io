from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path

from models import ContentItem, SiteConfig

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_TEMPLATE_CACHE: dict[str, str] = {}
_PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


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
            raise KeyError(f"Missing template value: {key} in {name}")
        return context[key]

    return _PLACEHOLDER_RE.sub(replace, template)


def _head(cfg: SiteConfig, page_title: str, has_math: bool, description: str = "", url: str = "", og_type: str = "website") -> str:
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
        },
    )


def _header(cfg: SiteConfig) -> str:
    nav = "".join(
        f'<a href="{html.escape(str(item.get("url", "#")))}">{html.escape(str(item.get("name", "")))}</a>'
        for item in cfg.menu
    )
    return _render_template("header.html", {"site_title": html.escape(cfg.title), "nav": nav})


def render_shell(
    cfg: SiteConfig,
    page_title: str,
    main_html: str,
    has_math: bool,
    show_top: bool = False,
    description: str = "",
    url: str = "",
    og_type: str = "website",
) -> str:
    top_button = _load_template("top_button.html") if show_top else ""
    return _render_template(
        "shell.html",
        {
            "head": _head(cfg, page_title, has_math, description, url, og_type),
            "header": _header(cfg),
            "main": main_html,
            "year": str(datetime.now().year),
            "top_button": top_button,
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
    text_only = re.sub(r"<[^>]+>", "", item.body_html)
    description = text_only[:160].strip() + ("..." if len(text_only) > 160 else "")
    return render_shell(cfg, item.title, body, has_math=item.has_math, show_top=True, description=description, url=item.rel_url, og_type="article")


def render_page(cfg: SiteConfig, item: ContentItem) -> str:
    body = _render_template(
        "page.html",
        {
            "title": html.escape(item.title),
            "body": item.body_html,
        },
    )
    return render_shell(cfg, item.title, body, has_math=item.has_math, show_top=False)


def render_404(cfg: SiteConfig) -> str:
    body = _load_template("404.html")
    return render_shell(cfg, "404", body, has_math=False, show_top=False, description="Page not found", url="/404.html")


def render_home(cfg: SiteConfig, posts: list[ContentItem]) -> str:
    intro = html.escape(cfg.description)
    items = "".join(
        _render_template(
            "post_list_item.html",
            {
                "url": p.rel_url,
                "title": html.escape(p.title),
                "date": html.escape(p.date),
            },
        )
        for p in posts
    )
    body = _render_template("home.html", {"intro": intro, "items": items, "scroll": ""})
    return render_shell(cfg, "", body, has_math=False, show_top=False)
