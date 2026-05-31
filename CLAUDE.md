# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Rules

- **Never** stage, commit, or push changes automatically. Only do so when explicitly asked by the user.

## Common Development Commands

This repository uses a custom static site generator implemented in Python. The main entry point is `run.py`.

### Building the site
```bash
python run.py -d          # Build static site to public/
```

### Local development with live reload
```bash
python run.py -s              # Build then serve public/ locally (default port 1313)
python run.py -s -p 8080      # Serve on a specific port
python run.py -s -H 0.0.0.0   # Serve on a specific host
```

### Creating new content
```bash
python run.py -n 2026-04-22-new-post   # Create a new post folder at content/posts/2026-04-22-new-post/
```

### Formatting posts
```bash
python run.py -f              # Format all posts (pangu spacing, strip trailing whitespace, normalize blank lines)
```

### Help
```bash
python run.py -h
```

## High-Level Architecture

### Overview
- The site generator is written in Python (no external dependencies).
- Content is authored in Markdown with YAML front matter, stored in `content/`.
- The generator reads configuration from `src/config.py` (hardcoded Python dict).
- Output is static HTML written to `public/`.

### Content Organization
- **Posts**: `content/posts/<slug>/index.md` (leaf bundles). Each post has an accompanying `assets/` folder for post-local media.
- **Logs**: `content/logs/<date>.md` (short log entries). The logs index is defined in `content/logs/_index.md`.
- **Pages**: `content/readme.md` and any other `.md` files at the content root become standalone pages.

### Build Pipeline (`src/builder.py`)
1. Load site configuration (`src/config.py`).
2. Parse Markdown content (`src/content_loader.py`, `src/markdown_engine.py`).
3. Copy static assets (`src/asset_pipeline.py`):
   - `src/assets/` → `public/assets/site/` (theme CSS, favicon, KaTeX vendor files).
   - Post-specific `assets/` folders are copied to the output.
4. Render HTML using inline templates (`src/template_runtime.py`):
   - Home page (paginated post list).
   - Individual post pages (with optional Giscus comments).
   - Logs pages (paginated, with collapsible long entries).
   - Standalone pages (e.g., readme).
   - Atom feed (`atom.xml`).
5. Write output to `public/` with directory-permalink structure (e.g., `public/posts/<slug>/index.html`).

### Markdown Engine (`src/markdown_engine.py`)
- Custom parser supporting common Markdown syntax: headings, paragraphs, lists, blockquotes, tables, horizontal rules, inline formatting (bold, italic, code, links, images).
- Code blocks with syntax highlighting for: bash, python, c, r, html, css, c# (aliases: sh, shell, zsh, py, rscript, csharp).
- Inline HTML is allowed (passed through).
- Tables are wrapped in a `<div class="table-wrap">` for responsive styling.
- Math is not processed by the Markdown engine; KaTeX is loaded separately when front matter contains `math: true`.

### Live Reload Server (`src/server.py`)
- When `-s` flag is used, the server watches `content/` and `src/` for changes.
- On any change, the site is rebuilt automatically.
- Injects an EventSource client into HTML pages that listens on `/__live_reload` for rebuild notifications.
- Uses a simple HTTP server with SSE for real‑time refresh.

### Key Conventions
- **Post slugs**: Should be descriptive and URL‑friendly; the generator does not enforce a date prefix, but the CLI’s `-n` helper uses the current date.
- **Front matter**: Required fields are `title` and `date` (YYYY‑MM‑DD). Optional `math: true` enables KaTeX rendering.
- **Asset references**: Inside a post, reference images as `./assets/filename.webp`. The pipeline copies them to the output post directory.
- **Theme styling**: CSS lives in `src/assets/style.css`. Dark/light theme toggle is built‑in and uses `localStorage`.
- **Math rendering**: KaTeX is vendored in `src/assets/vendor/katex/` (fonts, CSS, JS). It is loaded automatically when `math: true` is set in front matter.
- **Comments**: Giscus integration is configured in `src/config.py` under `theme_options.giscus`.

### Deployment
- GitHub Actions workflow (`.github/workflows/deploy.yml`) builds the site with `python run.py -d` and deploys the `public/` folder to GitHub Pages.
- The site is served from the root of `imjiaoyuan.github.io`.

## Notes
- The `.github/copilot-instructions.md` file is outdated (describes a Hugo‑based setup). Ignore its content.
- There are no external Python dependencies; the generator uses only the standard library.
- The CI uses Python 3.12 (see `.github/workflows/deploy.yml`). The code should be compatible with Python 3.7+ (uses `from __future__ import annotations`).
- No test suite or linter is currently configured.