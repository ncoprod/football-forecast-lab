from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from .espn import american_to_probability
from .http_client import fetch_json_with_meta
from .settings import REPO_ROOT, TEAM_ALIASES
from .utils import normalize_name, parse_dt, safe_float, safe_int


THE_ODDS_API_SPORT_KEY = "soccer_fifa_world_cup"
THE_ODDS_API_BASE_URL = f"https://api.the-odds-api.com/v4/sports/{THE_ODDS_API_SPORT_KEY}/odds"
DEFAULT_THE_ODDS_REGIONS = "eu,uk"
DEFAULT_THE_ODDS_MARKETS = "h2h,totals"

API_FOOTBALL_ODDS_URL = "https://v3.football.api-sports.io/odds?league=1&season=2026"
API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
API_FOOTBALL_LEAGUE_ID = "1"
API_FOOTBALL_SEASON = "2026"


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


def collect_optional_odds(round_events: list[dict[str, Any]], generated_at: datetime | None = None) -> dict[str, Any]:
    """Fetch optional external odds when free-tier API keys are present."""
    load_local_env()
    sources = {
        "espn_draftkings": {
            "status": "built_in",
            "note": "Used directly from ESPN event JSON when available.",
        },
        "the_odds_api": fetch_the_odds_api(round_events),
        "api_football": fetch_api_football(round_events, generated_at),
        "football_data_org": {
            "status": "not_odds_source",
            "note": "Free fixtures/results API; no free odds endpoint used here.",
        },
        "openfootball": {
            "status": "fixture_archive_only",
            "note": "Useful for historical fixtures/results, not live odds.",
        },
    }
    return {
        "sources": sources,
        "matched_markets": sources["the_odds_api"].get("matched_markets", {}),
        "api_football_enrichment": sources["api_football"].get("matched_fixtures", {}),
    }


def fetch_the_odds_api(round_events: list[dict[str, Any]]) -> dict[str, Any]:
    api_key = os.environ.get("THE_ODDS_API_KEY")
    if not api_key:
        return {
            "status": "missing_key",
            "env_var": "THE_ODDS_API_KEY",
            "note": "Free tier exists, but a personal API key is required.",
        }

    regions = os.environ.get("THE_ODDS_API_REGIONS", DEFAULT_THE_ODDS_REGIONS)
    markets = os.environ.get("THE_ODDS_API_MARKETS", DEFAULT_THE_ODDS_MARKETS)
    url = build_the_odds_api_url(api_key, regions, markets)
    try:
        data, headers, from_cache = fetch_json_with_meta(url, "the_odds_api_world_cup_odds.json")
    except Exception as exc:
        return {"status": "error", "env_var": "THE_ODDS_API_KEY", "error": str(exc)}

    matches = match_the_odds_api_events(round_events, data)
    return {
        "status": "ok",
        "sport_key": THE_ODDS_API_SPORT_KEY,
        "request_parameters": {"regions": regions, "markets": markets, "odds_format": "american"},
        "quota": extract_the_odds_quota(headers),
        "from_cache": from_cache,
        "events_returned": len(data) if isinstance(data, list) else 0,
        "matches_found": len(matches),
        "matched_markets": matches,
    }


def build_the_odds_api_url(api_key: str, regions: str, markets: str) -> str:
    query = urlencode(
        {
            "regions": regions,
            "markets": markets,
            "oddsFormat": "american",
            "apiKey": api_key,
        }
    )
    return f"{THE_ODDS_API_BASE_URL}?{query}"


def extract_the_odds_quota(headers: dict[str, str]) -> dict[str, int]:
    return {
        "requests_remaining": safe_int(headers.get("x-requests-remaining"), -1),
        "requests_used": safe_int(headers.get("x-requests-used"), -1),
        "requests_last": safe_int(headers.get("x-requests-last"), -1),
    }


def fetch_api_football(round_events: list[dict[str, Any]], generated_at: datetime | None) -> dict[str, Any]:
    api_key = os.environ.get("API_FOOTBALL_KEY") or os.environ.get("API_SPORTS_KEY")
    if not api_key:
        return {
            "status": "missing_key",
            "env_var": "API_FOOTBALL_KEY",
            "note": "API-SPORTS/API-Football odds require a key. The endpoint is wired as documentation/status, not called without a key.",
        }

    window = api_football_date_window(round_events)
    if window is None:
        return {"status": "no_round_events", "env_var": "API_FOOTBALL_KEY"}

    fixtures_url = build_api_football_url(
        "fixtures",
        {
            "league": API_FOOTBALL_LEAGUE_ID,
            "season": API_FOOTBALL_SEASON,
            "from": window[0],
            "to": window[1],
        },
    )
    try:
        data, _, from_cache = fetch_json_with_meta(
            fixtures_url,
            "api_football_fixtures_worldcup_2026_r32.json",
            headers={"x-apisports-key": api_key},
        )
    except Exception as exc:
        return {"status": "error", "env_var": "API_FOOTBALL_KEY", "error": str(exc)}

    response_rows = data.get("response", []) if isinstance(data, dict) else []
    matches = match_api_football_fixtures(round_events, response_rows)
    detail_status = enrich_api_football_details(matches, generated_at, api_key)
    status = "ok" if response_rows else "ok_no_fixtures"
    return {
        "status": status,
        "env_var": "API_FOOTBALL_KEY",
        "from_cache": from_cache,
        "window": {"from": window[0], "to": window[1]},
        "fixtures_returned": len(response_rows),
        "matches_found": len(matches),
        "matched_fixtures": matches,
        "detail_calls": detail_status,
        "note": "Fixture mapping is enabled. Detail calls are limited and only run when API_FOOTBALL_ENABLE_DETAIL_CALLS=1.",
        "endpoint": API_FOOTBALL_ODDS_URL,
    }


def build_api_football_url(path: str, params: dict[str, Any]) -> str:
    return f"{API_FOOTBALL_BASE_URL}/{path}?{urlencode(params)}"


def api_football_date_window(round_events: list[dict[str, Any]]) -> tuple[str, str] | None:
    dates = [parse_dt(event.get("date")) for event in round_events]
    dates = [date for date in dates if date]
    if not dates:
        return None
    start = min(dates).date().isoformat()
    end = max(dates).date().isoformat()
    return start, end


def match_api_football_fixtures(round_events: list[dict[str, Any]], fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    matches: dict[str, Any] = {}
    for event in round_events:
        competitors = event.get("competitions", [{}])[0].get("competitors", [])
        names = [canonical_team_name((item.get("team") or {}).get("displayName", "")) for item in competitors]
        match_dt = parse_dt(event.get("date"))
        for row in fixtures:
            teams = row.get("teams", {})
            home = canonical_team_name((teams.get("home") or {}).get("name", ""))
            away = canonical_team_name((teams.get("away") or {}).get("name", ""))
            fixture_dt = parse_dt((row.get("fixture") or {}).get("date"))
            if home not in names or away not in names:
                continue
            if match_dt and fixture_dt and abs(match_dt - fixture_dt) > timedelta(hours=8):
                continue
            fixture = row.get("fixture") or {}
            matches[str(event.get("id"))] = {
                "fixture_id": fixture.get("id"),
                "date": fixture.get("date"),
                "status": (fixture.get("status") or {}).get("short", ""),
                "home_team": (teams.get("home") or {}).get("name"),
                "away_team": (teams.get("away") or {}).get("name"),
                "injuries": [],
                "lineups": [],
                "player_stats": [],
            }
            break
    return matches


def enrich_api_football_details(matches: dict[str, Any], generated_at: datetime | None, api_key: str) -> dict[str, Any]:
    if os.environ.get("API_FOOTBALL_ENABLE_DETAIL_CALLS") != "1":
        return {"status": "disabled", "calls_made": 0, "env_var": "API_FOOTBALL_ENABLE_DETAIL_CALLS"}
    call_limit = safe_int(os.environ.get("API_FOOTBALL_DETAIL_CALL_LIMIT"), 12)
    calls_made = 0
    for event_id, match in matches.items():
        if calls_made >= call_limit:
            break
        fixture_id = match.get("fixture_id")
        match_dt = parse_dt(match.get("date"))
        if not fixture_id or (generated_at and match_dt and generated_at >= match_dt):
            continue
        for endpoint, target_key in (
            ("injuries", "injuries"),
            ("fixtures/lineups", "lineups"),
            ("fixtures/players", "player_stats"),
        ):
            if calls_made >= call_limit:
                break
            url = build_api_football_url(endpoint, {"fixture": fixture_id})
            try:
                data, _, from_cache = fetch_json_with_meta(
                    url,
                    f"api_football_{target_key}_{fixture_id}.json",
                    headers={"x-apisports-key": api_key},
                )
            except Exception as exc:
                match.setdefault("detail_errors", []).append({"endpoint": endpoint, "error": str(exc)})
                continue
            rows = data.get("response", []) if isinstance(data, dict) else []
            match[target_key] = summarize_api_football_detail_rows(target_key, rows, from_cache)
            calls_made += 1
    return {"status": "ok", "calls_made": calls_made, "call_limit": call_limit}


def summarize_api_football_detail_rows(target_key: str, rows: list[dict[str, Any]], from_cache: bool) -> dict[str, Any]:
    return {
        "from_cache": from_cache,
        "count": len(rows),
        "sample": rows[:3],
    }


def match_the_odds_api_events(round_events: list[dict[str, Any]], odds_events: Any) -> dict[str, Any]:
    if not isinstance(odds_events, list):
        return {}
    matches: dict[str, Any] = {}
    for event in round_events:
        competitors = event.get("competitions", [{}])[0].get("competitors", [])
        names = [canonical_team_name((item.get("team") or {}).get("displayName", "")) for item in competitors]
        match_dt = parse_dt(event.get("date"))
        for odds_event in odds_events:
            if not is_same_match(names, match_dt, odds_event):
                continue
            matches[str(event.get("id"))] = summarize_the_odds_market(odds_event)
            break
    return matches


def is_same_match(names: list[str], match_dt: Any, odds_event: dict[str, Any]) -> bool:
    home = canonical_team_name(odds_event.get("home_team", ""))
    away = canonical_team_name(odds_event.get("away_team", ""))
    if home not in names or away not in names:
        return False
    if not match_dt:
        return True
    odds_dt = parse_dt(odds_event.get("commence_time"))
    if not odds_dt:
        return True
    return abs(match_dt - odds_dt) <= timedelta(hours=8)


def canonical_team_name(value: str) -> str:
    normalized = normalize_name(value)
    alias_map = {normalize_name(key): normalize_name(alias) for key, alias in TEAM_ALIASES.items()}
    return alias_map.get(normalized, normalized)


def summarize_the_odds_market(odds_event: dict[str, Any]) -> dict[str, Any]:
    h2h_prices: dict[str, list[float]] = {}
    totals_by_line: dict[float, dict[str, list[float]]] = {}
    for bookmaker in odds_event.get("bookmakers", []) or []:
        for market in bookmaker.get("markets", []) or []:
            if market.get("key") == "h2h":
                for outcome in market.get("outcomes", []) or []:
                    price = american_to_probability(outcome.get("price"))
                    if price is not None:
                        h2h_prices.setdefault(outcome.get("name", ""), []).append(price)
            elif market.get("key") == "totals":
                for outcome in market.get("outcomes", []) or []:
                    line = safe_float(outcome.get("point"), -1.0)
                    price = american_to_probability(outcome.get("price"))
                    side = normalize_name(outcome.get("name", ""))
                    if line <= 0 or price is None or side not in {"over", "under"}:
                        continue
                    totals_by_line.setdefault(line, {"over": [], "under": []})[side].append(price)

    fair_h2h = normalize_h2h_prices(h2h_prices)
    fair_totals = choose_best_total_market(totals_by_line)
    return {
        "source": "the_odds_api",
        "home_team": odds_event.get("home_team"),
        "away_team": odds_event.get("away_team"),
        "commence_time": odds_event.get("commence_time"),
        "bookmaker_count": len(odds_event.get("bookmakers", []) or []),
        "h2h_fair": fair_h2h,
        "totals_fair": fair_totals,
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


def choose_best_total_market(totals_by_line: dict[float, dict[str, list[float]]]) -> dict[str, float]:
    candidates = []
    for line, sides in totals_by_line.items():
        over_prices = sides.get("over", [])
        under_prices = sides.get("under", [])
        if not over_prices or not under_prices:
            continue
        over_avg = sum(over_prices) / len(over_prices)
        under_avg = sum(under_prices) / len(under_prices)
        total = over_avg + under_avg
        if total <= 0:
            continue
        sample_count = len(over_prices) + len(under_prices)
        candidates.append(
            {
                "line": line,
                "over": over_avg / total,
                "under": under_avg / total,
                "sample_count": sample_count,
            }
        )
    if not candidates:
        return {}
    return max(candidates, key=lambda item: (item["sample_count"], -abs(item["line"] - 2.5)))
