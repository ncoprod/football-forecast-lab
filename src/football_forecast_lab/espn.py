from __future__ import annotations

import re
import math
from collections import defaultdict
from datetime import datetime
from typing import Any

from .settings import INJURY_TERMS
from .utils import clean_text, normalize_name, parse_dt, safe_float, safe_int

def event_competitors(event: dict[str, Any]) -> dict[str, dict[str, Any]]:
    competition = event.get("competitions", [{}])[0]
    competitors: dict[str, dict[str, Any]] = {}
    for competitor in competition.get("competitors", []):
        team = competitor.get("team", {})
        home_away = competitor.get("homeAway", "")
        competitors[home_away] = {
            "team_id": str(team.get("id", competitor.get("id", ""))),
            "name": team.get("displayName") or team.get("name") or "",
            "short_name": team.get("shortDisplayName") or team.get("displayName") or "",
            "abbr": team.get("abbreviation", ""),
            "score": safe_int(competitor.get("score"), 0),
            "winner": bool(competitor.get("winner", False)),
            "form": competitor.get("form", ""),
        }
    return competitors

def build_group_stats(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = defaultdict(new_team_stats)
    for event in events:
        competition = event.get("competitions", [{}])[0]
        status = competition.get("status", event.get("status", {})).get("type", {})
        if not status.get("completed"):
            continue
        competitors = event_competitors(event)
        if "home" not in competitors or "away" not in competitors:
            continue
        home = competitors["home"]
        away = competitors["away"]
        event_dt = parse_dt(event.get("date"))
        update_team_stats(stats[home["name"]], home, away, event_dt)
        update_team_stats(stats[away["name"]], away, home, event_dt)
    for team_stats in stats.values():
        matches = max(team_stats["matches"], 1)
        team_stats["ppg"] = team_stats["points"] / matches
        team_stats["gf_pg"] = team_stats["gf"] / matches
        team_stats["ga_pg"] = team_stats["ga"] / matches
        team_stats["gd_pg"] = team_stats["gd"] / matches
        team_stats["form_string"] = "".join(team_stats["form"][-5:])
    return dict(stats)

def new_team_stats() -> dict[str, Any]:
    return {
        "matches": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "points": 0,
        "gf": 0,
        "ga": 0,
        "gd": 0,
        "form": [],
        "last_match_utc": None,
    }

def update_team_stats(
    target: dict[str, Any],
    team: dict[str, Any],
    opponent: dict[str, Any],
    event_dt: datetime | None,
) -> None:
    gf = team["score"]
    ga = opponent["score"]
    target["matches"] += 1
    target["gf"] += gf
    target["ga"] += ga
    target["gd"] = target["gf"] - target["ga"]
    if gf > ga:
        target["wins"] += 1
        target["points"] += 3
        target["form"].append("W")
    elif gf == ga:
        target["draws"] += 1
        target["points"] += 1
        target["form"].append("D")
    else:
        target["losses"] += 1
        target["form"].append("L")
    if event_dt and (target["last_match_utc"] is None or event_dt > target["last_match_utc"]):
        target["last_match_utc"] = event_dt

def collect_round_teams(events: list[dict[str, Any]]) -> list[str]:
    names = []
    for event in events:
        competitors = event_competitors(event)
        for side in ("home", "away"):
            if side in competitors:
                names.append(competitors[side]["name"])
    return sorted(set(names))

def american_to_probability(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip().replace("+", "")
    odds = safe_float(value, float("nan"))
    if math.isnan(odds) or odds == 0:
        return None
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return -odds / (-odds + 100.0)

def nested_odds_value(node: dict[str, Any] | None) -> str | None:
    if not isinstance(node, dict):
        return None
    for branch in ("close", "open"):
        value = node.get(branch, {}).get("odds") if isinstance(node.get(branch), dict) else None
        if value:
            return str(value)
    if node.get("odds"):
        return str(node["odds"])
    return None

def nested_line_value(node: dict[str, Any] | None) -> float | None:
    if not isinstance(node, dict):
        return None
    for branch in ("close", "open"):
        line = node.get(branch, {}).get("line") if isinstance(node.get(branch), dict) else None
        if line:
            match = re.search(r"([0-9]+(?:\.[0-9]+)?)", str(line))
            if match:
                return float(match.group(1))
    return None

def extract_odds(event: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    competition = event.get("competitions", [{}])[0]
    odds_entries = competition.get("odds") or summary.get("odds") or []
    book = odds_entries[0] if odds_entries else {}
    if not isinstance(book, dict):
        book = {}
    moneyline = book.get("moneyline", {}) if isinstance(book, dict) else {}
    total = book.get("total", {}) if isinstance(book, dict) else {}

    raw_home = nested_odds_value(moneyline.get("home"))
    raw_draw = nested_odds_value(moneyline.get("draw")) or nested_odds_value(book.get("drawOdds"))
    raw_away = nested_odds_value(moneyline.get("away"))

    implied = {
        "home": american_to_probability(raw_home),
        "draw": american_to_probability(raw_draw),
        "away": american_to_probability(raw_away),
    }
    if all(value is not None for value in implied.values()):
        overround = sum(implied.values())
        fair = {key: value / overround for key, value in implied.items() if value is not None}
    else:
        fair = {}

    raw_over = nested_odds_value(total.get("over"))
    raw_under = nested_odds_value(total.get("under"))
    over_prob = american_to_probability(raw_over)
    under_prob = american_to_probability(raw_under)
    if over_prob is not None and under_prob is not None:
        total_prob_sum = over_prob + under_prob
        fair_over = over_prob / total_prob_sum
    else:
        fair_over = None

    return {
        "provider": (book.get("provider", {}) or {}).get("displayName") or (book.get("provider", {}) or {}).get("name"),
        "details": book.get("details", ""),
        "moneyline_raw": {"home": raw_home, "draw": raw_draw, "away": raw_away},
        "moneyline_fair": fair,
        "over_under_raw": {"over": raw_over, "under": raw_under},
        "total_line": nested_line_value(total.get("over")) or nested_line_value(total.get("under")),
        "over_fair": fair_over,
    }

def extract_leaders(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for team_bucket in summary.get("leaders", []) or []:
        team = team_bucket.get("team", {})
        team_name = team.get("displayName")
        if not team_name:
            continue
        team_result = {"top_goals": [], "top_assists": [], "top_saves": []}
        for category in team_bucket.get("leaders", []) or []:
            name = category.get("name", "")
            display_name = category.get("displayName", "")
            key = None
            if "goal" in name.lower() or display_name.lower() == "goals":
                key = "top_goals"
            elif "assist" in name.lower() or display_name.lower() == "assists":
                key = "top_assists"
            elif "save" in name.lower() or display_name.lower() == "saves":
                key = "top_saves"
            if not key:
                continue
            for leader in (category.get("leaders") or [])[:3]:
                athlete = leader.get("athlete", {})
                item = {
                    "name": clean_text(athlete.get("displayName") or athlete.get("fullName") or ""),
                    "position": (athlete.get("position") or {}).get("abbreviation", ""),
                    "value": stat_value(leader),
                    "display": clean_text(leader.get("displayValue") or leader.get("shortDisplayValue") or ""),
                }
                if item["name"]:
                    team_result[key].append(item)
        result[team_name] = team_result
    return result

def stat_value(leader: dict[str, Any]) -> float:
    for stat in leader.get("statistics", []) or []:
        if stat.get("name") in {"totalGoals", "goalAssists", "assists", "saves"}:
            return safe_float(stat.get("value"))
    main = leader.get("mainStat", {})
    return safe_float(main.get("value"))

def extract_news_notes(
    summary: dict[str, Any],
    league_news: dict[str, Any],
    home: dict[str, Any],
    away: dict[str, Any],
) -> list[dict[str, Any]]:
    articles = []
    for source in (summary.get("news", {}), league_news):
        articles.extend(source.get("articles", []) if isinstance(source, dict) else [])

    seen = set()
    notes = []
    home_terms = {normalize_name(home["name"]), normalize_name(home["abbr"])}
    away_terms = {normalize_name(away["name"]), normalize_name(away["abbr"])}
    for article in articles:
        article_id = str(article.get("id", ""))
        if article_id in seen:
            continue
        seen.add(article_id)
        headline = clean_text(article.get("headline", ""))
        description = clean_text(article.get("description", ""))
        blob = normalize_name(f"{headline} {description}")
        categories = article.get("categories", []) or []
        team_ids = {str(cat.get("teamId")) for cat in categories if cat.get("teamId") is not None}
        mentions_team = (
            home["team_id"] in team_ids
            or away["team_id"] in team_ids
            or any(term and term in blob for term in home_terms | away_terms)
        )
        is_broad_wc = "world cup" in blob or "championship odds" in blob or "knockout" in blob
        if not mentions_team and not is_broad_wc:
            continue
        raw_text = f"{headline} {description}".lower()
        notes.append(
            {
                "headline": headline,
                "published": article.get("published") or article.get("lastModified") or "",
                "url": ((article.get("links") or {}).get("web") or {}).get("href", ""),
                "risk_terms": ", ".join(term for term in INJURY_TERMS if term in raw_text),
            }
        )
        if len(notes) >= 4:
            break
    return notes

