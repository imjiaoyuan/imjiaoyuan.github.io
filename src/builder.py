from __future__ import annotations

import datetime as dt
import shutil
from pathlib import Path
from urllib.parse import urljoin
from xml.sax.saxutils import escape as xml_escape

from asset_pipeline import copy_assets
from config_loader import load_site_config
from content_loader import load_pages, load_posts
from date_utils import parse_date, to_atom_date
from markdown_engine import MarkdownEngine
from template_runtime import clear_cache, render_404, render_home, render_page, render_post, render_posts_list


def _write(public_dir: Path, rel_out_dir: str, html_text: str) -> None:
    out = public_dir / rel_out_dir
    out.mkdir(parents=True, exist_ok=True)

    out_path = out / "index.html"
    try:
        if out_path.read_text(encoding="utf-8") == html_text:
            return
    except FileNotFoundError:
        pass

    out_path.write_text(html_text, encoding="utf-8")


def _render_atom(cfg, posts) -> str:
    base = cfg.domain.rstrip("/") + "/"
    if cfg.feed_months > 0:
        cutoff = dt.date.today() - dt.timedelta(days=30 * cfg.feed_months)
        posts = [p for p in posts if parse_date(p.date) >= cutoff]
    updated = to_atom_date(posts[0].date) if posts else dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
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
<updated>{to_atom_date(post.date)}</updated>
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

    home_lastmod = f"\n    <lastmod>{xml_escape(posts[0].date)}</lastmod>" if posts else ""
    urls.append(f"""  <url>
    <loc>{xml_escape(base)}/</loc>{home_lastmod}
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>""")

    urls.append(f"""  <url>
    <loc>{xml_escape(base)}/blog/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>""")

    for post in posts:
        post_url = urljoin(base, post.rel_url.lstrip("/"))
        urls.append(f"""  <url>
    <loc>{xml_escape(post_url)}</loc>
    <lastmod>{xml_escape(post.date)}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

    home_slug = cfg.home_page.removesuffix(".md") if cfg.home_page else ""
    for slug, page in pages.items():
        if slug == home_slug:
            continue
        page_url = urljoin(base, page.rel_url.lstrip("/"))
        page_lastmod = f"\n    <lastmod>{xml_escape(page.date)}</lastmod>" if page.date else ""
        urls.append(f"""  <url>
    <loc>{xml_escape(page_url)}</loc>{page_lastmod}
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
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
    clear_cache()
    cfg = load_site_config(root)
    engine = MarkdownEngine()

    posts = load_posts(cfg, engine)
    pages = load_pages(cfg, engine)

    cfg.public_dir.mkdir(parents=True, exist_ok=True)

    needs_math = any(p.has_math for p in posts) or any(p.has_math for p in pages.values())
    copy_assets(cfg, needs_math)

    static_dir = root / "static"
    if static_dir.exists():
        dst = cfg.public_dir / "static"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(static_dir, dst)

    for p in posts:
        _write(cfg.public_dir, p.out_dir, render_post(cfg, p))

    home_slug = cfg.home_page.removesuffix(".md") if cfg.home_page else ""
    for slug, p in pages.items():
        if slug == home_slug:
            continue
        _write(cfg.public_dir, slug, render_page(cfg, p))

    home_page = pages.get(home_slug) if home_slug else None
    html = render_home(cfg, home_page)
    _write(cfg.public_dir, "", html)

    _write(cfg.public_dir, "blog", render_posts_list(cfg, posts))

    (cfg.public_dir / "atom.xml").write_text(_render_atom(cfg, posts), encoding="utf-8")

    (cfg.public_dir / "sitemap.xml").write_text(_render_sitemap(cfg, posts, pages), encoding="utf-8")

    (cfg.public_dir / "robots.txt").write_text(_render_robots_txt(cfg), encoding="utf-8")

    (cfg.public_dir / "404.html").write_text(render_404(cfg), encoding="utf-8")

    print(f"Built {len(posts)} posts -> {cfg.public_dir}")
