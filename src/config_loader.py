from __future__ import annotations

import importlib.util
from pathlib import Path

from models import SiteConfig


def load_site_config(root: Path) -> SiteConfig:
    config_path = root / "src" / "config.py"
    if not config_path.exists():
        raise FileNotFoundError(f"src/config.py not found in {root}")

    spec = importlib.util.spec_from_file_location("site_config", config_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load src/config.py")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    site = getattr(mod, "SITE", None)
    if not isinstance(site, dict):
        raise ValueError("src/config.py must define a SITE dictionary")

    menu = list(site.get("menu", []))
    return SiteConfig(
        title=site.get("title", "Site"),
        domain=site.get("domain", "/"),
        description=site.get("description", ""),
        icon=site.get("icon", "/favicon.ico"),

        content_dir=root / site.get("content_dir", "content"),
        static_dir=root / site.get("static_dir", "src/assets"),
        public_dir=root / site.get("public_dir", "public"),
        menu=menu,
        theme_options=site.get("theme_options", {}),
        r2_remote=site.get("r2_remote", ""),
        r2_base_url=site.get("r2_base_url", ""),
        server=site.get("server", {"host": "127.0.0.1", "port": 1313}),
        root=root,
    )
