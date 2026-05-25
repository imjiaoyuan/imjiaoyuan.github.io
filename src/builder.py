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
    try:
        out.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as e:
        print(f"Error: Cannot create directory {out}: {e}")
        raise

    out_path = out / "index.html"
    try:
        if out_path.read_text(encoding="utf-8") == html_text:
            return
    except (FileNotFoundError, OSError):
        pass

    try:
        out_path.write_text(html_text, encoding="utf-8")
    except (PermissionError, OSError) as e:
        print(f"Error: Cannot write file {out_path}: {e}")
        raise


def _to_atom_date(raw: str) -> str:
    try:
        d = dt.date.fromisoformat(str(raw)[:10])
    except (ValueError, TypeError):
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


def _render_sitemap(cfg, posts, pages) -> str:
    base = cfg.domain.rstrip("/")
    urls = []

    # Homepage
    urls.append(f"""  <url>
    <loc>{xml_escape(base)}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>""")

    # Posts
    for post in posts:
        post_url = urljoin(base, post.rel_url.lstrip("/"))
        urls.append(f"""  <url>
    <loc>{xml_escape(post_url)}</loc>
    <lastmod>{xml_escape(post.date)}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

    # Pages
    for slug, page in pages.items():
        page_url = urljoin(base, page.rel_url.lstrip("/"))
        urls.append(f"""  <url>
    <loc>{xml_escape(page_url)}</loc>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>""")

    # Logs
    logs_url = urljoin(base, "/logs/")
    urls.append(f"""  <url>
    <loc>{xml_escape(logs_url)}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>""")

    urls_xml = "\n".join(urls)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls_xml}
</urlset>
"""


def _render_robots_txt(cfg) -> str:
    base = cfg.domain.rstrip("/")
    sitemap_url = urljoin(base, "/sitemap.xml")
    return f"""User-agent: *
Allow: /

Sitemap: {sitemap_url}
"""



def build(root: Path) -> None:
    try:
        cfg = load_site_config(root)
    except Exception as e:
        print(f"Error: Failed to load configuration: {e}")
        raise RuntimeError("Configuration error. Check src/config.py for syntax errors.") from e

    engine = MarkdownEngine()

    try:
        posts = load_posts(cfg, engine)
        logs_index, logs = load_logs(cfg, engine)
        pages = load_pages(cfg, engine)
    except Exception as e:
        print(f"Error: Failed to load content: {e}")
        raise RuntimeError("Content loading failed. Check markdown files for errors.") from e

    try:
        cfg.public_dir.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as e:
        print(f"Error: Cannot create public directory {cfg.public_dir}: {e}")
        raise RuntimeError(f"Cannot create output directory. Check permissions.") from e

    try:
        copy_static(cfg)
    except (PermissionError, OSError) as e:
        print(f"Error: Failed to copy static files: {e}")
        raise RuntimeError("Failed to copy static assets. Check file permissions.") from e

    needs_math = any(p.has_math for p in posts) or any(l.has_math for l in logs) or any(p.has_math for p in pages.values())

    try:
        copy_site_assets(cfg, needs_math)
        copy_post_assets(cfg, posts)
    except (PermissionError, OSError) as e:
        print(f"Error: Failed to copy assets: {e}")
        raise RuntimeError("Failed to copy assets. Check file permissions and disk space.") from e

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

    try:
        (cfg.public_dir / "atom.xml").write_text(_render_atom(cfg, posts), encoding="utf-8")
    except (PermissionError, OSError) as e:
        print(f"Error: Cannot write atom.xml: {e}")
        raise

    try:
        (cfg.public_dir / "sitemap.xml").write_text(_render_sitemap(cfg, posts, pages), encoding="utf-8")
    except (PermissionError, OSError) as e:
        print(f"Error: Cannot write sitemap.xml: {e}")
        raise

    try:
        (cfg.public_dir / "robots.txt").write_text(_render_robots_txt(cfg), encoding="utf-8")
    except (PermissionError, OSError) as e:
        print(f"Error: Cannot write robots.txt: {e}")
        raise

    print(f"Built {len(posts)} posts, {len(logs)} logs -> {cfg.public_dir}")
