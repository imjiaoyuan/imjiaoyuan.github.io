from __future__ import annotations

import shutil
from pathlib import Path

from .models import ContentItem, SiteConfig


def _copy_dir(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def prepare_public_dir(cfg: SiteConfig) -> None:
    if cfg.public_dir.exists():
        shutil.rmtree(cfg.public_dir)
    cfg.public_dir.mkdir(parents=True, exist_ok=True)


def copy_static(cfg: SiteConfig) -> None:
    if not cfg.static_dir.exists():
        return
    for item in cfg.static_dir.iterdir():
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


def copy_jots_assets(cfg: SiteConfig) -> None:
    src = Path(__file__).resolve().parent / "assets"
    dst = cfg.public_dir / "assets" / "jots"
    _copy_dir(src, dst)


def copy_post_assets(cfg: SiteConfig, posts: list[ContentItem]) -> None:
    for p in posts:
        post_dir = p.source.parent
        out_post_dir = cfg.public_dir / p.out_dir
        for item in post_dir.iterdir():
            if item.name in {"index.md", "assets"}:
                continue
            target = out_post_dir / item.name
            if item.is_dir():
                _copy_dir(item, target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)

        asset_src = p.source.parent / "assets"
        if not asset_src.exists():
            continue
        target = cfg.public_dir / p.out_dir / "assets"
        _copy_dir(asset_src, target)
