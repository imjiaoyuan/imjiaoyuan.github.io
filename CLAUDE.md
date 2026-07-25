# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
python run.py -d                 # build static site to public/
python run.py -s                 # build + serve with live reload (port 1313)
python run.py -s -p 8080         # serve on custom port
python run.py -s -H 0.0.0.0      # serve on custom host
python run.py -n 2026-04-18-new-post  # create new draft post
python run.py -f                 # format all posts (pangu spacing, trailing whitespace)
python run.py -h                 # help
```

There are no tests, no linter, and no formatter configured for the source code. The project has zero external Python dependencies — only the standard library is used.

## Architecture

A **zero-dependency static site generator** for a personal blog. The entry point is `run.py`, which adds `src/` to the path and calls `cli.main()`.

### Data flow

```
content/posts/*.md  ──→ content_loader.load_posts()  ──→ ContentItem list
content/*.md        ──→ content_loader.load_pages()  ──→ ContentItem dict
                                                              │
src/config.py (SITE dict) ──→ config_loader.load_site_config() ──→ SiteConfig
                                                              │
src/templates/*.html ──→ template_runtime ({{ key }} engine) ──→ HTML strings
                                                              │
                    builder.build() writes public/
```

### Key modules

- **`src/config.py`** — The only file you edit to configure the site. Defines a `SITE` dict (title, domain, menu, etc.). Loaded at runtime via `importlib`.
- **`src/cli.py`** — Argument parsing and top-level orchestration. Handles `-d` (build), `-s` (serve), `-n` (new post), `-f` (format posts). Build errors are caught and printed with suggestions.

- **`src/config_loader.py`** — Wraps `src/config.py` into a `SiteConfig` dataclass with resolved paths and defaults.
- **`src/models.py`** — `SiteConfig` and `ContentItem` dataclasses. `ContentItem` holds parsed markdown: title, date, body_html, rel_url, out_dir, draft/pinned flags, has_math.
- **`src/content_loader.py`** — Front matter parser (handles YAML-like scalars, lists, nested lists), markdown file loader, and `BuildCache` for incremental builds. Post slugs are CRC24 hashes of the filename, not the filename itself — renaming a `.md` file does not change its URL. The build cache (stored at `.cache/build_cache.json`) is mtime-based per file and invalidates entirely when template/config/markdown-engine source files change (hash-based version).
- **`src/markdown_engine.py`** — Custom markdown-to-HTML renderer. Supports: headings with slugged IDs, paragraphs, ordered/unordered/task lists with nesting, fenced code blocks with syntax highlighting (bash, python, c, r, html, css, c#), tables, blockquotes with nested paragraphs, footnotes, inline code/images/links, bold/italic/strikethrough. Math (`$$...$$` / `$...$`) is detected but rendered client-side by KaTeX.
- **`src/template_runtime.py`** — Simple `{{ key }}` placeholder replacement. Templates live in `src/templates/`. Functions: `render_shell` (wraps all pages), `render_home`, `render_post`, `render_page`, `render_posts_list`, `render_404`. The shell template (`shell.html`) includes head, header with nav menu, main content, footer, and a dark/light theme toggle. Posts include a `comment.html` footer with the site email for replies.
- **`src/builder.py`** — Orchestrates the build: loads config → loads posts/pages → copies static assets → writes HTML for each post/page → writes homepage → writes `/posts/` list page → generates `atom.xml`, `sitemap.xml`, `robots.txt`, `404.html`. Also copies a root `static/` directory to `public/static/` if it exists (for user files outside the asset pipeline).
- **`src/server.py`** — `ThreadingHTTPServer` with live reload. Watches `content/` and `src/` for changes (polling every 0.8s), rebuilds automatically, and pushes reloads to browsers via SSE (`/__live_reload`). Injects a small `<script>` before `</body>` in HTML responses.
- **`src/asset_pipeline.py`** — Copies static files from `src/assets/` to `public/assets/site/`. KaTeX vendor files are only copied when `needs_math` is true (i.e., at least one post/page contains math).
- **`src/date_utils.py`** — `parse_date` (string → `datetime.date`, falls back to 1970-01-01) and `to_atom_date` for feed generation.

### Content model

- **Posts** live in `content/posts/<name>.md`. They are **drafts by default** (`draft: true` in front matter) — drafts are excluded from the homepage, `/posts/` list, and feeds. Remove the `draft` line to publish.
- **Pages** live in `content/*.md` (top-level only). The page matching `home_page` in config (e.g., `index.md`) is rendered as the homepage at `/` instead of its own URL.
- A **`/posts/`** list page is automatically generated with all published posts.
- Front matter uses a custom YAML-like parser (not PyYAML). Supports: scalars (string/int/float/bool), inline lists (`[a, b]`), and indented lists (`- item`). Comments (`# ...`) are skipped.

### Templates

All templates in `src/templates/` use `{{ placeholder_name }}` syntax. The `shell.html` template wraps every page. Menu navigation is generated from `SITE["menu"]` in config. The theme toggle (dark/light) is implemented in the shell via vanilla JS, persisted to `localStorage`. Posts include a `comment.html` footer with the site email for replies.
