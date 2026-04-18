from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .builder import build
from .config_loader import load_site_config
from .server import serve


def _create_post(root: Path, name: str) -> None:
    cfg = load_site_config(root)
    slug = name.strip().replace(" ", "-")
    if not slug:
        raise ValueError("post name cannot be empty")
    post_dir = cfg.posts_dir / slug
    post_file = post_dir / "index.md"
    assets_dir = post_dir / "assets"
    if post_file.exists():
        raise FileExistsError(f"post already exists: {post_file}")
    post_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(exist_ok=True)
    post_file.write_text(
        f"---\n"
        f"title: {slug}\n"
        f"date: {date.today().isoformat()}\n"
        f"---\n\n",
        encoding="utf-8",
    )
    print(f"Created {post_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="jots static site generator")
    parser.add_argument("-d", "--build", action="store_true", help="build static site to public/")
    parser.add_argument("-s", "--serve", action="store_true", help="build then serve public/ locally")
    parser.add_argument("-n", "--new", metavar="NAME", help="create a new post folder at posts/NAME/")
    parser.add_argument("-p", "--port", type=int, default=None, help="serve port")
    parser.add_argument("--host", default=None, help="serve host")
    parser.add_argument("--root", default=".", help="project root (default: .)")
    args = parser.parse_args()

    if not args.build and not args.serve and not args.new:
        parser.print_help()
        return

    root = Path(args.root).resolve()
    if args.new:
        _create_post(root, args.new)
        return

    build(root)

    if args.serve:
        cfg = load_site_config(root)
        host = args.host or cfg.server.get("host", "127.0.0.1")
        port = args.port or int(cfg.server.get("port", 1313))
        serve(cfg.public_dir, host, port)
