from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .settings import CACHE_DIR
from .utils import normalize_name


def build_availability_rows(audit: dict[str, Any], cache_dir: Path = CACHE_DIR) -> list[dict[str, Any]]:
    rows = []
    for prediction in audit.get("predictions", []) or []:
        event_id = str(prediction.get("event_id", ""))
        roster_counts = espn_roster_counts(event_id, cache_dir)
        api_football = prediction.get("api_football") or {}
        injury_count = detail_count(api_football, "injuries")
        lineup_count = detail_count(api_football, "lineups")
        player_stats_count = detail_count(api_football, "player_stats")
        home = prediction.get("home", {}).get("name", "")
        away = prediction.get("away", {}).get("name", "")
        risk_notes = [
            note for note in prediction.get("news_notes", []) or []
            if note.get("risk_terms") and note_mentions_team(note, home, away)
        ]
        status = availability_status(roster_counts, lineup_count, risk_notes)
        rows.append(
            {
                "generated_at_utc": audit.get("generated_at_utc"),
                "event_id": event_id,
                "kickoff_utc": prediction.get("match_utc"),
                "match": prediction.get("match"),
                "forecast_status": prediction.get("forecast_status"),
                "home": home,
                "away": away,
                "home_roster_count": roster_counts.get("home"),
                "away_roster_count": roster_counts.get("away"),
                "api_football_fixture_id": api_football.get("fixture_id"),
                "api_injury_count": injury_count,
                "api_lineup_count": lineup_count,
                "api_player_stats_count": player_stats_count,
                "risk_news_count": len(risk_notes),
                "risk_news_terms": "; ".join(sorted({note.get("risk_terms", "") for note in risk_notes if note.get("risk_terms")})),
                "availability_status": status,
                "confidence_penalty": confidence_penalty(status, len(risk_notes)),
                "manual_check_required": manual_check_required(prediction.get("forecast_status"), status),
                "notes": availability_notes(api_football, roster_counts, status),
            }
        )
    return rows


def espn_roster_counts(event_id: str, cache_dir: Path = CACHE_DIR) -> dict[str, int | None]:
    path = cache_dir / f"espn_summary_{event_id}.json"
    if not path.exists():
        return {"home": None, "away": None}
    data = json.loads(path.read_text(encoding="utf-8"))
    counts = {"home": None, "away": None}
    for roster in data.get("rosters", []) or []:
        side = roster.get("homeAway")
        if side in counts:
            counts[side] = len(roster.get("roster", []) or [])
    return counts


def detail_count(api_football: dict[str, Any], key: str) -> int:
    value = api_football.get(key)
    if isinstance(value, dict):
        return int(value.get("count") or 0)
    if isinstance(value, list):
        return len(value)
    return 0


def note_mentions_team(note: dict[str, Any], home: str, away: str) -> bool:
    text = normalize_name(" ".join(str(note.get(key, "")) for key in ("headline", "url")))
    home_key = normalize_name(home)
    away_key = normalize_name(away)
    return bool((home_key and home_key in text) or (away_key and away_key in text))


def availability_status(
    roster_counts: dict[str, int | None],
    lineup_count: int,
    risk_notes: list[dict[str, Any]],
) -> str:
    if lineup_count > 0:
        return "api_lineups_available"
    home_count = roster_counts.get("home") or 0
    away_count = roster_counts.get("away") or 0
    if home_count > 0 and away_count > 0:
        return "espn_rosters_available"
    if risk_notes:
        return "news_risk_only"
    return "missing_structured_player_data"


def confidence_penalty(status: str, risk_news_count: int) -> float:
    base = {
        "api_lineups_available": 0.00,
        "espn_rosters_available": 0.02,
        "news_risk_only": 0.05,
        "missing_structured_player_data": 0.05,
    }.get(status, 0.05)
    return min(0.10, base + 0.02 * risk_news_count)


def manual_check_required(forecast_status: str | None, status: str) -> bool:
    if forecast_status != "pre_match":
        return False
    return status != "api_lineups_available"


def availability_notes(
    api_football: dict[str, Any],
    roster_counts: dict[str, int | None],
    status: str,
) -> str:
    if status == "api_lineups_available":
        return "API-Football lineups/details available before kickoff."
    if status == "espn_rosters_available":
        return "ESPN rosters available, but lineups are not confirmed."
    if api_football.get("fixture_id") is None:
        return "No API-Football fixture mapping; use manual lineup check near kickoff."
    if roster_counts.get("home") == 0 or roster_counts.get("away") == 0:
        return "No structured roster/lineup data yet; use manual lineup check near kickoff."
    return "Structured player availability is incomplete."
