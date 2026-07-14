from __future__ import annotations

import shutil
from pathlib import Path

from models import SiteConfig


def copy_static(cfg: SiteConfig) -> None:
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
    src = Path(__file__).resolve().parent / "assets"
    dst = cfg.public_dir / "assets" / "site"
    dst.mkdir(parents=True, exist_ok=True)

    style_src = src / "style.css"
    style_dst = dst / "style.css"
    if style_src.exists():
        if not style_dst.exists() or style_src.read_bytes() != style_dst.read_bytes():
            shutil.copy2(style_src, style_dst)

    vendor_src = src / "vendor"
    vendor_dst = dst / "vendor"
    if needs_math and vendor_src.exists():
        if not vendor_dst.exists():
            shutil.copytree(vendor_src, vendor_dst)
    elif not needs_math and vendor_dst.exists():
        shutil.rmtree(vendor_dst)
