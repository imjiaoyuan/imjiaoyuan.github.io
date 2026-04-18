from __future__ import annotations

import importlib.util
from pathlib import Path

from .models import SiteConfig


def load_site_config(root: Path) -> SiteConfig:
    config_path = root / "config.py"
    if not config_path.exists():
        raise FileNotFoundError(f"config.py not found in {root}")

    spec = importlib.util.spec_from_file_location("jots_site_config", config_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load config.py")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    site = getattr(mod, "SITE", None)
    if not isinstance(site, dict):
        raise ValueError("config.py must define a SITE dictionary")

    menu = list(site.get("menu", []))
    return SiteConfig(
        title=site.get("title", "Site"),
        domain=site.get("domain", "/"),
        description=site.get("description", ""),
        icon=site.get("icon", "/favicon.ico"),
        home_limit=int(site.get("home_limit", 20)),
        log_limit=int(site.get("log_limit", 20)),
        posts_dir=root / site.get("posts_dir", "posts"),
        pages_dir=root / site.get("pages_dir", "pages"),
        static_dir=root / site.get("static_dir", "static"),
        public_dir=root / site.get("public_dir", "public"),
        menu=menu,
        theme_options=site.get("theme_options", {}),
        server=site.get("server", {"host": "127.0.0.1", "port": 1313}),
        root=root,
    )
