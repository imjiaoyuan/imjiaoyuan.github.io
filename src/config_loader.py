from __future__ import annotations

import importlib
import sys
from pathlib import Path

from models import SiteConfig


def load_site_config(root: Path) -> SiteConfig:
    src_dir = root / "src"
    if not (src_dir / "config.py").exists():
        raise FileNotFoundError(f"src/config.py not found in {root}")

    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    import config

    importlib.reload(config)

    site = getattr(config, "SITE", None)
    if not isinstance(site, dict):
        raise ValueError("src/config.py must define a SITE dictionary")

    domain = site.get("domain", "/")
    if not domain or domain == "/":
        print("Warning: SITE['domain'] is not set. Atom feed and sitemap will use relative URLs.",
              file=sys.stderr)

    return SiteConfig(
        title=site.get("title", "Site"),
        domain=domain,
        description=site.get("description", ""),
        icon=site.get("icon", "/favicon.ico"),
        email=site.get("email", ""),

        content_dir=root / site.get("content_dir", "content"),
        static_dir=root / site.get("static_dir", "src/assets"),
        public_dir=root / site.get("public_dir", "public"),
        menu=list(site.get("menu", [])),
        server=site.get("server", {"host": "127.0.0.1", "port": 1313}),
        home_page=site.get("home_page", ""),
        feed_months=site.get("feed_months", 12),
        author=site.get("author", ""),
        og_image=site.get("og_image", ""),
    )
