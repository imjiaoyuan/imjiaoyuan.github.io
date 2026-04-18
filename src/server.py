from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def serve(public_dir: Path, host: str, port: int) -> None:
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=str(public_dir), **kwargs)
    with ThreadingHTTPServer((host, port), handler) as httpd:
        print(f"Serving {public_dir} at http://{host}:{port}")
        httpd.serve_forever()
