from __future__ import annotations

from collections import defaultdict
from typing import Any

from .utils import parse_dt


OUTCOMES = ("home", "draw", "away")


def build_odds_movement_rows(snapshot_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in snapshot_rows:
        event_id = str(row.get("event_id", ""))
        if event_id:
            grouped[event_id].append(row)

    output = []
    for event_id, rows in grouped.items():
        ordered = sorted(rows, key=lambda row: row.get("generated_at_utc", ""))
        first = ordered[0]
        latest = ordered[-1]
        latest_market = latest.get("market") or {}
        first_market = first.get("market") or {}
        latest_probs = probability_triplet(latest_market)
        first_probs = probability_triplet(first_market)
        strongest = strongest_h2h_move(first_probs, latest_probs)
        latest_total = total_probability(latest_market)
        first_total = total_probability(first_market)
        output.append(
            {
                "event_id": event_id,
                "match": f"{latest.get('home')} - {latest.get('away')}",
                "home": latest.get("home"),
                "away": latest.get("away"),
                "kickoff_utc": latest.get("kickoff_utc"),
                "snapshots": len(ordered),
                "first_generated_at_utc": first.get("generated_at_utc"),
                "latest_generated_at_utc": latest.get("generated_at_utc"),
                "minutes_to_kickoff_latest": minutes_between(latest.get("generated_at_utc"), latest.get("kickoff_utc")),
                "p_home_first": first_probs.get("home"),
                "p_home_latest": latest_probs.get("home"),
                "p_home_move": probability_move(first_probs, latest_probs, "home"),
                "p_draw_first": first_probs.get("draw"),
                "p_draw_latest": latest_probs.get("draw"),
                "p_draw_move": probability_move(first_probs, latest_probs, "draw"),
                "p_away_first": first_probs.get("away"),
                "p_away_latest": latest_probs.get("away"),
                "p_away_move": probability_move(first_probs, latest_probs, "away"),
                "strongest_h2h_move": strongest["outcome"],
                "strongest_h2h_move_points": strongest["points"],
                "total_line_first": first_total.get("line"),
                "total_line_latest": latest_total.get("line"),
                "p_over_first": first_total.get("over"),
                "p_over_latest": latest_total.get("over"),
                "p_over_move": numeric_delta(first_total.get("over"), latest_total.get("over")),
                "latest_bookmaker_count": bookmaker_count(latest_market),
                "latest_provider": latest_market.get("provider", ""),
                "quota_remaining": latest_quota_remaining(latest),
            }
        )
    return sorted(output, key=lambda row: (row.get("kickoff_utc") or "", row.get("match") or ""))


def probability_triplet(market: dict[str, Any]) -> dict[str, float | None]:
    values = market.get("moneyline_fair") or {}
    return {outcome: safe_probability(values.get(outcome)) for outcome in OUTCOMES}


def total_probability(market: dict[str, Any]) -> dict[str, float | None]:
    external = market.get("external_totals_fair") or {}
    line = external.get("line", market.get("total_line"))
    over = external.get("over", market.get("over_fair"))
    return {"line": safe_probability(line), "over": safe_probability(over)}


def probability_move(first: dict[str, float | None], latest: dict[str, float | None], outcome: str) -> float | None:
    return numeric_delta(first.get(outcome), latest.get(outcome))


def numeric_delta(first: Any, latest: Any) -> float | None:
    if first is None or latest is None:
        return None
    return float(latest) - float(first)


def strongest_h2h_move(first: dict[str, float | None], latest: dict[str, float | None]) -> dict[str, Any]:
    moves = {
        outcome: probability_move(first, latest, outcome)
        for outcome in OUTCOMES
    }
    available = {outcome: move for outcome, move in moves.items() if move is not None}
    if not available:
        return {"outcome": "", "points": None}
    outcome, move = max(available.items(), key=lambda item: abs(item[1]))
    return {"outcome": outcome, "points": move}


def minutes_between(start: Any, end: Any) -> float | None:
    start_dt = parse_dt(start)
    end_dt = parse_dt(end)
    if not start_dt or not end_dt:
        return None
    return (end_dt - start_dt).total_seconds() / 60.0


def bookmaker_count(market: dict[str, Any]) -> int | None:
    external = market.get("external_totals_fair") or {}
    if external.get("sample_count") is not None:
        try:
            return int(external["sample_count"])
        except (TypeError, ValueError):
            return None
    return None


def latest_quota_remaining(row: dict[str, Any]) -> int | None:
    sources = row.get("source_status") or {}
    quota = (sources.get("the_odds_api") or {}).get("quota") or {}
    value = quota.get("requests_remaining")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def safe_probability(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
