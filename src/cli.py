from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from builder import build
from config_loader import load_site_config
from content_loader import format_content
from server import serve
from upload import upload


def _create_post(root: Path, name: str) -> None:
    try:
        cfg = load_site_config(root)
    except Exception as e:
        print(f"Error: Failed to load site configuration: {e}", file=sys.stderr)
        print("Suggestion: Check that src/config.py exists and is valid Python.", file=sys.stderr)
        sys.exit(1)

    slug = name.strip().replace(" ", "-")
    if not slug:
        print("Error: Post name cannot be empty.", file=sys.stderr)
        print("Usage: python run.py -n 'My Post Title'", file=sys.stderr)
        sys.exit(1)

    post_dir = cfg.content_dir / "posts" / slug
    post_file = post_dir / "index.md"
    assets_dir = post_dir / "assets"

    if post_file.exists():
        print(f"Error: Post already exists: {post_file}", file=sys.stderr)
        print(f"Suggestion: Use a different name or edit the existing post.", file=sys.stderr)
        sys.exit(1)

    try:
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
        print(f"  Edit the file and add your content, then run: python run.py -s")
    except (PermissionError, OSError) as e:
        print(f"Error: Failed to create post: {e}", file=sys.stderr)
        print("Suggestion: Check file permissions and disk space.", file=sys.stderr)
        sys.exit(1)


def _format_posts(root: Path) -> None:
    posts_dir = root / "content" / "posts"
    if not posts_dir.exists():
        print("No posts directory found.")
        return
    count = 0
    for folder in sorted(posts_dir.iterdir()):
        if not folder.is_dir():
            continue
        md = folder / "index.md"
        if not md.exists():
            continue
        raw = md.read_text(encoding="utf-8")
        new_raw = format_content(raw)
        if new_raw == raw:
            continue
        md.write_text(new_raw, encoding="utf-8")
        count += 1
        print(f"  formatted: {folder.name}")
    print(f"Done. {count} files updated.")


def main() -> None:
    parser = argparse.ArgumentParser(description="static site generator")
    parser.add_argument("-d", "--build", action="store_true", help="build static site to public/")
    parser.add_argument("-s", "--serve", action="store_true", help="build then serve public/ locally")
    parser.add_argument("-n", "--new", metavar="NAME", help="create a new post folder at content/posts/NAME/")
    parser.add_argument("-f", "--format", action="store_true", help="format all posts (pangu spacing, trailing whitespace, blank lines)")
    parser.add_argument("-u", "--upload", nargs="+", metavar="FILE", help="upload images to R2 (auto-convert to webp)")
    parser.add_argument("-p", "--port", type=int, default=None, help="serve port")
    parser.add_argument("-H", "--host", default=None, help="serve host")
    parser.add_argument("-r", "--root", default=".", help="project root (default: .)")
    args = parser.parse_args()

    if not args.build and not args.serve and not args.new and not args.format and not args.upload:
        parser.print_help()
        return

    root = Path(args.root).resolve()
    if args.new:
        _create_post(root, args.new)
        return
    if args.format:
        _format_posts(root)
        return
    if args.upload:
        cfg = load_site_config(root)
        for fp in args.upload:
            url = upload(Path(fp).resolve(), cfg.r2_remote, cfg.r2_base_url)
            print(url)
        return

    try:
        build(root)
        print("Build completed successfully")
    except FileNotFoundError as e:
        print(f"\nBuild failed: File not found", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        print(f"\nSuggestion: Check that all content files exist and paths are correct.", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"\nBuild failed: Permission denied", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        print(f"\nSuggestion: Check file permissions or try running with appropriate privileges.", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(f"\nBuild failed: Encoding error", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        print(f"\nSuggestion: Ensure all content files are saved as UTF-8.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nBuild failed: {type(e).__name__}", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        print(f"\nSuggestion: Check the error message above for details.", file=sys.stderr)
        print(f"  - Verify front matter syntax in your markdown files", file=sys.stderr)
        print(f"  - Check that src/config.py is valid", file=sys.stderr)
        print(f"  - Ensure content/ directory structure is correct", file=sys.stderr)
        sys.exit(1)

    if args.serve:
        try:
            cfg = load_site_config(root)
            host = args.host or cfg.server.get("host", "127.0.0.1")
            port = args.port or int(cfg.server.get("port", 1313))
            serve(cfg.public_dir, host, port, root)
        except KeyboardInterrupt:
            print("\nServer stopped")
        except Exception as e:
            print(f"\nServer failed: {e}", file=sys.stderr)
            print(f"Suggestion: Check that the port is not already in use.", file=sys.stderr)
            sys.exit(1)
