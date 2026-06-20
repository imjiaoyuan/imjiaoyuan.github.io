SITE = {
    "title": "JiaoYuan's blog",
    "domain": "https://jiaoyuan.org",
    "description": "Master's student in Bioinformatics at Sichuan University.",
    "icon": "/favicon.ico",
    "home_limit": 30,

    "content_dir": "content",
    "static_dir": "src/assets",
    "public_dir": "public",
    "menu": [
        {"name": "Readme", "url": "/readme"},
        {"name": "GitHub", "url": "https://github.com/imjiaoyuan"},
        {"name": "RSS", "url": "/atom.xml"},
    ],
    "theme_options": {
        "giscus": {
            "repo": "imjiaoyuan/imjiaoyuan.github.io",
            "repo_id": "YOUR_REPO_ID",
            "category": "Announcements",
            "category_id": "YOUR_CATEGORY_ID",
        },
    },
    "r2_remote": "r2:static/blog/images",
    "r2_base_url": "https://static.jiaoyuan.org/blog/images",
    "server": {"host": "127.0.0.1", "port": 1313},
}
