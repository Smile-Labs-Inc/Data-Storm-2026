"""Step 1: download the Geofabrik Sri Lanka OSM PBF.

Idempotent: skips if the file already exists with non-zero size.

Usage (no CLI flags -- edit `config.py`):
    python 01_download_pbf.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import PBF_PATH, PBF_URL, ensure_dirs


def download(url: str, dest: Path, chunk_size: int = 1 << 16) -> None:
    print(f"[poi] downloading {url}")
    print(f"[poi]   -> {dest}")
    t0 = time.time()
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        last_print = t0
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                now = time.time()
                if now - last_print > 2.0 and total:
                    pct = 100.0 * downloaded / total
                    rate = downloaded / 1024 / 1024 / max(now - t0, 0.1)
                    print(f"[poi]   {pct:5.1f}%  {downloaded / 1e6:7.1f} MB  ({rate:5.1f} MB/s)")
                    last_print = now
    print(f"[poi]   done in {time.time() - t0:.1f}s, size={dest.stat().st_size / 1e6:.1f} MB")


def main() -> None:
    ensure_dirs()
    if PBF_PATH.exists() and PBF_PATH.stat().st_size > 1_000_000:
        print(f"[poi] {PBF_PATH.name} already present ({PBF_PATH.stat().st_size / 1e6:.1f} MB), skipping")
        return
    download(PBF_URL, PBF_PATH)


if __name__ == "__main__":
    main()
