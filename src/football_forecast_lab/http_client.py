from __future__ import annotations

import json
import urllib.error
import urllib.request

from .settings import CACHE_DIR, USER_AGENT

def fetch_bytes(url: str, cache_name: str) -> bytes:
    cache_path = CACHE_DIR / cache_name
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
        cache_path.write_bytes(data)
        return data
    except (urllib.error.URLError, TimeoutError) as exc:
        if cache_path.exists():
            return cache_path.read_bytes()
        raise RuntimeError(f"Could not fetch {url}: {exc}") from exc

def fetch_text(url: str, cache_name: str) -> str:
    data = fetch_bytes(url, cache_name)
    return data.decode("utf-8", errors="replace")

def fetch_json(url: str, cache_name: str) -> dict[str, Any]:
    text = fetch_text(url, cache_name)
    return json.loads(text)

