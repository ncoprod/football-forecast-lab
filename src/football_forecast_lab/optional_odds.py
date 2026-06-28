from __future__ import annotations

import os
from datetime import timedelta
from typing import Any

from .espn import american_to_probability
from .http_client import fetch_json
from .settings import REPO_ROOT
from .utils import normalize_name, parse_dt, safe_float


THE_ODDS_API_SPORT_KEY = "soccer_fifa_world_cup"
THE_ODDS_API_URL = (
    "https://api.the-odds-api.com/v4/sports/"
    f"{THE_ODDS_API_SPORT_KEY}/odds"
    "?regions=us,uk,eu,au&markets=h2h,totals&oddsFormat=american"
)

API_FOOTBALL_ODDS_URL = "https://v3.football.api-sports.io/odds?league=1&season=2026"


def load_local_env() -> None:
    """Load simple KEY=value pairs from a local .env without overwriting the shell."""
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def collect_optional_odds(round_events: list[dict[str, Any]]) -> dict[str, Any]:
    """Fetch optional external odds when free-tier API keys are present."""
    load_local_env()
    sources = {
        "espn_draftkings": {
            "status": "built_in",
            "note": "Used directly from ESPN event JSON when available.",
        },
        "the_odds_api": fetch_the_odds_api(round_events),
        "api_football": fetch_api_football_status(),
        "football_data_org": {
            "status": "not_odds_source",
            "note": "Free fixtures/results API; no free odds endpoint used here.",
        },
        "openfootball": {
            "status": "fixture_archive_only",
            "note": "Useful for historical fixtures/results, not live odds.",
        },
    }
    return {"sources": sources, "matched_markets": sources["the_odds_api"].get("matched_markets", {})}


def fetch_the_odds_api(round_events: list[dict[str, Any]]) -> dict[str, Any]:
    api_key = os.environ.get("THE_ODDS_API_KEY")
    if not api_key:
        return {
            "status": "missing_key",
            "env_var": "THE_ODDS_API_KEY",
            "note": "Free tier exists, but a personal API key is required.",
        }

    url = f"{THE_ODDS_API_URL}&apiKey={api_key}"
    try:
        data = fetch_json(url, "the_odds_api_world_cup_odds.json")
    except Exception as exc:
        return {"status": "error", "env_var": "THE_ODDS_API_KEY", "error": str(exc)}

    matches = match_the_odds_api_events(round_events, data)
    return {
        "status": "ok",
        "sport_key": THE_ODDS_API_SPORT_KEY,
        "events_returned": len(data) if isinstance(data, list) else 0,
        "matches_found": len(matches),
        "matched_markets": matches,
    }


def fetch_api_football_status() -> dict[str, Any]:
    api_key = os.environ.get("API_FOOTBALL_KEY") or os.environ.get("API_SPORTS_KEY")
    if not api_key:
        return {
            "status": "missing_key",
            "env_var": "API_FOOTBALL_KEY",
            "note": "API-SPORTS/API-Football odds require a key. The endpoint is wired as documentation/status, not called without a key.",
        }
    return {
        "status": "configured_not_called",
        "env_var": "API_FOOTBALL_KEY",
        "note": "Key detected. Fixture-id matching is intentionally not enabled until verified against the live API response shape.",
        "endpoint": API_FOOTBALL_ODDS_URL,
    }


def match_the_odds_api_events(round_events: list[dict[str, Any]], odds_events: Any) -> dict[str, Any]:
    if not isinstance(odds_events, list):
        return {}
    matches: dict[str, Any] = {}
    for event in round_events:
        competitors = event.get("competitions", [{}])[0].get("competitors", [])
        names = [normalize_name((item.get("team") or {}).get("displayName", "")) for item in competitors]
        match_dt = parse_dt(event.get("date"))
        for odds_event in odds_events:
            if not is_same_match(names, match_dt, odds_event):
                continue
            matches[str(event.get("id"))] = summarize_the_odds_market(odds_event)
            break
    return matches


def is_same_match(names: list[str], match_dt: Any, odds_event: dict[str, Any]) -> bool:
    home = normalize_name(odds_event.get("home_team", ""))
    away = normalize_name(odds_event.get("away_team", ""))
    if home not in names or away not in names:
        return False
    if not match_dt:
        return True
    odds_dt = parse_dt(odds_event.get("commence_time"))
    if not odds_dt:
        return True
    return abs(match_dt - odds_dt) <= timedelta(hours=8)


def summarize_the_odds_market(odds_event: dict[str, Any]) -> dict[str, Any]:
    h2h_prices: dict[str, list[float]] = {}
    totals: list[dict[str, Any]] = []
    for bookmaker in odds_event.get("bookmakers", []) or []:
        for market in bookmaker.get("markets", []) or []:
            if market.get("key") == "h2h":
                for outcome in market.get("outcomes", []) or []:
                    price = american_to_probability(outcome.get("price"))
                    if price is not None:
                        h2h_prices.setdefault(outcome.get("name", ""), []).append(price)
            elif market.get("key") == "totals":
                totals.extend(market.get("outcomes", []) or [])

    fair_h2h = normalize_h2h_prices(h2h_prices)
    return {
        "source": "the_odds_api",
        "home_team": odds_event.get("home_team"),
        "away_team": odds_event.get("away_team"),
        "commence_time": odds_event.get("commence_time"),
        "bookmaker_count": len(odds_event.get("bookmakers", []) or []),
        "h2h_fair": fair_h2h,
        "total_points_sample": [safe_float(item.get("point")) for item in totals[:6] if item.get("point") is not None],
    }


def normalize_h2h_prices(prices: dict[str, list[float]]) -> dict[str, float]:
    averaged = {
        name: sum(values) / len(values)
        for name, values in prices.items()
        if values
    }
    total = sum(averaged.values())
    if total <= 0:
        return {}
    return {name: value / total for name, value in averaged.items()}
