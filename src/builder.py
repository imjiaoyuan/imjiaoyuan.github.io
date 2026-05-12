from __future__ import annotations

import datetime as dt
from pathlib import Path
from urllib.parse import urljoin
from xml.sax.saxutils import escape as xml_escape

from asset_pipeline import copy_site_assets, copy_post_assets, copy_static
from config_loader import load_site_config
from content_loader import load_logs, load_pages, load_posts
from markdown_engine import MarkdownEngine
from template_runtime import render_home, render_logs, render_page, render_post


def _write(public_dir: Path, rel_out_dir: str, html_text: str) -> None:
    out = public_dir / rel_out_dir
    out.mkdir(parents=True, exist_ok=True)
    out_path = out / "index.html"
    try:
        if out_path.read_text(encoding="utf-8") == html_text:
            return
    except (FileNotFoundError, OSError):
        pass
    out_path.write_text(html_text, encoding="utf-8")


def _to_atom_date(raw: str) -> str:
    try:
        d = dt.date.fromisoformat(str(raw)[:10])
    except Exception:
        d = dt.date(1970, 1, 1)
    return f"{d.isoformat()}T00:00:00Z"


def _render_atom(cfg, posts) -> str:
    base = cfg.domain.rstrip("/") + "/"
    updated = _to_atom_date(posts[0].date) if posts else dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    site_title = xml_escape(cfg.title)
    site_desc = xml_escape(cfg.description)
    site_link = xml_escape(base)
    feed_link = xml_escape(urljoin(base, "atom.xml"))
    feed_id = xml_escape(base)
    entries = []
    for post in posts:
        post_url = urljoin(base, post.rel_url.lstrip("/"))
        entries.append(
            f"""<entry>
<title>{xml_escape(post.title)}</title>
<link href="{xml_escape(post_url)}"/>
<id>{xml_escape(post_url)}</id>
<updated>{_to_atom_date(post.date)}</updated>
<summary>{xml_escape(post.title)}</summary>
<content type="html">{xml_escape(post.body_html)}</content>
</entry>"""
        )
    entries_xml = "\n".join(entries)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>{site_title}</title>
<subtitle>{site_desc}</subtitle>
<link href="{site_link}"/>
<link href="{feed_link}" rel="self" type="application/atom+xml"/>
<id>{feed_id}</id>
<updated>{updated}</updated>
{entries_xml}
</feed>
"""


def build(root: Path) -> None:
    cfg = load_site_config(root)
    engine = MarkdownEngine()

    posts = load_posts(cfg, engine)
    logs_index, logs = load_logs(cfg, engine)
    pages = load_pages(cfg, engine)

    cfg.public_dir.mkdir(parents=True, exist_ok=True)
    copy_static(cfg)
    needs_math = any(p.has_math for p in posts) or any(l.has_math for l in logs) or any(p.has_math for p in pages.values())
    copy_site_assets(cfg, needs_math)
    copy_post_assets(cfg, posts)

    for p in posts:
        _write(cfg.public_dir, p.out_dir, render_post(cfg, p))

    log_title = logs_index.title if logs_index else "Logs"
    log_size = max(1, cfg.log_limit)
    total_log_pages = max(1, (len(logs) + log_size - 1) // log_size)
    for i in range(total_log_pages):
        page_no = i + 1
        chunk = logs[i * log_size : (i + 1) * log_size]
        html = render_logs(cfg, log_title, chunk, page_no=page_no, total_pages=total_log_pages)
        out_dir = "logs" if page_no == 1 else f"logs/page/{page_no}"
        _write(cfg.public_dir, out_dir, html)

    if "readme" in pages:
        p = pages["readme"]
        _write(cfg.public_dir, "readme", render_page(cfg, p))

    for slug, p in pages.items():
        if slug == "readme":
            continue
        _write(cfg.public_dir, slug, render_page(cfg, p))

    pager_size = max(1, cfg.home_limit)
    total_pages = max(1, (len(posts) + pager_size - 1) // pager_size)
    for i in range(total_pages):
        page_no = i + 1
        chunk = posts[i * pager_size : (i + 1) * pager_size]
        html = render_home(cfg, chunk, page_no=page_no, total_pages=total_pages)
        out_dir = "" if page_no == 1 else f"page/{page_no}"
        _write(cfg.public_dir, out_dir, html)

    (cfg.public_dir / "atom.xml").write_text(_render_atom(cfg, posts), encoding="utf-8")

    print(f"Built {len(posts)} posts, {len(logs)} logs -> {cfg.public_dir}")
