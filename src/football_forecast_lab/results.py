from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .espn import event_competitors
from .utils import parse_dt


FINAL_SCORE_SCOPE = "espn_final_score"


def completed_event_result_rows(
    scoreboard: dict[str, Any],
    source_url: str,
    resolved_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    """Extract completed match results from an ESPN scoreboard payload."""
    resolved_at = resolved_at_utc or datetime.now(UTC).isoformat()
    rows: list[dict[str, Any]] = []
    for event in scoreboard.get("events", []) or []:
        competition = (event.get("competitions") or [{}])[0]
        status = competition.get("status") or event.get("status") or {}
        status_type = status.get("type") or {}
        if not status_type.get("completed"):
            continue

        competitors = event_competitors(event)
        if "home" not in competitors or "away" not in competitors:
            continue

        home = competitors["home"]
        away = competitors["away"]
        rows.append(
            {
                "resolved_at_utc": resolved_at,
                "event_id": str(event.get("id")),
                "match_utc": _iso_or_empty(event.get("date")),
                "home": home.get("name", ""),
                "away": away.get("name", ""),
                "actual_home_score": int(home.get("score", 0)),
                "actual_away_score": int(away.get("score", 0)),
                "actual_score_scope": FINAL_SCORE_SCOPE,
                "actual_result": score_outcome(int(home.get("score", 0)), int(away.get("score", 0))),
                "status": status_type.get("name") or "",
                "status_detail": status_type.get("detail") or status_type.get("shortDetail") or "",
                "source": "espn_scoreboard",
                "source_url": source_url,
            }
        )
    return rows


def score_outcome(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "home"
    if home_score < away_score:
        return "away"
    return "draw"


def _iso_or_empty(value: Any) -> str:
    parsed = parse_dt(value)
    return parsed.isoformat() if parsed else ""
