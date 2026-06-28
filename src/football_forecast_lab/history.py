from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


REQUIRED_HISTORY_COLUMNS = {
    "date",
    "competition",
    "home",
    "away",
    "home_score",
    "away_score",
}


def load_historical_matches(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    missing = REQUIRED_HISTORY_COLUMNS - set(rows[0].keys() if rows else [])
    if missing:
        raise ValueError(f"Historical file is missing columns: {sorted(missing)}")
    return rows


def actual_outcome(row: dict[str, Any]) -> str:
    home = int(row["home_score"])
    away = int(row["away_score"])
    if home > away:
        return "home"
    if home < away:
        return "away"
    return "draw"
