from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from .model import final_score_distribution_with_extra_time, leader_goal_signal, outcome_probs
from .settings import DEFAULT_CONFIG
from .utils import clamp, elo_diff_from_probability, logistic_base10, safe_float

def penalty_share(profile_a: dict[str, Any], profile_b: dict[str, Any]) -> float:
    diff = safe_float(profile_a.get("rating")) - safe_float(profile_b.get("rating"))
    return logistic_base10(diff, 650.0)

def build_team_profiles(predictions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    market_residuals: defaultdict[str, float] = defaultdict(float)

    for pred in predictions:
        home_name = pred["home"]["name"]
        away_name = pred["away"]["name"]
        fair = pred["odds"].get("moneyline_fair", {})
        if fair.get("home") is None or fair.get("away") is None:
            continue
        conditional_home = fair["home"] / max(fair["home"] + fair["away"], 0.001)
        market_diff = elo_diff_from_probability(conditional_home)
        elo_diff = safe_float(pred["elo_home"].get("rating")) - safe_float(pred["elo_away"].get("rating"))
        residual = clamp(market_diff - elo_diff, -220.0, 220.0)
        market_residuals[home_name] += residual / 2.0
        market_residuals[away_name] -= residual / 2.0

    for pred in predictions:
        for side in ("home", "away"):
            team_name = pred[side]["name"]
            if team_name in profiles:
                continue
            elo = pred[f"elo_{side}"]
            group = pred[f"group_{side}"]
            leaders = pred[f"leaders_{side}"]
            base_rating = safe_float(elo.get("rating"), 1700.0)
            group_nudge = clamp(
                34.0 * safe_float(group.get("gd_pg"))
                + 26.0 * (safe_float(group.get("ppg")) - 1.5)
                + 10.0 * (safe_float(group.get("gf_pg")) - 1.25)
                - 8.0 * (safe_float(group.get("ga_pg")) - 1.15),
                -115.0,
                115.0,
            )
            leader_nudge = clamp(5.0 * leader_goal_signal(leaders), 0.0, 45.0)
            market_nudge = market_residuals[team_name]
            rating = base_rating + group_nudge + leader_nudge + market_nudge
            attack = clamp(
                1.0
                + 0.11 * (safe_float(group.get("gf_pg")) - 1.25)
                + 0.018 * leader_goal_signal(leaders),
                0.72,
                1.38,
            )
            defense = clamp(
                1.0
                + 0.09 * (1.15 - safe_float(group.get("ga_pg")))
                + 0.035 * safe_float(group.get("gd_pg")),
                0.74,
                1.34,
            )
            profiles[team_name] = {
                "team": team_name,
                "base_elo": base_rating,
                "rating": rating,
                "market_nudge": market_nudge,
                "group_nudge": group_nudge,
                "leader_nudge": leader_nudge,
                "attack": attack,
                "defense": defense,
                "group": group,
                "leaders": leaders,
            }
    return profiles

def future_pair_model(
    team_a: str,
    team_b: str,
    profiles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    profile_a = profiles[team_a]
    profile_b = profiles[team_b]
    diff = safe_float(profile_a.get("rating")) - safe_float(profile_b.get("rating"))
    raw_a = math.exp(diff / 690.0) * safe_float(profile_a.get("attack"), 1.0) / max(safe_float(profile_b.get("defense"), 1.0), 0.68)
    raw_b = math.exp(-diff / 690.0) * safe_float(profile_b.get("attack"), 1.0) / max(safe_float(profile_a.get("defense"), 1.0), 0.68)
    base_total = clamp(
        2.30
        + 0.10 * ((safe_float(profile_a.get("attack"), 1.0) + safe_float(profile_b.get("attack"), 1.0)) - 2.0)
        - 0.06 * ((safe_float(profile_a.get("defense"), 1.0) + safe_float(profile_b.get("defense"), 1.0)) - 2.0),
        1.75,
        3.30,
    )
    scale = base_total / max(raw_a + raw_b, 0.001)
    lam_a = raw_a * scale
    lam_b = raw_b * scale
    scores = final_score_distribution_with_extra_time(lam_a, lam_b, DEFAULT_CONFIG["extra_time_goal_factor"])
    outcomes = outcome_probs(scores)
    p_pen_a = penalty_share(profile_a, profile_b)
    p_adv_a = outcomes["home"] + outcomes["draw"] * p_pen_a
    p_adv_b = 1.0 - p_adv_a
    return {
        "lambda_a": lam_a,
        "lambda_b": lam_b,
        "outcomes": outcomes,
        "penalty_share_a": p_pen_a,
        "advance_a": p_adv_a,
        "advance_b": p_adv_b,
    }

def first_round_winner_distribution(prediction: dict[str, Any], profiles: dict[str, dict[str, Any]]) -> dict[str, float]:
    home_name = prediction["home"]["name"]
    away_name = prediction["away"]["name"]
    p_pen_home = penalty_share(profiles[home_name], profiles[away_name])
    outcomes = prediction["final_outcomes"]
    p_home = outcomes["home"] + outcomes["draw"] * p_pen_home
    p_away = 1.0 - p_home
    return {home_name: p_home, away_name: p_away}

def combine_slots(
    slot_a: dict[str, float],
    slot_b: dict[str, float],
    profiles: dict[str, dict[str, Any]],
) -> dict[str, float]:
    output: defaultdict[str, float] = defaultdict(float)
    for team_a, prob_a in slot_a.items():
        for team_b, prob_b in slot_b.items():
            if team_a == team_b:
                output[team_a] += prob_a * prob_b
                continue
            model = future_pair_model(team_a, team_b, profiles)
            base = prob_a * prob_b
            output[team_a] += base * model["advance_a"]
            output[team_b] += base * model["advance_b"]
    total = sum(output.values())
    return {team: prob / total for team, prob in output.items()} if total else {}

def top_distribution(distribution: dict[str, float], limit: int = 10) -> list[dict[str, Any]]:
    return [
        {"team": team, "probability": prob}
        for team, prob in sorted(distribution.items(), key=lambda item: item[1], reverse=True)[:limit]
    ]

def extract_future_bracket_events(knockout_scoreboard: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for event in sorted(knockout_scoreboard.get("events", []), key=lambda item: item.get("date", "")):
        rows.append(
            {
                "id": str(event.get("id", "")),
                "name": event.get("name", ""),
                "date": event.get("date", ""),
                "slug": (event.get("season") or {}).get("slug", ""),
            }
        )
    return rows

def simulate_tournament(
    predictions: list[dict[str, Any]],
    knockout_scoreboard: dict[str, Any],
) -> dict[str, Any]:
    profiles = build_team_profiles(predictions)
    r32_slots = [first_round_winner_distribution(pred, profiles) for pred in predictions]

    # ESPN labels the future bracket as "Round of 32 N Winner"; indexes below are zero-based.
    r16_pairs = [(0, 2), (1, 4), (3, 5), (6, 7), (10, 11), (8, 9), (13, 15), (12, 14)]
    qf_pairs = [(0, 1), (4, 5), (2, 3), (6, 7)]
    sf_pairs = [(0, 1), (2, 3)]

    r16_slots = [combine_slots(r32_slots[a], r32_slots[b], profiles) for a, b in r16_pairs]
    qf_slots = [combine_slots(r16_slots[a], r16_slots[b], profiles) for a, b in qf_pairs]
    sf_slots = [combine_slots(qf_slots[a], qf_slots[b], profiles) for a, b in sf_pairs]
    champion_slot = combine_slots(sf_slots[0], sf_slots[1], profiles)

    advancement: dict[str, dict[str, float]] = {}
    for name in profiles:
        advancement[name] = {
            "reach_r16": sum(slot.get(name, 0.0) for slot in r32_slots),
            "reach_qf": sum(slot.get(name, 0.0) for slot in r16_slots),
            "reach_sf": sum(slot.get(name, 0.0) for slot in qf_slots),
            "reach_final": sum(slot.get(name, 0.0) for slot in sf_slots),
            "champion": champion_slot.get(name, 0.0),
            "rating": profiles[name]["rating"],
            "base_elo": profiles[name]["base_elo"],
            "market_nudge": profiles[name]["market_nudge"],
            "group_nudge": profiles[name]["group_nudge"],
        }

    likely_path = {
        "r16": [top_distribution(slot, 2) for slot in r16_slots],
        "qf": [top_distribution(slot, 2) for slot in qf_slots],
        "sf": [top_distribution(slot, 2) for slot in sf_slots],
        "final": top_distribution(champion_slot, 8),
    }

    return {
        "profiles": profiles,
        "future_bracket_events": extract_future_bracket_events(knockout_scoreboard),
        "advancement": advancement,
        "likely_path": likely_path,
        "champion_top": top_distribution(champion_slot, 16),
        "round_slots": {
            "r32_winners": [top_distribution(slot, 4) for slot in r32_slots],
            "r16_winners": [top_distribution(slot, 6) for slot in r16_slots],
            "qf_winners": [top_distribution(slot, 8) for slot in qf_slots],
            "sf_winners": [top_distribution(slot, 10) for slot in sf_slots],
        },
    }

