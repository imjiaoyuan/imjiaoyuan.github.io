# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
python run.py -d                 # build static site to public/
python run.py -s                 # build + serve with live reload (port 1313)
python run.py -s -p 8080         # serve on custom port
python run.py -s -H 0.0.0.0      # serve on custom host
python run.py -n 2026-04-18-new-post  # create new draft post
python run.py -f                 # format all posts in-place (pangu spacing, trailing whitespace, blank lines)
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

- **`src/config.py`** — The only file you edit to configure the site. Defines a `SITE` dict (title, domain, description, menu, etc.). The `description` field feeds `<meta>` tags and the Atom feed subtitle; it defaults to `""` if omitted. Loaded at runtime via `importlib`.
- **`src/cli.py`** — Argument parsing and top-level orchestration. Handles `-d` (build), `-s` (serve), `-n` (new post), `-f` (format posts). Build errors are caught and printed with suggestions.

- **`src/config_loader.py`** — Wraps `src/config.py` into a `SiteConfig` dataclass with resolved paths and defaults.
- **`src/models.py`** — `SiteConfig` and `ContentItem` dataclasses. `ContentItem` holds parsed markdown: title, date, body_html, rel_url, out_dir, draft/pinned flags, has_math.
- **`src/content_loader.py`** — Front matter parser (handles YAML-like scalars, lists, nested lists), markdown file loader. Post slugs are CRC24 hashes of the filename stem — renaming a `.md` file changes its URL. (The hash ensures short, collision-resistant URLs without exposing the original filename.) Slugs colliding with each other or with reserved names (`assets`, `index`, `page`, `atom`) get a `-N` suffix. Also provides `pangu_format()` and `format_content()` for post formatting.
- **`src/markdown_engine.py`** — Custom markdown-to-HTML renderer. Supports: headings with slugged IDs, paragraphs, ordered/unordered/task lists with nesting, fenced code blocks (plain `<pre><code>`, no syntax highlighting), tables, blockquotes with nested paragraphs, footnotes, inline code/images/links, bold/italic/strikethrough. Math (`$$...$$` / `$...$`) is detected but rendered client-side by KaTeX. Inline links and images are only rendered when the URL matches an allowlist (`https?://`, `mailto:`, `/`, `./`, `../`).
- **`src/template_runtime.py`** — Simple `{{ key }}` placeholder replacement. Templates live in `src/templates/`. Functions: `render_shell` (wraps all pages), `render_home`, `render_post`, `render_page`, `render_posts_list`, `render_404`. The shell template (`shell.html`) includes head, header with nav menu, main content, footer, and a dark/light theme toggle. Posts include a `comment.html` footer with the site email for replies.
- **`src/builder.py`** — Orchestrates the build: loads config → loads posts/pages → copies static assets → writes HTML for each post/page → writes homepage → writes `/blog/` list page → generates `atom.xml`, `sitemap.xml`, `robots.txt`, `404.html`. Also copies a root `static/` directory to `public/static/` if it exists (for user files outside the asset pipeline).
- **`src/server.py`** — `ThreadingHTTPServer` with live reload. Watches `content/` and `src/` for changes (polling every 0.8s), rebuilds automatically, and pushes reloads to browsers via SSE (`/__live_reload`). Injects a small `<script>` before `</body>` in HTML responses.
- **`src/asset_pipeline.py`** — Copies static files from `src/assets/` to `public/assets/site/`. KaTeX vendor files are only copied when `needs_math` is true (i.e., at least one post/page contains math).
- **`src/date_utils.py`** — `parse_date` (string → `datetime.date`, falls back to 1970-01-01) and `to_atom_date` for feed generation.

### Static assets

Two paths for static files, with different behaviors:

- **`src/assets/`** — Managed by the asset pipeline (`asset_pipeline.py`). `style.css` goes to `public/assets/site/style.css`; KaTeX vendor files (`src/assets/vendor/`) are only copied when at least one post/page contains math; everything else (e.g. `favicon.ico`) is copied directly to `public/`.
- **`static/`** (repo root) — User-controlled. Copied as-is to `public/static/` with no transformation. Only exists if you create it.

### Content model

- **Posts** live in `content/posts/<name>.md`. They are **drafts by default** (`draft: true` in front matter) — drafts are excluded from the homepage, `/blog/` list, and feeds. Remove the `draft` line to publish.
- **Pages** live in `content/*.md` (top-level only). The page matching `home_page` in config (e.g., `index.md`) is rendered as the homepage at `/` instead of its own URL.
- A **`/blog/`** list page is automatically generated with all published posts.
- Front matter uses a custom YAML-like parser (not PyYAML). Supports: scalars (string/int/bool), inline lists (`[a, b]`), and indented lists (`- item`). Comments (`# ...`) are skipped.
- Recognized front matter keys: `title`, `date`, `draft` (excludes from lists/feeds), `pinned` (sorts to the top of the homepage and `/blog/`, ahead of date ordering), and `math` (force-loads KaTeX even without `$`/`$$` in the body — otherwise math is auto-detected by regex).

### Templates

All templates in `src/templates/` use `{{ placeholder_name }}` syntax. The `shell.html` template wraps every page. Menu navigation is generated from `SITE["menu"]` in config. The theme toggle (dark/light) is implemented in the shell via vanilla JS, persisted to `localStorage`. Posts include a `comment.html` footer with the site email for replies.
