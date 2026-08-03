JiaoYuan's blog

## Local usage

```bash
make                        # live rebuild + auto refresh (default)
make build                  # build static site
make new NAME=2026-04-18-new-post  # create new post
make pangu                  # format all posts
```

New posts are created as flat files under `content/posts/<name>.md`.
Posts are **drafts by default** (`draft: true` in front matter) and hidden from the homepage. Remove the `draft` line to publish.

## Front matter

```yaml
---
title: My Post Title
date: 2026-06-20
draft: true       # delete this line to publish
pinned: true      # optional, pin to top of homepage
---
```
