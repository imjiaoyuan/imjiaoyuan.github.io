# Copilot Instructions for `imjiaoyuan.github.io`

## Build, test, and lint

This repository is a Hugo site (theme: PaperMod). The production build command used in CI is:

```bash
hugo --gc --minify --baseURL "https://jiaoyuan.org/"
```

Useful local commands:

```bash
# local preview
hugo server

# include draft content while previewing
hugo server -D
```

There is currently no dedicated test suite or linter configured in this repository (no project-level test/lint scripts or Makefile targets), so there is no single-test command to run.

## High-level architecture

- Site configuration is centralized in `hugo.toml` (base URL, menus, pagination, theme params, markup/highlight settings).
- Content is split into:
  - `content/posts/**/index.md`: long-form posts as Hugo **leaf bundles** (each post folder contains `index.md` plus an `assets/` folder for post-local media).
  - `content/logs/*.md`: short log entries.
  - `content/logs/_index.md`: section index wired to a custom layout (`layout: "logs"`).
- Theme code is committed under `themes/PaperMod/` and includes customizations used by this site:
  - `themes/PaperMod/layouts/logs/list.html`: custom rendering for `/logs` (sorts by filename date and paginates).
  - `themes/PaperMod/assets/css/extended/log.css`: styling for log cards/date rows.
  - `themes/PaperMod/layouts/partials/extend_head.html`: optional head extension area (currently commented KaTeX include).
- Deployment is GitHub Pages via `.github/workflows/hugo.yml`:
  - Hugo Extended `0.119.0`
  - build + upload artifact from `public/`
  - deploy with `actions/deploy-pages`

## Key conventions in this codebase

- **Post path convention:** posts live in date-prefixed directories like `content/posts/YYYY-MM-DD-slug/index.md`.
- **Post media convention:** images/files for a post are colocated under that post’s `assets/` folder and referenced with relative paths (`assets/...` or `./assets/...`).
- **Front matter convention:** most posts keep front matter minimal (`title`, `date`); extra metadata like `categories` is optional and used sparingly.
- **Logs convention:** log entries are plain markdown files named by date (for example `2026-03-13.md`), and the logs layout displays `File.TranslationBaseName` as the visible log date.
- **Menu/navigation convention:** top-level navigation (for example `LOGS`, `ARCHIVES`, `README`) is configured in `hugo.toml` under `[menu.main]`, not inferred from folder names.
