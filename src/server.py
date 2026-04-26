from __future__ import annotations

import os
import queue
from pathlib import Path
from threading import Event, Lock, Thread
from urllib.parse import urlsplit
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from builder import build


_LIVE_RELOAD_SNIPPET = """
<script>
(() => {
  const es = new EventSource("/__live_reload");
  es.onmessage = () => window.location.reload();
  addEventListener("beforeunload", () => es.close());
})();
</script>
"""


class _LiveReloadHub:
    def __init__(self) -> None:
        self._lock = Lock()
        self._subs: list[queue.Queue[None]] = []

    def subscribe(self) -> queue.Queue[None]:
        q: queue.Queue[None] = queue.Queue()
        with self._lock:
            self._subs.append(q)
        return q

    def unsubscribe(self, q: queue.Queue[None]) -> None:
        with self._lock:
            if q in self._subs:
                self._subs.remove(q)

    def notify(self) -> None:
        with self._lock:
            subs = list(self._subs)
        for q in subs:
            q.put_nowait(None)


def _inject_live_reload(html_text: str) -> str:
    idx = html_text.rfind("</body>")
    if idx < 0:
        return html_text + _LIVE_RELOAD_SNIPPET
    return html_text[:idx] + _LIVE_RELOAD_SNIPPET + html_text[idx:]


def _scan_source_mtimes(root: Path) -> dict[str, int]:
    mtimes: dict[str, int] = {}
    for base in (root / "content", root / "src"):
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for name in filenames:
                p = Path(dirpath) / name
                try:
                    mtimes[str(p)] = p.stat().st_mtime_ns
                except FileNotFoundError:
                    continue
    return mtimes


def _watch_and_rebuild(root: Path, hub: _LiveReloadHub, stop: Event) -> None:
    last = _scan_source_mtimes(root)
    while not stop.wait(0.8):
        current = _scan_source_mtimes(root)
        if current == last:
            continue
        last = current
        try:
            build(root)
        except Exception as exc:
            print(f"Rebuild failed: {exc}")
            continue
        print("Rebuilt after changes.")
        hub.notify()


def serve(public_dir: Path, host: str, port: int, root: Path) -> None:
    stop = Event()
    hub = _LiveReloadHub()
    watcher = Thread(target=_watch_and_rebuild, args=(root, hub, stop), daemon=True)
    watcher.start()

    class PreviewHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(public_dir), **kwargs)

        _CACHE_FOR = {"image/": 86400, "font/": 86400, "text/css": 86400, "application/javascript": 86400}

        def _resolved_html_path(self) -> Path | None:
            req_path = urlsplit(self.path).path
            fs_path = Path(self.translate_path(req_path))
            if fs_path.is_dir():
                fs_path = fs_path / "index.html"
            if fs_path.exists() and fs_path.suffix.lower() == ".html":
                return fs_path
            return None

        def _guess_mime(self, path: Path) -> str:
            ext = path.suffix.lower()
            return {
                ".html": "text/html",
                ".css": "text/css",
                ".js": "application/javascript",
                ".json": "application/json",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
                ".ico": "image/x-icon",
                ".woff2": "font/woff2",
                ".woff": "font/woff",
                ".ttf": "font/ttf",
                ".otf": "font/otf",
                ".xml": "application/xml",
                ".txt": "text/plain",
            }.get(ext, "application/octet-stream")

        def _serve_file(self, fs_path: Path) -> None:
            mime = self._guess_mime(fs_path)
            payload = fs_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime + "; charset=utf-8" if mime.startswith("text/") else mime)
            self.send_header("Content-Length", str(len(payload)))
            cache_age = next((v for k, v in self._CACHE_FOR.items() if mime.startswith(k)), None)
            if mime == "text/html":
                self.send_header("Cache-Control", "no-store")
            elif cache_age:
                self.send_header("Cache-Control", f"public, max-age={cache_age}")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            if urlsplit(self.path).path == "/__live_reload":
                self._serve_live_reload()
                return

            html_path = self._resolved_html_path()
            if html_path is not None:
                payload = _inject_live_reload(html_path.read_text(encoding="utf-8")).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(payload)
                return

            req_path = urlsplit(self.path).path
            fs_path = Path(self.translate_path(req_path))
            if fs_path.exists() and fs_path.is_file():
                self._serve_file(fs_path)
                return

            super().do_GET()

        def _serve_live_reload(self) -> None:
            q = hub.subscribe()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            try:
                while not stop.is_set():
                    try:
                        q.get(timeout=15)
                        self.wfile.write(b"data: reload\n\n")
                    except queue.Empty:
                        self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                hub.unsubscribe(q)

    with ThreadingHTTPServer((host, port), PreviewHandler) as httpd:
        print(f"Serving {public_dir} at http://{host}:{port}")
        try:
            httpd.serve_forever()
        finally:
            stop.set()
