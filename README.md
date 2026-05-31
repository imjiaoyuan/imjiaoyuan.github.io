JiaoYuan's blog

## Local usage

```bash
python run.py -d                 # build static site
python run.py -s                 # live rebuild + auto refresh
python run.py -s -p 8080         # serve on custom port
python run.py -s -H 0.0.0.0      # serve on custom host
python run.py -n 2026-04-18-new-post  # create new post
python run.py -f                 # format all posts
python run.py -h                 # help
```

New posts are created under `content/posts/<name>/`.
