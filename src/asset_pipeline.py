from __future__ import annotations

import filecmp
import shutil

from models import SiteConfig


def copy_assets(cfg: SiteConfig, needs_math: bool = False) -> None:
    src = cfg.static_dir
    if not src.exists():
        return

    site_dst = cfg.public_dir / "assets" / "site"
    site_dst.mkdir(parents=True, exist_ok=True)

    style_src = src / "style.css"
    style_dst = site_dst / "style.css"
    if style_src.exists() and not (style_dst.exists() and filecmp.cmp(style_src, style_dst, shallow=False)):
        shutil.copy2(style_src, style_dst)

    vendor_src = src / "vendor"
    vendor_dst = site_dst / "vendor"
    if needs_math and vendor_src.exists():
        shutil.copytree(vendor_src, vendor_dst, dirs_exist_ok=True)
    elif vendor_dst.exists():
        shutil.rmtree(vendor_dst)

    for item in src.iterdir():
        if item.name in {"style.css", "vendor"}:
            continue
        target = cfg.public_dir / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)
