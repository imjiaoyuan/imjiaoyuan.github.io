# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make                       # build + serve with live reload (port 1313, default target)
make build                 # build static site to public/
make new NAME=2026-04-18-new-post  # create a new draft post at content/posts/<NAME>.md
make pangu                 # format all posts in-place (pangu spacing, trailing whitespace, blank lines)
```

Equivalent CLI: `python src/cli.py` with `-s` (serve), `-d` (build), `-n NAME` (new), `-f` (format), `-p PORT`, `-H HOST`.

There are no tests, no linter, and no formatter configured for the source code. The project has **zero external Python dependencies** — stdlib only. It is developed on Python 3.14 locally and built in CI with Python 3.12 (see Deployment), so code must stay compatible with both. `public/` is a build artifact, gitignored.

## Common workflows

- **Add a page**: create `content/<stem>.md` (top-level, not in `posts/`); it is served at `/<stem>/`, or as the homepage if `stem == home_page`. Give it a `title` and optionally a `description:` front-matter line.
- **Publish a draft**: delete the `draft: true` line in `content/posts/<file>.md`.
- **Add a post**: `make new NAME='2026-04-18-my-post'`. The `NAME` is taken verbatim as the filename (a date prefix is a convention, not enforced), and the file is created as a draft.
- **Set the site-wide SEO description / author / social image**: edit `description`, `author`, `og_image` in `src/config.py` (no code change needed). Per-page/per-post descriptions come from `description:` in front matter.
- **Change styling**: edit `src/assets/style.css`; the pipeline copies it to `public/assets/site/style.css` on every build.
- **Change nav / menu**: edit the `menu` list in `src/config.py`.
- **Before committing**: run `make pangu` so formatting is consistent, and eyeball `make build` output.

## Architecture

A hand-written, zero-dependency static site generator for a personal blog. Entry point is `src/cli.py`; the modules in `src/` use **flat imports** (e.g. `from builder import build`) which resolve because running the script puts `src/` on `sys.path`. So `src/` files must be run/imported with that directory as the working path — they are not a package.

### Build data flow (`builder.build()`)

```
content/posts/*.md  ──→ content_loader.load_posts()  ──→ ContentItem list (sorted: pinned, then date desc)
content/*.md        ──→ content_loader.load_pages()  ──→ ContentItem dict (keyed by stem)
src/config.py (SITE) ─→ config_loader ──→ SiteConfig     MarkdownEngine.render() turns body → body_html
src/templates/*.html ─→ template_runtime ({{ key }})      │
                                  builder writes public/: each post/page → <slug>/index.html
                                                       home (/), /blog/ list, atom.xml, sitemap.xml,
                                                       robots.txt, 404.html
```

`_write()` is a smart writer: it skips re-writing a file whose content is unchanged (preserves mtimes — matters for the watcher and incremental deploys).

### Key modules

- **`src/config.py`** — The only file to edit for site config. Defines a `SITE` dict (title, description, author, og_image, domain, icon, email, menu, server, `home_page`, `feed_months`). `description` feeds the homepage `<meta>`/Atom subtitle (defaults to `""`, in which case the homepage meta is auto-extracted from the home page body). `author` and `og_image` feed the JSON-LD markup. Loaded at runtime via `importlib`.
- **`src/cli.py`** — argparse + top-level orchestration. Build errors are caught and printed with suggestions (`_BUILD_ERRORS` map).
- **`src/content_loader.py`** — Custom front-matter parser (YAML-like, not PyYAML) and the markdown file loader. **Post slugs are CRC24 hashes of the filename stem, base36-encoded** — short, collision-resistant, and the original filename is not exposed in the URL. Because the hash is of the stem, **renaming a `.md` file changes its URL**. Reserved slugs (`assets`, `index`, `page`, `atom`) and collisions get a `-N` suffix. Also contains `pangu_format()` / `format_content()`.
- **`src/markdown_engine.py`** — A from-scratch markdown→HTML renderer (not a library). Supports headings (with slugged `id`), paragraphs, nested ordered/unordered/task lists, fenced code (`<pre><code>`, **no syntax highlighting**), tables, blockquotes with nested paragraphs, footnotes (`[^id]`), and inline code/links/images/bold/italic/strikethrough. Blank lines between list items are tolerated. Math (`$$…$$`/`$…$`) is preserved for **client-side KaTeX rendering**, not rendered here. Inline links/images are only emitted when the URL matches an allowlist (`https?://`, `mailto:`, `/`, `./`, `../`).
- **`src/template_runtime.py`** — `{{ placeholder }}` regex substitution over `src/templates/`. A missing key raises `KeyError` (surfaced by the CLI). Template file cache is cleared at the start of each build. `shell.html` wraps every page (head + header/nav + main). Posts append a `comment.html` footer using the site email.
- **`src/server.py`** — `ThreadingHTTPServer` dev server with live reload. Polls mtimes of `content/` and `src/` every 0.8s, rebuilds on change, and pushes reloads to browsers via SSE at `/__live_reload`. Injects a `<script>` before `</body>` in served HTML (dev only — not in build output).
- **`src/asset_pipeline.py`** — Copies `src/assets/`: `style.css` → `public/assets/site/style.css`; KaTeX (`src/assets/vendor/`) copied **only when `needs_math`** (at least one post/page has math), else removed; everything else (e.g. `favicon.ico`) copied straight to `public/`.
- **`src/models.py`** — `SiteConfig` and `ContentItem` dataclasses. Keep any new global site-level option (e.g. social/author fields) on `SiteConfig` and defaults on `ContentItem`.
- **`src/date_utils.py`** — `parse_date` (string→`date`, falls back to 1970-01-01) and `to_atom_date` for feeds.

> **Bytecode hygiene**: `src/__pycache__/` may accumulate stale `.pyc` files from scripts that were deleted (e.g. it currently contains `rclone.cpython-314.pyc` and `upload.cpython-314.pyc` with no matching `.py`). These are gitignored and harmless, but can be cleaned with `find src -name '__pycache__' -type d -prune -exec rm -rf {} +`.

### Static assets — two distinct paths

- **`src/assets/`** — managed by the pipeline (see above). CSS, KaTeX, favicon.
- **`static/`** (repo root) — user files, copied verbatim to `public/static/`. Images live here as `static/images/*.webp`. Posts reference them with **relative** paths like `../../static/images/<hash>.webp` (note the `../../`, since a post is served from `/<slug>/`).

### Content model

- **Posts**: `content/posts/<YYYY-MM-DD>-<name>.md`. **Drafts by default** (`draft: true`) — excluded from home, `/blog/`, and feeds. Delete the `draft` line to publish.
- **Pages**: top-level `content/*.md`, URL = stem. The page whose stem matches `home_page` (e.g. `index`) renders as the homepage at `/` instead of its own path.
- **`/blog/`** list page is auto-generated from all published posts.
- Front matter is parsed by a custom parser (scalars, `true/false`, ints, inline `[a, b]`, indented `- item`, `#` comments). Recognized keys: `title`, `date`, `draft`, `pinned` (sorts above date ordering on home + `/blog/`), `math` (force KaTeX even without `$`/`$$` — otherwise auto-detected by regex with code fences stripped), and `description` (overrides the auto-extracted page/post `<meta name="description">` and the JSON-LD `description`).

### SEO / structured data

- Every page emits `<meta description>`, Open Graph, Twitter Card, and `canonical`.
- Posts emit `BlogPosting` JSON-LD (with `author`, `image`/`publisher`/`logo`); regular pages emit `WebPage`; the homepage emits `Person` + `WebSite` JSON-LD.
- `og_image` in `src/config.py` feeds the schema `image`/`logo` (and should point at a real 1200×630 social card); `favicon.ico` is the fallback placeholder.
- `sitemap.xml` lists the home page, `/blog/`, every post, and every non-home page.

## Deployment

GitHub Actions (`.github/workflows/deploy.yml`) on push to `main`: `make build` → deploy `public/` to GitHub Pages, using `actions/setup-python@v6` with Python 3.12. `public/` is the Pages artifact and is not committed. The build needs no network access — it is fully offline-safe.
