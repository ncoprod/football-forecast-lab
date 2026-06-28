from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from typing import Any

from .espn import event_competitors, extract_leaders, extract_news_notes, extract_odds
from .settings import PARIS_TZ
from .utils import parse_dt, safe_float

def poisson_pmf(lam: float, max_goals: int) -> list[float]:
    lam = max(lam, 0.01)
    values = [math.exp(-lam)]
    for k in range(1, max_goals + 1):
        values.append(values[-1] * lam / k)
    total = sum(values)
    return [value / total for value in values]

def score_distribution(lam_home: float, lam_away: float, max_goals: int = 10) -> dict[tuple[int, int], float]:
    home_pmf = poisson_pmf(lam_home, max_goals)
    away_pmf = poisson_pmf(lam_away, max_goals)
    return {(h, a): home_pmf[h] * away_pmf[a] for h in range(max_goals + 1) for a in range(max_goals + 1)}

def outcome_probs(scores: dict[tuple[int, int], float]) -> dict[str, float]:
    home = sum(prob for (h, a), prob in scores.items() if h > a)
    draw = sum(prob for (h, a), prob in scores.items() if h == a)
    away = sum(prob for (h, a), prob in scores.items() if h < a)
    total = home + draw + away
    return {"home": home / total, "draw": draw / total, "away": away / total}

def over_probability(scores: dict[tuple[int, int], float], line: float | None) -> float | None:
    if line is None:
        return None
    threshold = math.floor(line) + 1
    return sum(prob for (h, a), prob in scores.items() if h + a >= threshold)

def fit_market_lambdas(odds: dict[str, Any]) -> tuple[float, float, dict[str, Any]]:
    fair = odds.get("moneyline_fair", {})
    target_home = fair.get("home")
    target_draw = fair.get("draw")
    target_away = fair.get("away")
    target_over = odds.get("over_fair")
    total_line = odds.get("total_line") or 2.5

    if target_home is None or target_draw is None or target_away is None:
        return 1.25, 1.15, {"source": "fallback", "fit_error": None}

    total_guess = solve_total_goals(target_over, total_line) if target_over is not None else 2.45
    min_total = max(1.2, total_guess - 1.0)
    max_total = min(4.6, total_guess + 1.0)

    best: tuple[float, float, float, dict[str, float]] | None = None
    for total_i in range(int(min_total * 100), int(max_total * 100) + 1, 2):
        total = total_i / 100.0
        for share_i in range(12, 89):
            share = share_i / 100.0
            lam_home = total * share
            lam_away = total - lam_home
            scores = score_distribution(lam_home, lam_away, 9)
            probs = outcome_probs(scores)
            p_over = over_probability(scores, total_line)
            objective = (
                2.2 * (probs["home"] - target_home) ** 2
                + 2.8 * (probs["draw"] - target_draw) ** 2
                + 2.2 * (probs["away"] - target_away) ** 2
                + 0.8 * ((p_over or target_over or 0.5) - (target_over or p_over or 0.5)) ** 2
                + 0.03 * (total - total_guess) ** 2
            )
            if best is None or objective < best[0]:
                best = (objective, lam_home, lam_away, probs | {"over": p_over or 0.0})

    if best is None:
        return 1.25, 1.15, {"source": "fallback", "fit_error": None}

    objective, lam_home, lam_away, fitted_probs = best
    return lam_home, lam_away, {"source": "market_fit", "fit_error": objective, "fitted_probs": fitted_probs}

def solve_total_goals(over_prob: float | None, line: float | None) -> float:
    if over_prob is None or line is None:
        return 2.45
    threshold = math.floor(line) + 1
    lo, hi = 0.4, 5.5
    for _ in range(50):
        mid = (lo + hi) / 2
        p_over = 1.0 - sum(math.exp(-mid) * mid**k / math.factorial(k) for k in range(threshold))
        if p_over < over_prob:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def context_adjust_lambdas(
    lam_home: float,
    lam_away: float,
    home_name: str,
    away_name: str,
    match_dt: datetime | None,
    group_stats: dict[str, dict[str, Any]],
    elo_map: dict[str, dict[str, Any]],
    leaders: dict[str, dict[str, Any]],
) -> tuple[float, float, dict[str, Any]]:
    original_total = lam_home + lam_away
    notes = []

    home_elo = elo_map.get(home_name, {})
    away_elo = elo_map.get(away_name, {})
    if home_elo.get("available") and away_elo.get("available"):
        diff = safe_float(home_elo.get("rating")) - safe_float(away_elo.get("rating"))
        elo_share = 0.5 + 0.23 * math.tanh(diff / 520.0)
        elo_home_lam = original_total * elo_share
        elo_away_lam = original_total - elo_home_lam
        lam_home = 0.86 * lam_home + 0.14 * elo_home_lam
        lam_away = 0.86 * lam_away + 0.14 * elo_away_lam
        notes.append(f"Elo diff {diff:+.0f}")

    home_form = form_score(group_stats.get(home_name, {}))
    away_form = form_score(group_stats.get(away_name, {}))
    form_diff = max(-2.5, min(2.5, home_form - away_form))
    lam_home *= math.exp(0.035 * form_diff)
    lam_away *= math.exp(-0.035 * form_diff)
    notes.append(f"group form diff {form_diff:+.2f}")

    if match_dt:
        rest_home = rest_days(group_stats.get(home_name, {}), match_dt)
        rest_away = rest_days(group_stats.get(away_name, {}), match_dt)
        if rest_home is not None and rest_away is not None:
            rest_diff = max(-4.0, min(4.0, rest_home - rest_away))
            lam_home *= math.exp(0.010 * rest_diff)
            lam_away *= math.exp(-0.010 * rest_diff)
            notes.append(f"rest diff {rest_diff:+.1f}d")

    goal_leader_diff = leader_goal_signal(leaders.get(home_name, {})) - leader_goal_signal(leaders.get(away_name, {}))
    goal_leader_diff = max(-4.0, min(4.0, goal_leader_diff))
    lam_home *= math.exp(0.010 * goal_leader_diff)
    lam_away *= math.exp(-0.010 * goal_leader_diff)
    if abs(goal_leader_diff) > 0:
        notes.append(f"leader goals diff {goal_leader_diff:+.1f}")

    adjusted_total = lam_home + lam_away
    if adjusted_total > 0:
        # Keep contextual nudges modest; the market total is a stronger signal than our features.
        blend_total = 0.88 * original_total + 0.12 * adjusted_total
        scale = blend_total / adjusted_total
        lam_home *= scale
        lam_away *= scale

    return max(lam_home, 0.05), max(lam_away, 0.05), {"adjustment_notes": notes}

def form_score(stats: dict[str, Any]) -> float:
    if not stats:
        return 0.0
    return (
        0.70 * safe_float(stats.get("ppg"))
        + 0.28 * safe_float(stats.get("gd_pg"))
        + 0.12 * (safe_float(stats.get("gf_pg")) - 1.25)
        - 0.10 * (safe_float(stats.get("ga_pg")) - 1.10)
    )

def rest_days(stats: dict[str, Any], match_dt: datetime) -> float | None:
    last = stats.get("last_match_utc")
    if not isinstance(last, datetime):
        return None
    return (match_dt - last).total_seconds() / 86400.0

def leader_goal_signal(leaders: dict[str, Any]) -> float:
    top_goals = leaders.get("top_goals", [])
    if not top_goals:
        return 0.0
    return sum(item.get("value", 0.0) for item in top_goals[:3])

def final_score_distribution_with_extra_time(
    lam_home_90: float,
    lam_away_90: float,
    et_factor: float,
) -> dict[tuple[int, int], float]:
    regular = score_distribution(lam_home_90, lam_away_90, 8)
    final: dict[tuple[int, int], float] = defaultdict(float)
    et_home_pmf = poisson_pmf(lam_home_90 * et_factor, 5)
    et_away_pmf = poisson_pmf(lam_away_90 * et_factor, 5)
    for (h, a), prob in regular.items():
        if h != a:
            final[(h, a)] += prob
        else:
            for eh, ph in enumerate(et_home_pmf):
                for ea, pa in enumerate(et_away_pmf):
                    final[(h + eh, a + ea)] += prob * ph * pa
    total = sum(final.values())
    return {score: prob / total for score, prob in final.items()}

def predict_match(
    event: dict[str, Any],
    summary: dict[str, Any],
    group_stats: dict[str, dict[str, Any]],
    elo_map: dict[str, dict[str, Any]],
    league_news: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    competitors = event_competitors(event)
    home = competitors["home"]
    away = competitors["away"]
    match_dt = parse_dt(event.get("date"))
    odds = extract_odds(event, summary)
    market_lam_home, market_lam_away, fit_info = fit_market_lambdas(odds)
    leaders = extract_leaders(summary)
    lam_home, lam_away, adjustment = context_adjust_lambdas(
        market_lam_home,
        market_lam_away,
        home["name"],
        away["name"],
        match_dt,
        group_stats,
        elo_map,
        leaders,
    )

    regular_scores = score_distribution(lam_home, lam_away, 10)
    regular_outcomes = outcome_probs(regular_scores)
    final_scores = final_score_distribution_with_extra_time(
        lam_home,
        lam_away,
        float(config["extra_time_goal_factor"]),
    )
    final_outcomes = outcome_probs(final_scores)

    ranked_scores = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)
    safe_score, safe_prob = ranked_scores[0]
    recommended_score, recommended_prob, recommended_value = choose_mpp_score(
        final_scores, final_outcomes, odds, config
    )
    aggressive_score, aggressive_prob = choose_aggressive_score(final_scores, final_outcomes, odds)

    news_notes = extract_news_notes(summary, league_news, home, away)
    confidence = confidence_label(final_outcomes, recommended_prob)
    risk = risk_label(final_outcomes, recommended_score)

    return {
        "event_id": str(event.get("id")),
        "match_utc": match_dt.isoformat() if match_dt else "",
        "match_paris": match_dt.astimezone(PARIS_TZ).strftime("%Y-%m-%d %H:%M") if match_dt else "",
        "home": home,
        "away": away,
        "match": f"{home['name']} - {away['name']}",
        "odds": odds,
        "fit_info": fit_info,
        "lambda_home_90": lam_home,
        "lambda_away_90": lam_away,
        "market_lambda_home_90": market_lam_home,
        "market_lambda_away_90": market_lam_away,
        "regular_outcomes": regular_outcomes,
        "final_outcomes": final_outcomes,
        "recommended_score": score_text(recommended_score),
        "recommended_score_tuple": recommended_score,
        "recommended_exact_probability": recommended_prob,
        "recommended_value": recommended_value,
        "safe_score": score_text(safe_score),
        "safe_exact_probability": safe_prob,
        "aggressive_score": score_text(aggressive_score),
        "aggressive_exact_probability": aggressive_prob,
        "top_scores": [
            {"score": score_text(score), "probability": prob}
            for score, prob in ranked_scores[:8]
        ],
        "confidence": confidence,
        "risk": risk,
        "group_home": group_stats.get(home["name"], {}),
        "group_away": group_stats.get(away["name"], {}),
        "elo_home": elo_map.get(home["name"], {}),
        "elo_away": elo_map.get(away["name"], {}),
        "leaders_home": leaders.get(home["name"], {}),
        "leaders_away": leaders.get(away["name"], {}),
        "news_notes": news_notes,
        "adjustment": adjustment,
        "source_url": f"https://www.espn.com/soccer/match/_/gameId/{event.get('id')}",
    }

def choose_mpp_score(
    final_scores: dict[tuple[int, int], float],
    final_outcomes: dict[str, float],
    odds: dict[str, Any],
    config: dict[str, Any],
) -> tuple[tuple[int, int], float, float]:
    fair = odds.get("moneyline_fair", {}) or {}
    best: tuple[tuple[int, int], float, float] | None = None
    for score, exact_prob in final_scores.items():
        outcome = score_outcome(score)
        outcome_prob = final_outcomes[outcome]
        fair_result_prob = fair.get(outcome, outcome_prob)
        leverage = 1.0 / max(fair_result_prob, 0.08)
        value = (
            float(config["exact_score_weight"]) * exact_prob
            + float(config["result_weight"]) * outcome_prob * exact_prob
            + float(config["underdog_boost"]) * exact_prob * math.log1p(leverage)
        )
        if best is None or value > best[2]:
            best = (score, exact_prob, value)
    assert best is not None
    return best

def choose_aggressive_score(
    final_scores: dict[tuple[int, int], float],
    final_outcomes: dict[str, float],
    odds: dict[str, Any],
) -> tuple[tuple[int, int], float]:
    fair = odds.get("moneyline_fair", {}) or {}
    ranked = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)
    safe_score = ranked[0][0]
    top_prob = ranked[0][1]
    candidates = []
    for score, prob in ranked[:25]:
        if score == safe_score:
            continue
        if prob < top_prob * 0.35:
            continue
        outcome = score_outcome(score)
        leverage = 1.0 / max(fair.get(outcome, final_outcomes[outcome]), 0.08)
        exact_rarity = top_prob / max(prob, 0.001)
        candidates.append((prob * (leverage ** 0.42) * (exact_rarity ** 0.18), score, prob))
    if not candidates:
        return ranked[1] if len(ranked) > 1 else ranked[0]
    _, score, prob = max(candidates, key=lambda item: item[0])
    return score, prob

def score_outcome(score: tuple[int, int]) -> str:
    if score[0] > score[1]:
        return "home"
    if score[0] < score[1]:
        return "away"
    return "draw"

def score_text(score: tuple[int, int]) -> str:
    return f"{score[0]}-{score[1]}"

def confidence_label(outcomes: dict[str, float], exact_prob: float) -> str:
    sorted_outcomes = sorted(outcomes.values(), reverse=True)
    edge = sorted_outcomes[0] - sorted_outcomes[1]
    if edge > 0.28 and exact_prob > 0.10:
        return "forte"
    if edge > 0.16:
        return "moyenne+"
    if edge > 0.08:
        return "moyenne"
    return "faible"

def risk_label(outcomes: dict[str, float], score: tuple[int, int]) -> str:
    outcome = score_outcome(score)
    p = outcomes[outcome]
    if p >= 0.62:
        return "prudent"
    if p >= 0.48:
        return "equilibre"
    return "agressif"

