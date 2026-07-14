from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SiteConfig:
    title: str
    domain: str
    description: str
    icon: str
    email: str

    content_dir: Path
    static_dir: Path
    public_dir: Path
    menu: list[dict[str, Any]]
    server: dict[str, Any]
    root: Path
    search: bool = True


@dataclass
class ContentItem:
    source: Path
    title: str
    date: str
    body_html: str
    rel_url: str
    out_dir: str
    draft: bool = False
    pinned: bool = False
    has_math: bool = False
