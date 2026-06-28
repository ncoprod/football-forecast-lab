from __future__ import annotations

import csv
import math
import urllib.request
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .settings import CACHE_DIR, OUTPUT_DIR, USER_AGENT


RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"


@dataclass
class MatchExample:
    date: date
    home: str
    away: str
    tournament: str
    features: dict[str, float]
    target: int
    score: str


def fetch_historical_results() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / "international_results.csv"
    request = urllib.request.Request(RESULTS_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45) as response:
        path.write_bytes(response.read())
    return path


def load_historical_results(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    rows.sort(key=lambda row: row["date"])
    return rows


def build_examples(rows: list[dict[str, str]], start_year: int = 1990) -> list[MatchExample]:
    elo = defaultdict(lambda: 1500.0)
    recent_points: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=5))
    recent_gd: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=5))
    recent_gf: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=5))
    recent_ga: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=5))
    last_match: dict[str, date] = {}

    examples: list[MatchExample] = []
    for row in rows:
        match_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
        home = row["home_team"]
        away = row["away_team"]
        if row["home_score"] == "NA" or row["away_score"] == "NA":
            continue
        home_score = int(row["home_score"])
        away_score = int(row["away_score"])
        target = result_class(home_score, away_score)
        tournament = row["tournament"]
        neutral = row["neutral"].upper() == "TRUE"

        if match_date.year >= start_year:
            features = {
                "elo_diff": elo[home] - elo[away],
                "home_elo": elo[home],
                "away_elo": elo[away],
                "home_advantage": 0.0 if neutral else 1.0,
                "form_points_diff": mean(recent_points[home]) - mean(recent_points[away]),
                "form_gd_diff": mean(recent_gd[home]) - mean(recent_gd[away]),
                "form_gf_diff": mean(recent_gf[home]) - mean(recent_gf[away]),
                "form_ga_diff": mean(recent_ga[away]) - mean(recent_ga[home]),
                "rest_diff": rest_feature(last_match.get(home), match_date) - rest_feature(last_match.get(away), match_date),
                "is_world_cup": 1.0 if tournament == "FIFA World Cup" else 0.0,
                "is_qualifier": 1.0 if "qualification" in tournament.lower() or "qualifier" in tournament.lower() else 0.0,
                "is_friendly": 1.0 if tournament == "Friendly" else 0.0,
                "is_continental": 1.0 if is_continental_tournament(tournament) else 0.0,
            }
            examples.append(
                MatchExample(
                    date=match_date,
                    home=home,
                    away=away,
                    tournament=tournament,
                    features=features,
                    target=target,
                    score=f"{home_score}-{away_score}",
                )
            )

        update_state(
            elo,
            recent_points,
            recent_gd,
            recent_gf,
            recent_ga,
            last_match,
            match_date,
            home,
            away,
            home_score,
            away_score,
            tournament,
            neutral,
        )
    return examples


def write_training_snapshot(examples: list[MatchExample]) -> Path:
    path = OUTPUT_DIR / "historical_training_dataset_snapshot.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not examples:
        return path
    feature_names = list(examples[0].features.keys())
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["date", "home", "away", "tournament", "target", "score", *feature_names],
        )
        writer.writeheader()
        for example in examples:
            writer.writerow(
                {
                    "date": example.date.isoformat(),
                    "home": example.home,
                    "away": example.away,
                    "tournament": example.tournament,
                    "target": example.target,
                    "score": example.score,
                    **example.features,
                }
            )
    return path


def result_class(home_score: int, away_score: int) -> int:
    if home_score > away_score:
        return 0
    if home_score == away_score:
        return 1
    return 2


def mean(values: deque[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def rest_feature(previous: date | None, current: date) -> float:
    if previous is None:
        return 0.0
    return min(365.0, max(0.0, float((current - previous).days))) / 30.0


def is_continental_tournament(tournament: str) -> bool:
    terms = (
        "UEFA Euro",
        "Copa América",
        "African Cup",
        "AFC Asian Cup",
        "CONCACAF Championship",
        "CONCACAF Gold Cup",
        "Oceania Nations Cup",
    )
    return any(term in tournament for term in terms)


def update_state(
    elo: dict[str, float],
    recent_points: dict[str, deque[float]],
    recent_gd: dict[str, deque[float]],
    recent_gf: dict[str, deque[float]],
    recent_ga: dict[str, deque[float]],
    last_match: dict[str, date],
    match_date: date,
    home: str,
    away: str,
    home_score: int,
    away_score: int,
    tournament: str,
    neutral: bool,
) -> None:
    home_points = 3.0 if home_score > away_score else 1.0 if home_score == away_score else 0.0
    away_points = 3.0 if away_score > home_score else 1.0 if home_score == away_score else 0.0
    recent_points[home].append(home_points)
    recent_points[away].append(away_points)
    recent_gd[home].append(home_score - away_score)
    recent_gd[away].append(away_score - home_score)
    recent_gf[home].append(float(home_score))
    recent_gf[away].append(float(away_score))
    recent_ga[home].append(float(away_score))
    recent_ga[away].append(float(home_score))

    update_elo(elo, home, away, home_score, away_score, tournament, neutral)
    last_match[home] = match_date
    last_match[away] = match_date


def update_elo(
    elo: dict[str, float],
    home: str,
    away: str,
    home_score: int,
    away_score: int,
    tournament: str,
    neutral: bool,
) -> None:
    home_advantage = 0.0 if neutral else 70.0
    expected_home = 1.0 / (1.0 + 10 ** (-((elo[home] + home_advantage) - elo[away]) / 400.0))
    actual_home = 1.0 if home_score > away_score else 0.5 if home_score == away_score else 0.0
    margin = abs(home_score - away_score)
    margin_multiplier = 1.0 if margin <= 1 else math.log(margin + 1.0)
    k = tournament_k(tournament)
    change = k * margin_multiplier * (actual_home - expected_home)
    elo[home] += change
    elo[away] -= change


def tournament_k(tournament: str) -> float:
    if tournament == "FIFA World Cup":
        return 50.0
    if "qualification" in tournament.lower() or "qualifier" in tournament.lower():
        return 35.0
    if is_continental_tournament(tournament):
        return 40.0
    if tournament == "Friendly":
        return 18.0
    return 26.0
