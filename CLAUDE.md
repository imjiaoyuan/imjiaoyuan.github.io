# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Rules

- **Never** stage, commit, or push changes automatically. Only do so when explicitly asked by the user.
- When committing, use the user's Git identity (`JiaoYuan`). Keep commit messages concise (one line). Do not append Co-Authored-By trailers.

## Common Development Commands

This repository uses a custom static site generator implemented in Python (no external dependencies). The main entry point is `run.py`.

```bash
python run.py -d                          # Build static site to public/
python run.py -s                          # Build, then serve with live reload (default http://127.0.0.1:1313)
python run.py -s -p 8080                  # Serve on a custom port
python run.py -s -H 0.0.0.0               # Serve on a custom host
python run.py -n "My Post Title"          # Create a new post at content/posts/my-post-title.md
python run.py -f                          # Format all posts (pangu spacing, trailing whitespace, blank lines)
python run.py -u image1.png image2.jpg    # Upload images to R2 (auto-convert to WebP, xxHash32 naming, prints URL)
python run.py -r /path/to/project -d      # Build from a custom project root
python run.py -h                          # Show help
```

## High-Level Architecture

### Overview
- Content is authored in Markdown with YAML front matter, stored under `content/`.
- Site configuration is a hardcoded Python dict in `src/config.py`, loaded dynamically via `importlib` by `src/config_loader.py`.
- Output is static HTML written to `public/`, deployed to GitHub Pages.

### Source Module Map

| Module | Role |
|---|---|
| `run.py` | Entry point — adds `src/` to path, delegates to `cli.main()` |
| `src/cli.py` | Argument parsing, post creation, formatting, image upload, orchestration |
| `src/config.py` | Hardcoded `SITE` dict (title, domain, menu, pagination limits, server defaults, R2 config) |
| `src/config_loader.py` | Loads `src/config.py` via `importlib`, returns a `SiteConfig` dataclass |
| `src/models.py` | `SiteConfig` and `ContentItem` dataclasses |
| `src/content_loader.py` | Parses front matter, loads posts/pages, pangu formatting, slug hashing, incremental build cache |
| `src/markdown_engine.py` | Custom Markdown-to-HTML parser with syntax highlighting |
| `src/template_runtime.py` | HTML rendering via `{{placeholder}}` template substitution |
| `src/asset_pipeline.py` | Copies static assets (CSS, favicon, vendor/) to `public/` |
| `src/builder.py` | Orchestrates the full build: load → parse → copy → render → write |
| `src/server.py` | HTTP server with file watcher, live-reload via SSE |
| `src/upload.py` | Image upload pipeline: WebP conversion (ffmpeg) → xxHash32 naming → rclone upload to R2 |
| `src/date_utils.py` | Date parsing (`YYYY-MM-DD`) and Atom date formatting |
| `src/templates/` | HTML fragments using `{{variable}}` syntax (shell, head, header, home, post, page, comment, 404, etc.) |

### Content Organization
- **Posts**: Flat `.md` files directly under `content/posts/` (e.g., `content/posts/2024-03-20-arch-install.md`). No subdirectories — the structure was flattened from Hugo-style leaf bundles.
- **Pages**: Any `.md` file directly under `content/` (e.g., `content/readme.md`) becomes a standalone page at `/<stem>/`.
- **Drafts**: Set `draft: true` in front matter to exclude a post from the build.

### Slug Hashing
Post URLs are **not** derived from filenames. Each post gets a short hash-based slug computed via CRC24 → base62 (`src/content_loader.py:_slug_hash()`). This means the URL is opaque (e.g., `/3ab7f/`) and does not change when a post file is renamed. Reserved slugs (`assets`, `logs`, `readme`, `page`, `atom`, `posts`) are avoided, and collisions get a numeric suffix.

### Build Pipeline (`src/builder.py`)
1. Load site config → `SiteConfig` dataclass.
2. Parse all posts and pages (front matter + Markdown → HTML), using incremental cache when unchanged.
3. Copy static files: `src/assets/` contents (favicon, CSS, vendor/) go to `public/assets/site/`.
4. Conditionally copy KaTeX vendor files only when at least one post/page has math.
5. Render HTML pages:
   - Home page with paginated post list (infinite scroll via IntersectionObserver for subsequent pages).
   - Individual post pages with comment integration.
   - Standalone pages.
   - `404.html`, `atom.xml`, `sitemap.xml`, `robots.txt`.
6. Write output using directory-permalink structure (`public/<slug>/index.html`).

### Incremental Build Cache (`src/content_loader.py:BuildCache`)
- Parsed post/page data is cached to `.cache/build_cache.json` keyed by file path with nanosecond mtime.
- On rebuild, files whose mtime hasn't changed reuse cached HTML — only modified files are re-parsed.
- A version hash derived from template files, `config.py`, `markdown_engine.py`, and `template_runtime.py` invalidates the entire cache when any of these change.
- Cache is saved atomically (write to `.tmp`, then rename).

### Template System (`src/template_runtime.py`)
- Simple `{{variable_name}}` placeholder substitution — not Jinja or Django.
- Templates are cached in memory after first read from `src/templates/`.
- A `render_shell()` helper wraps page content with the shared `<head>`, header, footer, theme toggle, and email modal.

### Markdown Engine (`src/markdown_engine.py`)
- Custom line-by-line parser. Supports: headings (with auto-generated `id` slugs), paragraphs, unordered/ordered lists (nested), blockquotes, tables (wrapped in `<div class="table-wrap">`), horizontal rules, inline formatting (bold, italic, **strikethrough**, code, links, images), **task lists** (`- [ ]` / `- [x]`), and **footnotes** (`[^id]`).
- Fenced code blocks with syntax highlighting for: bash, python, c, r, html, css, c# (aliases: sh, shell, zsh, py, rscript, csharp). Unrecognized languages render as plain escaped text.
- Inline HTML is passed through verbatim.
- Math (`$...$` / `$$...$$`) is left as raw text; KaTeX is loaded client-side when `math: true` is set in front matter.

### Image Upload Pipeline (`src/upload.py`)
- Images are uploaded to Cloudflare R2, not stored in the repo.
- Pipeline: input image → ffmpeg conversion to WebP (quality 85) → xxHash32 content hash for deduplicated naming → rclone copy to R2.
- Configurable via `r2_remote` and `r2_base_url` in `src/config.py`.
- The CLI prints the resulting URL (e.g., `https://static.jiaoyuan.org/blog/images/a1b2c3d4.webp`).

### Live Reload Server (`src/server.py`)
- Watches `content/` and `src/` for file changes (polling every 0.8s, comparing mtimes).
- On change: rebuilds the site, then notifies all connected browsers via Server-Sent Events.
- Injects an `<script>` snippet before `</body>` that connects to `/__live_reload` EventSource.
- HTML responses get `Cache-Control: no-store`; static assets get long cache lifetimes (images, fonts, CSS: 86400s).

### Key Conventions
- **Front matter**: YAML-like, between `---` lines. Required: `title`, `date` (YYYY-MM-DD). Optional: `math: true` (enables KaTeX), `draft: true` (excludes from build).
- **Image references**: Images are uploaded to R2 via `python run.py -u`. In posts, reference them by their full R2 URL (`https://static.jiaoyuan.org/blog/images/<hash>.webp`).
- **Comments**: Custom GitHub Issues-based system (not Giscus). `src/templates/comment.html` fetches the GitHub Issues API to find an existing issue matching the post title, or links to create a new one. Configured via `theme_options.comment_repo` in `src/config.py`.
- **Theme**: Dark/light toggle in the shell template. Stores preference in `localStorage` under `site-theme`, applies via `data-theme` attribute on `<html>`. Respects `prefers-color-scheme` when no explicit preference is saved. CSS lives in `src/assets/style.css`.
- **Math rendering**: KaTeX is vendored in `src/assets/vendor/katex/`. It is only copied to the output when at least one post or page has `math: true` (or contains `$` math delimiters in the body).
- **Homepage pagination**: Configurable via `home_limit` in `src/config.py` (default 30). Page 1 is at `/`, subsequent pages at `/page/N/`. The homepage uses infinite scroll: an IntersectionObserver fetches the next page's post list and appends it.

### Deployment
- GitHub Actions workflow (`.github/workflows/deploy.yml`) triggers on push to `main`.
- Builds with Python 3.12 + `python run.py -d`, deploys `public/` via `actions/deploy-pages`.

## Notes
- The `.github/copilot-instructions.md` file is outdated (describes a Hugo‑based setup). Ignore its content.
- No external Python dependencies — the generator uses only the standard library.
- No test suite or linter is currently configured.
- CI uses Python 3.12; source code targets Python 3.7+ (uses `from __future__ import annotations`).
- Image upload requires `ffmpeg` and `rclone` to be installed and configured on the local machine.
