JiaoYuan's blog

## Local usage

```bash
python run.py -d                 # build static site
python run.py -s                 # live rebuild + auto refresh
python run.py -s -p 8080         # serve on custom port
python run.py -s -H 0.0.0.0      # serve on custom host
python run.py -n 2026-04-18-new-post  # create new post
python run.py -f                 # format all posts
python run.py -u image.png       # upload image to R2 (auto webp, prints URL)
python run.py -h                 # help
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
