from __future__ import annotations

import urllib.parse
from typing import Any

from .http_client import fetch_text
from .settings import ELO_BASE, TEAM_ALIASES
from .utils import normalize_name, safe_int

def load_elo_dictionary() -> tuple[dict[str, str], dict[str, str]]:
    text = fetch_text(f"{ELO_BASE}/en.teams.tsv", "elo_en_teams.tsv")
    name_to_code: dict[str, str] = {}
    canonical_by_code: dict[str, str] = {}
    for raw_line in text.splitlines():
        parts = raw_line.strip().split("\t")
        if len(parts) < 2 or parts[0].endswith("_loc"):
            continue
        code = parts[0]
        canonical_by_code[code] = parts[1]
        for alias in parts[1:]:
            if alias:
                name_to_code[normalize_name(alias)] = code
    return name_to_code, canonical_by_code

def load_elo_for_teams(team_names: list[str]) -> dict[str, dict[str, Any]]:
    name_to_code, canonical_by_code = load_elo_dictionary()
    elo_map: dict[str, dict[str, Any]] = {}
    for team in team_names:
        elo_name = TEAM_ALIASES.get(team, team)
        code = name_to_code.get(normalize_name(elo_name))
        if not code:
            elo_map[team] = {"available": False, "reason": "no name match"}
            continue
        canonical = canonical_by_code[code]
        page = urllib.parse.quote(canonical.replace(" ", "_"), safe="_")
        try:
            text = fetch_text(f"{ELO_BASE}/{page}.tsv", f"elo_{page}.tsv")
            rating = parse_latest_elo(text, code)
            rating.update(
                {
                    "available": True,
                    "code": code,
                    "elo_name": canonical,
                    "url": f"{ELO_BASE}/{page}",
                }
            )
            elo_map[team] = rating
        except Exception as exc:  # Keep the model running if one Elo page is missing.
            elo_map[team] = {"available": False, "reason": str(exc), "code": code, "elo_name": canonical}
    return elo_map

def parse_latest_elo(text: str, code: str) -> dict[str, Any]:
    for line in reversed(text.splitlines()):
        parts = line.strip().split("\t")
        if len(parts) < 12:
            continue
        home_code, away_code = parts[3], parts[4]
        if code not in (home_code, away_code):
            continue
        if code == home_code:
            rating = safe_int(parts[10])
            rank = safe_int(parts[14], 0) if len(parts) > 14 else 0
        else:
            rating = safe_int(parts[11])
            rank = safe_int(parts[15], 0) if len(parts) > 15 else 0
        return {
            "rating": rating,
            "rank": rank,
            "date": f"{parts[0]}-{parts[1]}-{parts[2]}",
            "last_match": line.strip(),
        }
    raise ValueError(f"No Elo rows found for code {code}")

