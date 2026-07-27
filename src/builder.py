from __future__ import annotations

import datetime as dt
import hashlib
import shutil
from pathlib import Path
from urllib.parse import urljoin
from xml.sax.saxutils import escape as xml_escape

from asset_pipeline import copy_assets
from config_loader import load_site_config
from content_loader import BuildCache, load_pages, load_posts
from date_utils import to_atom_date
from markdown_engine import MarkdownEngine
from template_runtime import render_404, render_home, render_page, render_post, render_posts_list


def _compute_cache_version(root: Path) -> int:
    v = 0
    templates_dir = root / "src" / "templates"
    if templates_dir.exists():
        for f in sorted(templates_dir.iterdir()):
            v ^= int.from_bytes(hashlib.sha256(f.read_bytes()).digest()[:8], 'big')
    for rel in ["src/config.py", "src/markdown_engine.py", "src/template_runtime.py"]:
        v ^= int.from_bytes(hashlib.sha256((root / rel).read_bytes()).digest()[:8], 'big')
    return v


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

    urls.append(f"""  <url>
    <loc>{xml_escape(base)}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>""")

    for post in posts:
        post_url = urljoin(base, post.rel_url.lstrip("/"))
        urls.append(f"""  <url>
    <loc>{xml_escape(post_url)}</loc>
    <lastmod>{xml_escape(post.date)}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

    for slug, page in pages.items():
        page_url = urljoin(base, page.rel_url.lstrip("/"))
        urls.append(f"""  <url>
    <loc>{xml_escape(page_url)}</loc>
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
    cfg = load_site_config(root)
    engine = MarkdownEngine()

    cache_dir = root / ".cache"
    cache_path = cache_dir / "build_cache.json"
    cache_version = _compute_cache_version(root)
    build_cache = BuildCache(cache_path, cache_version)

    posts = load_posts(cfg, engine, build_cache)
    pages = load_pages(cfg, engine, build_cache)

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

    build_cache.save()

    print(f"Built {len(posts)} posts -> {cfg.public_dir}")
