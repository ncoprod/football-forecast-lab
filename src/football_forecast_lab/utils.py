from __future__ import annotations

import math
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).astimezone(timezone.utc)

def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = value.replace("&", "and")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    if "Ã" in text or "Â" in text or "â" in text:
        try:
            repaired = text.encode("latin1").decode("utf-8")
            if "�" not in repaired and repaired.count("Ã") <= text.count("Ã"):
                return repaired
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return text

def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{100 * value:.1f}%"

def fmt_float(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def logistic_base10(diff: float, scale: float = 400.0) -> float:
    return 1.0 / (1.0 + 10 ** (-diff / scale))

def elo_diff_from_probability(probability: float, scale: float = 400.0) -> float:
    probability = clamp(probability, 0.03, 0.97)
    return scale * math.log10(probability / (1.0 - probability))

def serialize_datetimes(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: serialize_datetimes(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize_datetimes(item) for item in value]
    return value

