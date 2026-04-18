from __future__ import annotations

import argparse
from pathlib import Path

from .builder import build
from .config_loader import load_site_config
from .server import serve


def main() -> None:
    parser = argparse.ArgumentParser(description="jots static site generator")
    parser.add_argument("-d", "--build", action="store_true", help="build static site to public/")
    parser.add_argument("-s", "--serve", action="store_true", help="serve public/ locally")
    parser.add_argument("-p", "--port", type=int, default=None, help="serve port")
    parser.add_argument("--host", default=None, help="serve host")
    parser.add_argument("--root", default=".", help="project root (default: .)")
    args = parser.parse_args()

    if not args.build and not args.serve:
        parser.print_help()
        return

    root = Path(args.root).resolve()
    build(root)

    if args.serve:
        cfg = load_site_config(root)
        host = args.host or cfg.server.get("host", "127.0.0.1")
        port = args.port or int(cfg.server.get("port", 1313))
        serve(cfg.public_dir, host, port)
