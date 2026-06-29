from __future__ import annotations

from typing import Any


H2H_EDGE_THRESHOLD = 0.035
TOTALS_EDGE_THRESHOLD = 0.040
TOTALS_MIN_PROBABILITY = 0.54
H2H_MIN_PROBABILITY = 0.45
MIN_LIVE_RESOLVED_ROWS_FOR_REAL_STAKING = 30


def build_market_edge_rows(
    audit: dict[str, Any],
    availability_rows: list[dict[str, Any]] | None = None,
    live_resolved_rows: int = 0,
) -> list[dict[str, Any]]:
    availability_by_event = {
        str(row.get("event_id")): row
        for row in availability_rows or []
    }
    rows = []
    for raw_prediction in audit.get("predictions", []) or []:
        prediction = dict(raw_prediction)
        prediction["generated_at_utc"] = audit.get("generated_at_utc")
        availability = availability_by_event.get(str(prediction.get("event_id")), {})
        rows.extend(h2h_candidates(prediction, availability, live_resolved_rows))
        rows.extend(total_candidates(prediction, availability, live_resolved_rows))
    return sorted(rows, key=lambda row: (row["decision_rank"], -row["rank_score"], row["kickoff_utc"], row["match"]))


def h2h_candidates(
    prediction: dict[str, Any],
    availability: dict[str, Any],
    live_resolved_rows: int,
) -> list[dict[str, Any]]:
    market = (prediction.get("odds") or {}).get("moneyline_fair") or {}
    model = prediction.get("calibrated_probabilities") or prediction.get("regular_outcomes") or {}
    if not {"home", "draw", "away"}.issubset(market) or not {"home", "draw", "away"}.issubset(model):
        return [base_row(prediction, availability, live_resolved_rows, "1X2_90", "", None, None, "skip_missing_market")]

    rows = []
    for outcome in ("home", "draw", "away"):
        rows.append(
            candidate_row(
                prediction=prediction,
                availability=availability,
                live_resolved_rows=live_resolved_rows,
                market="1X2_90",
                selection=selection_label(prediction, outcome),
                selection_key=outcome,
                model_probability=float(model[outcome]),
                market_probability=float(market[outcome]),
                edge_threshold=H2H_EDGE_THRESHOLD,
                min_probability=H2H_MIN_PROBABILITY,
            )
        )
    return rows


def total_candidates(
    prediction: dict[str, Any],
    availability: dict[str, Any],
    live_resolved_rows: int,
) -> list[dict[str, Any]]:
    odds = prediction.get("odds") or {}
    line = odds.get("total_line")
    market_over = odds.get("over_fair")
    if line is None or market_over is None:
        return [base_row(prediction, availability, live_resolved_rows, "TOTALS_90", "", None, None, "skip_missing_market")]

    model_over = score_distribution_over_probability(prediction.get("score_distribution_90") or [], float(line))
    market_over = float(market_over)
    return [
        candidate_row(
            prediction=prediction,
            availability=availability,
            live_resolved_rows=live_resolved_rows,
            market="TOTALS_90",
            selection=f"Over {float(line):g}",
            selection_key="over",
            model_probability=model_over,
            market_probability=market_over,
            edge_threshold=TOTALS_EDGE_THRESHOLD,
            min_probability=TOTALS_MIN_PROBABILITY,
        ),
        candidate_row(
            prediction=prediction,
            availability=availability,
            live_resolved_rows=live_resolved_rows,
            market="TOTALS_90",
            selection=f"Under {float(line):g}",
            selection_key="under",
            model_probability=1.0 - model_over,
            market_probability=1.0 - market_over,
            edge_threshold=TOTALS_EDGE_THRESHOLD,
            min_probability=TOTALS_MIN_PROBABILITY,
        ),
    ]


def candidate_row(
    prediction: dict[str, Any],
    availability: dict[str, Any],
    live_resolved_rows: int,
    market: str,
    selection: str,
    selection_key: str,
    model_probability: float,
    market_probability: float,
    edge_threshold: float,
    min_probability: float,
) -> dict[str, Any]:
    edge = model_probability - market_probability
    penalty = float(availability.get("confidence_penalty") or 0.0)
    decision = decision_label(
        prediction.get("forecast_status"),
        edge,
        model_probability,
        edge_threshold,
        min_probability,
        penalty,
        live_resolved_rows,
    )
    row = base_row(
        prediction,
        availability,
        live_resolved_rows,
        market,
        selection,
        model_probability,
        market_probability,
        decision,
    )
    row.update(
        {
            "selection_key": selection_key,
            "edge": edge,
            "availability_penalty": penalty,
            "rank_score": edge - penalty,
            "paper_stake_eur": 0.10 if decision.startswith("paper_candidate") else 0.0,
            "real_stake_eur": 0.0,
        }
    )
    return row


def base_row(
    prediction: dict[str, Any],
    availability: dict[str, Any],
    live_resolved_rows: int,
    market: str,
    selection: str,
    model_probability: float | None,
    market_probability: float | None,
    decision: str,
) -> dict[str, Any]:
    return {
        "generated_at_utc": prediction.get("generated_at_utc"),
        "event_id": prediction.get("event_id"),
        "kickoff_utc": prediction.get("match_utc"),
        "match": prediction.get("match"),
        "forecast_status": prediction.get("forecast_status"),
        "market": market,
        "selection": selection,
        "selection_key": "",
        "model_probability": model_probability,
        "market_probability": market_probability,
        "edge": None if model_probability is None or market_probability is None else model_probability - market_probability,
        "availability_status": availability.get("availability_status", ""),
        "availability_penalty": float(availability.get("confidence_penalty") or 0.0),
        "live_resolved_rows": live_resolved_rows,
        "calibration_gate": calibration_gate(live_resolved_rows),
        "decision": decision,
        "decision_rank": decision_rank(decision),
        "rank_score": -1.0,
        "paper_stake_eur": 0.0,
        "real_stake_eur": 0.0,
    }


def decision_label(
    forecast_status: str | None,
    edge: float,
    model_probability: float,
    edge_threshold: float,
    min_probability: float,
    availability_penalty: float,
    live_resolved_rows: int,
) -> str:
    if forecast_status != "pre_match":
        return "skip_not_pre_match"
    if edge < edge_threshold:
        return "watch_only_edge_below_threshold"
    if model_probability < min_probability:
        return "watch_only_probability_too_low"
    if availability_penalty >= 0.05:
        return "paper_candidate_needs_lineup_check"
    if live_resolved_rows < MIN_LIVE_RESOLVED_ROWS_FOR_REAL_STAKING:
        return "paper_candidate_needs_live_calibration"
    return "paper_candidate_real_stake_review"


def calibration_gate(live_resolved_rows: int) -> str:
    if live_resolved_rows < MIN_LIVE_RESOLVED_ROWS_FOR_REAL_STAKING:
        return f"locked_until_{MIN_LIVE_RESOLVED_ROWS_FOR_REAL_STAKING}_resolved_rows"
    return "review_allowed"


def decision_rank(decision: str) -> int:
    if decision.startswith("paper_candidate"):
        return 0
    if decision.startswith("watch_only"):
        return 1
    return 2


def score_distribution_over_probability(scores: list[dict[str, Any]], line: float) -> float:
    probability = 0.0
    for item in scores:
        home_goals = int(item.get("home_goals", 0))
        away_goals = int(item.get("away_goals", 0))
        if home_goals + away_goals > line:
            probability += float(item.get("probability", 0.0))
    return probability


def selection_label(prediction: dict[str, Any], outcome: str) -> str:
    if outcome == "home":
        return prediction.get("home", {}).get("name", "home")
    if outcome == "away":
        return prediction.get("away", {}).get("name", "away")
    return "Draw"
