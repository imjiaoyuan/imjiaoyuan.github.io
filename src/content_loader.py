from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from markdown_engine import MarkdownEngine
from models import ContentItem, SiteConfig


MATH_RE = re.compile(r"\$\$.*?\$\$|\$[^$\n]+\$", re.DOTALL)

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyz"

RESERVED_SLUGS = frozenset({"assets", "logs", "readme", "page", "atom", "posts"})


def _crc24(data: bytes) -> int:
    crc = 0xB704CE
    for b in data:
        crc ^= b << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= 0x1864CFB
    return crc & 0xFFFFFF


def _slug_hash(name: str) -> str:
    val = _crc24(name.encode())
    result = []
    while val > 0:
        result.append(BASE62[val % len(BASE62)])
        val //= len(BASE62)
    return "".join(reversed(result)).rjust(5, "0")


def _parse_front_matter(text: str) -> tuple[dict, str]:
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return {}, text
    fm = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1 :])
    meta: dict = {}
    current_key: str | None = None
    for raw_line in fm.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_key:
            meta.setdefault(current_key, [])
            meta[current_key].append(_parse_scalar(line[4:].strip()))
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        key = k.strip()
        val = v.strip()
        if not val:
            meta[key] = []
            current_key = key
        else:
            meta[key] = _parse_scalar(val)
            current_key = key
    return meta, body


def _parse_scalar(val: str):
    if val.startswith(("'", '"')) and val.endswith(("'", '"')) and len(val) >= 2:
        return val[1:-1]
    low = val.lower()
    if low in {"true", "false"}:
        return low == "true"
    if re.fullmatch(r"-?\d+", val):
        return int(val)
    if re.fullmatch(r"-?\d+\.\d+", val):
        return float(val)
    if val.startswith("[") and val.endswith("]"):
        parts = [x.strip() for x in val[1:-1].split(",") if x.strip()]
        return [_parse_scalar(x) for x in parts]
    return val


def _safe_date(date_str: str) -> dt.date:
    try:
        return dt.date.fromisoformat(str(date_str)[:10])
    except (ValueError, TypeError):
        return dt.date(1970, 1, 1)


def _load_markdown_file(path: Path, rel_url: str, out_dir: str, is_log: bool, engine: MarkdownEngine) -> ContentItem:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        print(f"Warning: Failed to decode {path} as UTF-8: {e}. Trying with error handling.")
        raw = path.read_text(encoding="utf-8", errors="replace")
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error: Cannot read file {path}: {e}")
        raise

    meta, body = _parse_front_matter(raw)
    title = str(meta.get("title", path.stem))
    fallback_date = path.stem if is_log else ""
    date = str(meta.get("date", fallback_date))
    draft = bool(meta.get("draft"))
    has_math = bool(MATH_RE.search(body)) or bool(meta.get("math"))
    return ContentItem(
        source=path,
        title=title,
        date=date,
        body_html=engine.render(body),
        rel_url=rel_url,
        out_dir=out_dir,
        draft=draft,
        has_math=has_math,
    )


def load_posts(cfg: SiteConfig, engine: MarkdownEngine) -> list[ContentItem]:
    items: list[ContentItem] = []
    posts_dir = cfg.content_dir / "posts"
    if not posts_dir.exists():
        return items
    used: set[str] = set()
    for folder in sorted(posts_dir.iterdir()):
        if not folder.is_dir():
            continue
        md = folder / "index.md"
        if not md.exists():
            continue
        slug = _slug_hash(folder.name)
        if slug in used or slug in RESERVED_SLUGS:
            i = 1
            while f"{slug}-{i}" in used:
                i += 1
            slug = f"{slug}-{i}"
        used.add(slug)
        item = _load_markdown_file(md, f"/{slug}/", slug, False, engine)
        if item.draft:
            continue
        items.append(item)
    items.sort(key=lambda x: _safe_date(x.date), reverse=True)
    return items


def load_logs(cfg: SiteConfig, engine: MarkdownEngine) -> tuple[ContentItem | None, list[ContentItem]]:
    logs_dir = cfg.content_dir / "logs"
    if not logs_dir.exists():
        return None, []
    index_item: ContentItem | None = None
    entries: list[ContentItem] = []
    index_file = logs_dir / "_index.md"
    if index_file.exists():
        index_item = _load_markdown_file(index_file, "/logs/", "logs", True, engine)

    for md in sorted(logs_dir.glob("*.md"), reverse=True):
        if md.name == "_index.md":
            continue
        slug = md.stem
        entries.append(_load_markdown_file(md, f"/logs/{slug}/", f"logs/{slug}", True, engine))
    return index_item, entries


def load_pages(cfg: SiteConfig, engine: MarkdownEngine) -> dict[str, ContentItem]:
    out: dict[str, ContentItem] = {}
    if not cfg.content_dir.exists():
        return out
    for md in sorted(cfg.content_dir.glob("*.md")):
        slug = md.stem
        out[slug] = _load_markdown_file(md, f"/{slug}/", slug, False, engine)
    return out
