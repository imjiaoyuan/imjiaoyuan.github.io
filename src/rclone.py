import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

PRIME1 = 0x9E3779B1
PRIME2 = 0x85EBCA77
PRIME3 = 0xC2B2AE3D
PRIME4 = 0x27D4EB2F
PRIME5 = 0x165667B1

_IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".bmp", ".ico", ".avif"})


def xxh32(data: bytes, seed: int = 0) -> int:
    n = len(data)
    h32 = (seed + PRIME5 + n) & 0xFFFFFFFF
    if n < 16:
        p = 0
        while p + 4 <= n:
            h32 = (h32 + struct.unpack_from('<I', data, p)[0] * PRIME3) & 0xFFFFFFFF
            h32 = ((h32 << 17) | (h32 >> 15)) & 0xFFFFFFFF
            h32 = (h32 * PRIME4) & 0xFFFFFFFF
            p += 4
        while p < n:
            h32 = (h32 + data[p] * PRIME5) & 0xFFFFFFFF
            h32 = ((h32 << 11) | (h32 >> 21)) & 0xFFFFFFFF
            h32 = (h32 * PRIME1) & 0xFFFFFFFF
            p += 1
    else:
        v1 = (seed + PRIME1 + PRIME2) & 0xFFFFFFFF
        v2 = (seed + PRIME2) & 0xFFFFFFFF
        v3 = seed & 0xFFFFFFFF
        v4 = (seed - PRIME1) & 0xFFFFFFFF
        p = 0
        limit = n - 16
        while p <= limit:
            for vi in range(4):
                lane = struct.unpack_from('<I', data, p)[0]
                p += 4
                if vi == 0:
                    v1 = (v1 + lane * PRIME2) & 0xFFFFFFFF
                    v1 = ((v1 << 13) | (v1 >> 19)) & 0xFFFFFFFF
                    v1 = (v1 * PRIME1) & 0xFFFFFFFF
                elif vi == 1:
                    v2 = (v2 + lane * PRIME2) & 0xFFFFFFFF
                    v2 = ((v2 << 13) | (v2 >> 19)) & 0xFFFFFFFF
                    v2 = (v2 * PRIME1) & 0xFFFFFFFF
                elif vi == 2:
                    v3 = (v3 + lane * PRIME2) & 0xFFFFFFFF
                    v3 = ((v3 << 13) | (v3 >> 19)) & 0xFFFFFFFF
                    v3 = (v3 * PRIME1) & 0xFFFFFFFF
                else:
                    v4 = (v4 + lane * PRIME2) & 0xFFFFFFFF
                    v4 = ((v4 << 13) | (v4 >> 19)) & 0xFFFFFFFF
                    v4 = (v4 * PRIME1) & 0xFFFFFFFF
        h32 = ((v1 << 1) | (v1 >> 31)) & 0xFFFFFFFF
        h32 = (h32 + ((v2 << 7) | (v2 >> 25))) & 0xFFFFFFFF
        h32 = (h32 + ((v3 << 12) | (v3 >> 20))) & 0xFFFFFFFF
        h32 = (h32 + ((v4 << 18) | (v4 >> 14))) & 0xFFFFFFFF
        while p < n:
            lane = struct.unpack_from('<I', data[p:p+4].ljust(4, b'\x00'), 0)[0]
            h32 = (h32 + lane * PRIME3) & 0xFFFFFFFF
            h32 = ((h32 << 17) | (h32 >> 15)) & 0xFFFFFFFF
            h32 = (h32 * PRIME4) & 0xFFFFFFFF
            p += 4
    h32 ^= n
    h32 ^= (h32 >> 15)
    h32 = (h32 * PRIME2) & 0xFFFFFFFF
    h32 ^= (h32 >> 13)
    h32 = (h32 * PRIME3) & 0xFFFFFFFF
    h32 ^= (h32 >> 16)
    return h32


def _check_cmd(name: str) -> None:
    if shutil.which(name) is None:
        sys.exit(f"Error: '{name}' is required but not found. Please install it first.")


def _to_webp(filepath: Path) -> Path:
    if filepath.suffix.lower() == ".webp":
        return filepath
    _check_cmd("magick")
    out = filepath.with_suffix(".webp")
    subprocess.run(
        ["magick", str(filepath), "-quality", "85", str(out)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return out


def _resolve_remote_path(identifier: str, remote: str, base_url: str) -> str:
    if identifier.startswith("http://") or identifier.startswith("https://"):
        parsed = urlparse(identifier)
        url_path = parsed.path.lstrip("/")
        base_path = urlparse(base_url).path.lstrip("/")
        if base_path and url_path.startswith(base_path + "/"):
            rel = url_path[len(base_path) + 1:]
        elif base_path and url_path == base_path:
            rel = ""
        else:
            rel = Path(parsed.path).name
    else:
        rel = identifier.lstrip("/")
    if not rel:
        raise ValueError(f"Cannot resolve remote path from: {identifier}")
    return f"{remote}/{rel}"


def upload(filepath: Path, remote: str, base_url: str) -> str:
    _check_cmd("rclone")
    ext = filepath.suffix.lower()

    if ext in _IMAGE_EXTS:
        webp = _to_webp(filepath)
        data = webp.read_bytes()
        name = f"{xxh32(data):08x}.webp"
        remote_path = f"{remote}/images/{name}"
        url = f"{base_url.rstrip('/')}/images/{name}"
    else:
        webp = filepath
        data = filepath.read_bytes()
        name = f"{xxh32(data):08x}{ext}"
        remote_path = f"{remote}/{name}"
        url = f"{base_url.rstrip('/')}/{name}"

    tmp = Path(tempfile.gettempdir()) / name
    try:
        shutil.copy(webp, tmp)
        subprocess.run(
            ["rclone", "copyto", str(tmp), remote_path],
            check=True,
        )
    finally:
        if tmp.exists():
            tmp.unlink()
        if webp != filepath and webp.exists():
            webp.unlink()

    return url


def delete(identifier: str, remote: str, base_url: str) -> str:
    _check_cmd("rclone")
    remote_path = _resolve_remote_path(identifier, remote, base_url)
    subprocess.run(
        ["rclone", "delete", remote_path],
        check=True,
    )
    return remote_path


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: python {__file__} <file> [file...]")
        sys.exit(1)

    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "src"))
    from config_loader import load_site_config

    cfg = load_site_config(root)
    remote = cfg.r2_remote
    base_url = cfg.r2_base_url

    for arg in sys.argv[1:]:
        url = upload(Path(arg).resolve(), remote, base_url)
        print(url)


if __name__ == "__main__":
    main()
