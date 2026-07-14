from __future__ import annotations

import shutil
from pathlib import Path

from models import ContentItem, SiteConfig


def _copy_dir(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def copy_static(cfg: SiteConfig) -> None:
    """Copy top-level static files (favicon, etc.) from src/assets/ to public/.

    style.css and vendor/ are skipped — copy_site_assets handles those under
    public/assets/site/ where the templates actually reference them.
    """
    if not cfg.static_dir.exists():
        return
    SKIP = {"style.css", "vendor"}
    for item in cfg.static_dir.iterdir():
        if item.name in SKIP:
            continue
        target = cfg.public_dir / item.name
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def copy_site_assets(cfg: SiteConfig, needs_math: bool = True) -> None:
    """Copy style.css and optionally KaTeX vendor files to public/assets/site/."""
    src = Path(__file__).resolve().parent / "assets"
    dst = cfg.public_dir / "assets" / "site"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    style = src / "style.css"
    if style.exists():
        shutil.copy2(style, dst / "style.css")
    if needs_math:
        vendor = src / "vendor"
        if vendor.exists():
            shutil.copytree(vendor, dst / "vendor")
