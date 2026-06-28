from __future__ import annotations

import json
import re
from typing import Any
import urllib.error
import urllib.request

from .settings import CACHE_DIR, USER_AGENT


SENSITIVE_QUERY_KEYS = ("apikey", "api_key", "key", "token", "access_token")


def redact_url(url: str) -> str:
    """Hide common secret query parameters before errors reach logs or audits."""
    pattern = r"([?&](" + "|".join(SENSITIVE_QUERY_KEYS) + r")=)[^&]+"
    return re.sub(pattern, r"\1REDACTED", url, flags=re.IGNORECASE)


def fetch_bytes_with_meta(
    url: str,
    cache_name: str,
    headers: dict[str, str] | None = None,
) -> tuple[bytes, dict[str, str], bool]:
    cache_path = CACHE_DIR / cache_name
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(url, headers=request_headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
            headers = {key.lower(): value for key, value in response.headers.items()}
        cache_path.write_bytes(data)
        return data, headers, False
    except (urllib.error.URLError, TimeoutError) as exc:
        if cache_path.exists():
            return cache_path.read_bytes(), {}, True
        raise RuntimeError(f"Could not fetch {redact_url(url)}: {exc}") from exc


def fetch_bytes(url: str, cache_name: str) -> bytes:
    data, _, _ = fetch_bytes_with_meta(url, cache_name)
    return data

def fetch_text(url: str, cache_name: str) -> str:
    data = fetch_bytes(url, cache_name)
    return data.decode("utf-8", errors="replace")

def fetch_json_with_meta(
    url: str,
    cache_name: str,
    headers: dict[str, str] | None = None,
) -> tuple[Any, dict[str, str], bool]:
    data, headers, from_cache = fetch_bytes_with_meta(url, cache_name, headers)
    return json.loads(data.decode("utf-8", errors="replace")), headers, from_cache


def fetch_json(url: str, cache_name: str) -> Any:
    text = fetch_text(url, cache_name)
    return json.loads(text)

