# Repository Guidelines

A hand-written, zero-dependency Python static site generator for a personal blog. Markdown in `content/` is built into a static site in `public/`, deployed to GitHub Pages by GitHub Actions on every push to `main`. There are no tests, no linter and no formatter for the source.

## Project Structure & Module Organization

- **`src/`** — the generator. Entry point is `src/cli.py`; modules use flat imports (e.g. `from builder import build`) and must be run from the repo root, not as a package. Error messages live in the CLI's `_BUILD_ERRORS` map.
- **`content/`** — content. Posts live at `content/posts/<YYYY-MM-DD>-<name>.md`; pages live as top-level `content/<stem>.md` served at `/<stem>/`.
- **`src/templates/`** — HTML templates; `shell.html` wraps every page, `{{ key }}` substitution raises `KeyError` on a missing key.
- **`src/assets/`** — managed assets (`style.css`, favicon, KaTeX) copied on build; KaTeX is copied only when some post or page needs math.
- **`static/`** — user files copied verbatim; images at `static/images/*.webp`, referenced from posts with a relative `../../static/images/<hash>.webp`.
- **`public/`** — build output, gitignored and never committed.

Post URLs are the CRC24 hash of the filename stem, base36-encoded, so renaming a `.md` file changes its URL.

## Build, Test, and Development Commands

From the repo root:

```bash
make                        # build + serve on port 1313 with live reload
make build                  # build the static site into public/
make new NAME=2026-04-18-my-post  # create a new draft post
make pangu                  # format all posts in-place (pangu spacing, whitespace)
```

The equivalent CLI is `python src/cli.py` with `-s` (serve), `-d` (build), `-n NAME` (new), `-f` (format), `-p PORT`, `-H HOST`.

## Coding Style & Naming Conventions

- **Python:** stdlib only — do not add dependencies. Keep code compatible with Python 3.12 (CI) and 3.14 (local). Use 4-space indentation and type hints.
- **Posts:** lowercase hyphenated filenames with a date prefix (`2026-04-18-my-post.md`). Drafts are default (`draft: true`) and stay out of the home page, `/blog/` and the feeds; delete that line to publish.
- **Front matter** uses a custom YAML-like parser (no PyYAML). Recognized keys: `title`, `date`, `draft`, `pinned`, `math`, `description`. `description` overrides the auto-extracted `<meta name="description">` — otherwise the opening of the body is used, so the first paragraph has to stand on its own as a summary.
- **Site config:** `src/config.py` is the only file to edit for site-level options (`description`, `author`, `og_image`, `menu`, `home_page`, server port).
- **Source:** no linter or formatter is configured; run `make pangu` to keep content consistent.

## Testing Guidelines

There is no test framework or suite. Verify changes by running `make build` and inspecting the generated HTML under `public/<slug>/index.html`. Since the build is offline-safe and dependency-free, manual review of `public/` output is the expected check. The dev server polls `content/` and `src/` mtimes, so a running `make serve` picks edits up on its own.

## SEO & Deployment

- Every page emits `<meta description>`, Open Graph, Twitter Card and `canonical`; posts emit `BlogPosting` JSON-LD, regular pages `WebPage`, the homepage `Person` + `WebSite`.
- `og_image` in `src/config.py` should point at a real 1200×630 social card.
- `sitemap.xml` lists the home page, `/blog/`, every post and every non-home page.
- GitHub Actions (`.github/workflows/deploy.yml`) runs `make build` on push to `main` and deploys `public/` to GitHub Pages with Python 3.12.

## Commit & Pull Request Guidelines

One concise line per commit: a lowercase imperative subject, no prefix and no body. Older history also carries Conventional Commit prefixes such as `feat(seo): ...`; either way keep the subject imperative and short.

Before committing, run `make pangu` and `make build` so formatting is consistent and the site still builds. For pull requests, describe what changed and why, link any related issue, and note config or front-matter changes. Pushing commits, branches or tags outward needs the user's explicit go-ahead.
