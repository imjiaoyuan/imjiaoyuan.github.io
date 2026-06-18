# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Rules

- **Never** stage, commit, or push changes automatically. Only do so when explicitly asked by the user.

## Common Development Commands

This repository uses a custom static site generator implemented in Python (no external dependencies). The main entry point is `run.py`.

```bash
python run.py -d                          # Build static site to public/
python run.py -s                          # Build, then serve with live reload (default http://127.0.0.1:1313)
python run.py -s -p 8080                  # Serve on a custom port
python run.py -s -H 0.0.0.0               # Serve on a custom host
python run.py -n 2026-04-22-new-post      # Create a new post scaffold at content/posts/<name>/
python run.py -f                          # Format all posts (pangu spacing, strip trailing whitespace, normalize blank lines)
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
| `src/cli.py` | Argument parsing, post creation, formatting, orchestration |
| `src/config.py` | Hardcoded `SITE` dict (title, domain, menu, pagination limits, server defaults) |
| `src/config_loader.py` | Loads `src/config.py` via `importlib`, returns a `SiteConfig` dataclass |
| `src/models.py` | `SiteConfig` and `ContentItem` dataclasses |
| `src/content_loader.py` | Parses front matter, loads posts/pages, pangu formatting, slug hashing |
| `src/markdown_engine.py` | Custom Markdown-to-HTML parser with syntax highlighting |
| `src/template_runtime.py` | HTML rendering via `{{placeholder}}` template substitution |
| `src/asset_pipeline.py` | Copies static assets and per-post assets to `public/` |
| `src/builder.py` | Orchestrates the full build: load → parse → copy → render → write |
| `src/server.py` | HTTP server with file watcher, live-reload via SSE |
| `src/date_utils.py` | Date parsing (`YYYY-MM-DD`) and Atom date formatting |
| `src/templates/` | HTML fragments using `{{variable}}` syntax (shell, head, header, home, post, page, comment, 404, etc.) |

### Content Organization
- **Posts**: `content/posts/<folder-name>/index.md` (leaf bundles) with an optional `assets/` subfolder for images/media.
- **Pages**: Any `.md` file directly under `content/` (e.g., `content/readme.md`) becomes a standalone page at `/<stem>/`.
- **Drafts**: Set `draft: true` in front matter to exclude a post from the build.

### Slug Hashing
Post URLs are **not** derived from folder names. Each post gets a short hash-based slug computed via CRC24 → base62 (`src/content_loader.py:_slug_hash()`). This means the URL is opaque (e.g., `/3ab7f/`) and does not change when a post folder is renamed. Reserved slugs (`assets`, `logs`, `readme`, `page`, `atom`, `posts`) are avoided, and collisions get a numeric suffix.

### Build Pipeline (`src/builder.py`)
1. Load site config → `SiteConfig` dataclass.
2. Parse all posts and pages (front matter + Markdown → HTML).
3. Copy static files: `src/assets/` contents (favicon, CSS, vendor/) go to `public/assets/site/`; per-post `assets/` folders go alongside each post’s `index.html`.
4. Render HTML pages:
   - Home page with paginated post list (infinite scroll via IntersectionObserver for subsequent pages).
   - Individual post pages with comment integration.
   - Standalone pages.
   - `404.html`, `atom.xml`, `sitemap.xml`, `robots.txt`.
5. Write output using directory-permalink structure (`public/<slug>/index.html`).

### Template System (`src/template_runtime.py`)
- Simple `{{variable_name}}` placeholder substitution — not Jinja or Django.
- Templates are cached in memory after first read from `src/templates/`.
- A `render_shell()` helper wraps page content with the shared `<head>`, header, footer, theme toggle, and email modal.

### Markdown Engine (`src/markdown_engine.py`)
- Custom line-by-line parser. Supports: headings (with auto-generated `id` slugs), paragraphs, unordered/ordered lists (nested), blockquotes, tables (wrapped in `<div class="table-wrap">`), horizontal rules, inline formatting (bold, italic, code, links, images).
- Fenced code blocks with syntax highlighting for: bash, python, c, r, html, css, c# (aliases: sh, shell, zsh, py, rscript, csharp). Unrecognized languages render as plain escaped text.
- Inline HTML is passed through verbatim.
- Math (`$...$` / `$$...$$`) is left as raw text; KaTeX is loaded client-side when `math: true` is set in front matter.

### Live Reload Server (`src/server.py`)
- Watches `content/` and `src/` for file changes (polling every 0.8s, comparing mtimes).
- On change: rebuilds the site, then notifies all connected browsers via Server-Sent Events.
- Injects an `<script>` snippet before `</body>` that connects to `/__live_reload` EventSource.
- HTML responses get `Cache-Control: no-store`; static assets get long cache lifetimes (images, fonts, CSS: 86400s).

### Key Conventions
- **Front matter**: YAML-like, between `---` lines. Required: `title`, `date` (YYYY-MM-DD). Optional: `math: true` (enables KaTeX), `draft: true` (excludes from build).
- **Asset references**: Inside a post, reference images as `./assets/filename.webp`. The asset pipeline copies the post’s `assets/` folder to the output directory.
- **Comments**: Custom GitHub Issues-based system (not Giscus). `src/templates/comment.html` fetches the GitHub Issues API to find an existing issue matching the post title, or links to create a new one. Configured via `theme_options.comment_repo` in `src/config.py`.
- **Theme**: Dark/light toggle in the shell template. Stores preference in `localStorage` under `site-theme`, applies via `data-theme` attribute on `<html>`. Respects `prefers-color-scheme` when no explicit preference is saved. CSS lives in `src/assets/style.css`.
- **Math rendering**: KaTeX is vendored in `src/assets/vendor/katex/`. It is only copied to the output when at least one post or page has `math: true` (or contains `$` math delimiters in the body).
- **Homepage pagination**: Configurable via `home_limit` in `src/config.py` (default 30). Page 1 is at `/`, subsequent pages at `/page/N/`. The homepage uses infinite scroll: an IntersectionObserver fetches the next page’s post list and appends it.

### Deployment
- GitHub Actions workflow (`.github/workflows/deploy.yml`) triggers on push to `main`.
- Builds with Python 3.12 + `python run.py -d`, deploys `public/` via `actions/deploy-pages`.

## Notes
- The `.github/copilot-instructions.md` file is outdated (describes a Hugo‑based setup). Ignore its content.
- No external Python dependencies — the generator uses only the standard library.
- No test suite or linter is currently configured.
- CI uses Python 3.12; source code targets Python 3.7+ (uses `from __future__ import annotations`).