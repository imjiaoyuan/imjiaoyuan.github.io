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
python run.py -h                          # Show help
```

## High-Level Architecture

### Overview
- Content is authored in Markdown with YAML front matter, stored under `content/`.
- Site configuration is a hardcoded Python dict in `src/config.py`, loaded dynamically via `importlib` by `src/config_loader.py`.
- Output is static HTML written to `public/`, deployed to GitHub Pages.
- `public/` and `.cache/` are gitignored — builds are always local, deployment happens via CI.

### Source Module Map

| Module | Role |
|---|---|
| `run.py` | Entry point — adds `src/` to path, delegates to `cli.main()` |
| `src/cli.py` | Argument parsing, post creation, formatting, image upload, orchestration |
| `src/config.py` | Hardcoded `SITE` dict (title, domain, email, menu, server defaults) |
| `src/config_loader.py` | Loads `src/config.py` via `importlib`, returns a `SiteConfig` dataclass |
| `src/models.py` | `SiteConfig` and `ContentItem` dataclasses |
| `src/content_loader.py` | Parses front matter, loads posts/pages, pangu formatting, slug hashing, incremental build cache |
| `src/markdown_engine.py` | Custom Markdown-to-HTML parser with syntax highlighting |
| `src/template_runtime.py` | HTML rendering via `{{placeholder}}` template substitution |
| `src/asset_pipeline.py` | Copies static assets: `copy_static` → top-level files (favicon, etc.) to `public/`; `copy_site_assets` → CSS and KaTeX vendor to `public/assets/site/` |
| `src/builder.py` | Orchestrates the full build: load → parse → copy → render → write |
| `src/server.py` | HTTP server with file watcher, live-reload via SSE |
| `src/date_utils.py` | Date parsing (`YYYY-MM-DD`) and Atom date formatting (RFC 3339) |
| `src/templates/` | HTML fragments using `{{variable}}` syntax (shell, head, header, home, post, page, comment, search_page, 404, etc.) |

### Content Organization
- **Posts**: Flat `.md` files directly under `content/posts/` (e.g., `content/posts/2024-03-20-arch-install.md`). No subdirectories — the structure was flattened from Hugo-style leaf bundles.
- **Pages**: Any `.md` file directly under `content/` (e.g., `content/readme.md`) becomes a standalone page at `/<stem>/`.
- **Drafts**: New posts created via `-n` default to `draft: true`. Drafts are parsed and cached but excluded from all output (homepage, Atom feed, sitemap). Delete the `draft` line in front matter to publish.

### Slug Hashing
Post URLs are **not** derived from filenames. Each post gets a short hash-based slug computed via CRC24 → base36 (`src/content_loader.py:_slug_hash()`). This means the URL is opaque (e.g., `/3ab7f/`) and does not change when a post file is renamed. Reserved slugs (`assets`, `logs`, `readme`, `page`, `atom`, `posts`) are avoided, and collisions get a numeric suffix.

### Build Pipeline (`src/builder.py`)
1. Load site config → `SiteConfig` dataclass.
2. Parse all posts and pages (front matter + Markdown → HTML), using incremental cache when unchanged.
3. Copy static files: `copy_static` copies top-level assets (favicon, etc.) to `public/` (skipping `style.css` and `vendor/`); `copy_site_assets` copies CSS and KaTeX vendor to `public/assets/site/`.
4. Conditionally copy KaTeX vendor files only when at least one post/page has math.
5. Render HTML pages:
   - Home page with full post list (no pagination).
   - Individual post pages with comment integration.
   - Standalone pages (the `readme` page gets special treatment — it's rendered first at a fixed `/readme/` path, then skipped in the general pages loop).
   - `404.html`, `atom.xml`, `sitemap.xml`, `robots.txt`.
6. Write output using directory-permalink structure (`public/<slug>/index.html`). The `_write()` helper skips writing when the output file already contains identical content — an optimization that avoids touching unchanged files.

### Incremental Build Cache (`src/content_loader.py:BuildCache`)
- Parsed post/page data is cached to `.cache/build_cache.json` keyed by file path with nanosecond mtime.
- On rebuild, files whose mtime hasn't changed reuse cached HTML — only modified files are re-parsed.
- A version hash derived from template files, `config.py`, `markdown_engine.py`, and `template_runtime.py` invalidates the entire cache when any of these change.
- Cache is saved atomically (write to `.tmp`, then rename).

### Template System (`src/template_runtime.py`)
- Simple `{{variable_name}}` placeholder substitution — not Jinja or Django.
- Templates are cached in memory after first read from `src/templates/`.
- A `render_shell()` helper wraps page content with the shared `<head>`, header, footer, theme toggle, and email modal.
- Note: `atom.xml`, `sitemap.xml`, and `robots.txt` are generated inline in `src/builder.py` — they do **not** use the template system.

**Template variable reference** — each template expects these context variables:

| Template | Variables |
|---|---|
| `shell.html` | `{{head}}`, `{{header}}`, `{{main}}`, `{{year}}`, `{{top_button}}` |
| `head.html` | `{{full_title}}`, `{{page_desc}}`, `{{page_url}}`, `{{og_type}}`, `{{site_title}}`, `{{icon}}`, `{{atom_url}}`, `{{math_block}}` |
| `header.html` | `{{site_title}}`, `{{nav}}` (pre-rendered `<a>` links from `cfg.menu`) |
| `home.html` | `{{intro}}`, `{{items}}` (pre-rendered `<li>` list), `{{scroll}}` (reserved, always empty) |
| `post_list_item.html` | `{{url}}`, `{{title}}`, `{{date}}` |
| `post.html` | `{{title}}`, `{{date}}`, `{{body}}`, `{{comment_html}}` |
| `page.html` | `{{title}}`, `{{body}}` |
| `comment.html` | `{{email}}` |
| `search_page.html` | No variables (static content with inline JS) |
| `404.html`, `math_block.html`, `top_button.html` | No variables (static content) |

The `render_shell()` function assembles the final page by rendering `head.html` and `header.html`, then wrapping everything in `shell.html`. Post pages additionally get a "back to top" button (`show_top=True`) and OpenGraph `og_type="article"`.

### Markdown Engine (`src/markdown_engine.py`)
- Custom line-by-line parser. Supports: headings (with auto-generated `id` slugs), paragraphs, unordered/ordered lists (nested), blockquotes, tables (wrapped in `<div class="table-wrap">`), horizontal rules, inline formatting (bold, italic, **strikethrough**, code, links, images), **task lists** (`- [ ]` / `- [x]`), and **footnotes** (`[^id]`).
- Fenced code blocks with syntax highlighting for: bash, python, c, r, html, css, c# (aliases: sh, shell, zsh, py, rscript, csharp). Unrecognized languages render as plain escaped text.
- Inline HTML is passed through verbatim.
- Math (`$...$` / `$$...$$`) is left as raw text; KaTeX is loaded client-side when `math: true` is set in front matter.

### Live Reload Server (`src/server.py`)
- Watches `content/` and `src/` for file changes (polling every 0.8s, comparing mtimes).
- On change: rebuilds the site, then notifies all connected browsers via Server-Sent Events.
- Injects an `<script>` snippet before `</body>` that connects to `/__live_reload` EventSource.
- HTML responses get `Cache-Control: no-store`; static assets get long cache lifetimes (images, fonts, CSS: 86400s).
- **Development workflow**: run `python run.py -s`, open the browser, edit Markdown files in `content/` — the server rebuilds and pushes a refresh automatically. No manual rebuild needed.

### Search
- Opt-in via `"search": True` in `src/config.py`. When enabled:
  - A "Search" link appears in the header nav (rightmost item).
  - `search_index.json` is generated at build time — a JSON array with `title`, `date`, `url`, and full plain-text `text` for every published post.
  - A `/search/` page is built with a search input and client-side filtering JS.
- Matching is **term-based**: the query is split on whitespace, every term must match either the title or body text (case-insensitive). Title matches score higher than body matches. No external search dependency.
- When `search: false` or omitted, no search link, page, or index is emitted.

### Key Conventions
- **Front matter**: A **custom parser** (not real YAML), between `---` lines. Supports: strings (optionally quoted), booleans (`true`/`false`), integers, floats, basic arrays (`[a, b]`), and list values (indented `- item` lines under a key with no initial value — this is a stateful parse: when a key like `tags:` appears with an empty value, the parser enters list-collection mode and subsequent `  - value` lines are appended to that key). Required fields: `title`, `date` (YYYY-MM-DD). Optional: `math: true` (enables KaTeX), `draft: true` (excludes from homepage), `pinned: true` (pin to top of homepage). New posts created via `-n` are drafts by default.
  - **Parser limitations**: No nested/dict values, no multi-line strings (except indented lists). String values containing spaces that aren't meant to be arrays must be quoted (`title: "My Post Title"`). Lines starting with `#` in front matter are treated as comments and ignored. Bare words like `true`/`false`/`123`/`3.14` are auto-typed; everything else is a string.
- **Post sort order**: Posts on the homepage are sorted by pinned status first (pinned posts at top), then by date descending (most recent first). This is implemented in `src/content_loader.py:load_posts()`.
- **Formatting**: The `-f` command runs pangu formatting (adds a space between CJK characters and Latin letters/digits), strips trailing whitespace, collapses 4+ consecutive blank lines to 3, and right-strips the body. Code blocks and inline code are preserved during pangu formatting.
- **Image references**: Images are stored locally in `static/images/` (committed to git). In posts, reference them as `../../static/images/<hash>.webp` — this relative path works both in editor markdown previews and on the deployed site. The builder copies `static/` into `public/static/` during the build.
- **Image compression**: Use ImageMagick to keep images lightweight: `convert <input> -resize '1200x1200>' -quality 70 <output>.webp`. The 1200px max width and quality 70 keep most images under 200KB while maintaining reasonable quality.
- **Contact**: Each post page shows a contact line with the email configured via `email` in `src/config.py`.
- **Theme**: Dark/light toggle in the shell template. Stores preference in `localStorage` under `site-theme`, applies via `data-theme` attribute on `<html>`. Respects `prefers-color-scheme` when no explicit preference is saved. CSS lives in `src/assets/style.css`.
- **CSS**: All styles are in a single file: `src/assets/style.css`. It uses CSS custom properties (variables) for theming — light and dark color schemes are defined via `:root` and `[data-theme="dark"]` selectors.
- **Client-side JS**: All JavaScript is inline in templates (no external `.js` files):
  - `shell.html`: Theme toggle button, back-to-top button. (Also has an email modal JS, but no `mailto:` link exists on the page — inert unless a mailto link is added to the header/menu.)
  - `head.html`: Inline script before CSS to apply saved theme (blocks flash of wrong theme).
- **Math rendering**: KaTeX is vendored in `src/assets/vendor/katex/`. It is only copied to the output when at least one post or page has `math: true` (or contains `$` math delimiters in the body — `has_math` is auto-detected via regex).
- **Homepage**: All posts are rendered on a single page at `/`. No pagination, no lazy loading.

### Deployment
- GitHub Actions workflow (`.github/workflows/deploy.yml`) triggers on push to `main`.
- Builds with Python 3.12 + `python run.py -d`, deploys `public/` via `actions/deploy-pages`.

## Notes
- The `.github/copilot-instructions.md` file is outdated (describes a Hugo‑based setup). Ignore its content.
- No external Python dependencies — the generator uses only the standard library.
- No test suite or linter is currently configured.
- CI uses Python 3.12; source code targets Python 3.7+ (uses `from __future__ import annotations`).
- Image compression requires `imagemagick`.
- **Date parsing silently falls back to 1970-01-01** for invalid or unparseable date strings in front matter (`src/date_utils.py:parse_date()`). A malformed date won't cause a build error — double-check post dates if sort order looks wrong.

## Codebase Quirks

These are non-obvious behaviors worth knowing before making changes:

- **Import ordering in `content_loader.py`**: Local module imports (`from date_utils import parse_date`, `from markdown_engine import MarkdownEngine`, `from models import ContentItem, SiteConfig`) appear mid-file after the `BuildCache` class, not at the top. This is deliberate — `BuildCache` has no local dependencies, while the functions below need those modules.

- **Vestigial `is_log` parameter**: `_load_markdown_file()` accepts `is_log: bool` but both callers (`load_posts` and `load_pages`) pass `False`. The parameter only affects the fallback date value (uses `path.stem` when true). This is a leftover from the Hugo-to-custom-generator migration.

- **`_write()` is idempotent**: The builder's `_write()` function reads the existing output file and skips writing if the new HTML is identical. This means editing a post and rebuilding won't update the output file's mtime unless the rendered HTML actually changed — relevant if you're checking timestamps for deployment.

- **Asset copy is split across two functions**: `copy_static` handles top-level files (favicon, etc.) directly in `public/`, but explicitly skips `style.css` and `vendor/`. `copy_site_assets` handles those, placing them under `public/assets/site/` where templates reference them. When adding new static assets, check which function (and output path) is appropriate.

- **Config loaded via `importlib`**: `src/config_loader.py` uses `importlib.util` to dynamically load `src/config.py` as a module. Each call to `load_site_config()` re-executes the file, so config changes are picked up on the next build without restarting the server. This also means `src/config.py` must be valid Python (not just a data file) and any import-side effects will re-run on every build.

- **Server watcher covers `content/` and `src/`**: The live-reload watcher (`src/server.py:_scan_source_mtimes()`) scans both directories for changes. Editing templates, CSS, config, or Python source all trigger a full rebuild + browser reload — not just Markdown content changes.

- **Pagination was removed**: All posts render on a single page at `/`. The old `home_scroll.html` template, `home_limit` config, and `/page/N/` routes are gone. If re-adding pagination: add `home_limit` back to config/models/config_loader, restore the page loop in `builder.py`, recreate the infinite-scroll template, and add `page_no`/`total_pages` params back to `render_home()`.
