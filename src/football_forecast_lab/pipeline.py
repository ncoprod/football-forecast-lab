from __future__ import annotations

import time
from datetime import datetime, timezone

from .elo import load_elo_for_teams
from .espn import build_group_stats, collect_round_teams
from .http_client import fetch_json
from .model import predict_match
from .optional_odds import collect_optional_odds
from .reporting import write_outputs
from .settings import (
    CACHE_DIR,
    ESPN_BASE,
    GROUP_SCOREBOARD_URL,
    KNOCKOUT_SCOREBOARD_URL,
    NEWS_URL,
    OUTPUT_DIR,
    R32_SCOREBOARD_URL,
    load_config,
)
from .tournament import simulate_tournament
from .trained_layer import enrich_predictions_with_ml


def load_round_of_32_events(scoreboard: dict) -> list[dict]:
    """Return only real Round-of-32 fixtures, excluding future placeholders."""
    return sorted(
        [
            event
            for event in scoreboard.get("events", [])
            if (event.get("season") or {}).get("slug") == "round-of-32"
        ],
        key=lambda event: event.get("date", ""),
    )


def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    config = load_config()
    generated_at = datetime.now(timezone.utc)

    group_scoreboard = fetch_json(GROUP_SCOREBOARD_URL, "espn_group_scoreboard.json")
    round_scoreboard = fetch_json(R32_SCOREBOARD_URL, "espn_r32_scoreboard.json")
    knockout_scoreboard = fetch_json(KNOCKOUT_SCOREBOARD_URL, "espn_knockout_scoreboard.json")
    league_news = fetch_json(NEWS_URL, "espn_worldcup_news.json")

    group_events = group_scoreboard.get("events", [])
    round_events = load_round_of_32_events(round_scoreboard)

    summaries: dict[str, dict] = {}
    for event in round_events:
        event_id = str(event["id"])
        summaries[event_id] = fetch_json(
            f"{ESPN_BASE}/summary?event={event_id}",
            f"espn_summary_{event_id}.json",
        )
        time.sleep(0.05)

    group_stats = build_group_stats(group_events)
    team_names = collect_round_teams(round_events)
    elo_map = load_elo_for_teams(team_names)
    optional_odds = collect_optional_odds(round_events)

    predictions = []
    for event in round_events:
        event_id = str(event["id"])
        predictions.append(
            predict_match(
                event,
                summaries.get(event_id, {}),
                group_stats,
                elo_map,
                league_news,
                config,
            )
        )

    trained_ml_status = enrich_predictions_with_ml(predictions)
    tournament = simulate_tournament(predictions, knockout_scoreboard)
    write_outputs(predictions, group_stats, elo_map, tournament, optional_odds, trained_ml_status, generated_at, config)
