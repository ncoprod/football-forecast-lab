from __future__ import annotations

from typing import Any

from .history import actual_outcome
from .ledger import attach_resolved_results, validate_ledger_rows
from .metrics import accuracy, brier_score, log_loss, score_log_loss, score_top_k, summarize_metric_rows


def evaluate_outcome_predictions(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Evaluate rows with probabilities and actual scores.

    Expected probability keys: p_home, p_draw, p_away.
    Expected score keys: home_score, away_score.
    """
    metric_rows = []
    for row in rows:
        probs = {
            "home": float(row["p_home"]),
            "draw": float(row["p_draw"]),
            "away": float(row["p_away"]),
        }
        actual = actual_outcome(row)
        metric_rows.append(
            {
                "log_loss": log_loss(probs, actual),
                "brier_score": brier_score(probs, actual),
                "accuracy": accuracy(probs, actual),
            }
        )
    return summarize_metric_rows(metric_rows)


def evaluate_ledger_predictions(
    rows: list[dict[str, Any]],
    resolved_results: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate resolved clean pre-match ledger rows.

    Prediction rows remain immutable. Final scores are joined from a separate
    results ledger at evaluation time.
    """
    validate_ledger_rows(rows)
    rows = attach_resolved_results(rows, resolved_results)
    resolved = [
        row for row in rows
        if row.get("actual_home_score") is not None and row.get("actual_away_score") is not None
    ]
    unresolved = [
        row for row in rows
        if row.get("actual_home_score") is None or row.get("actual_away_score") is None
    ]
    pending = len(unresolved)
    if not resolved:
        return {
            "rows": len(rows),
            "unique_events": unique_event_count(rows),
            "resolved": 0,
            "resolved_events": 0,
            "pending": pending,
            "pending_events": unique_event_count(rows),
            "metrics": {},
        }

    metric_rows = []
    for row in resolved:
        actual = resolved_actual_outcome(row)
        probabilities = final_result_probabilities(row)
        actual_score = f"{int(row['actual_home_score'])}-{int(row['actual_away_score'])}"
        scores = row.get("score_distribution_after_extra", [])
        metric_rows.append(
            {
                "final_log_loss": log_loss(probabilities, actual),
                "final_brier_score": brier_score(probabilities, actual),
                "final_accuracy": accuracy(probabilities, actual),
                "final_score_top1": score_top_k(scores, actual_score, 1),
                "final_score_top3": score_top_k(scores, actual_score, 3),
                "final_score_top5": score_top_k(scores, actual_score, 5),
                "final_score_log_loss": score_log_loss(scores, actual_score),
                "closing_line_value": closing_line_value(row),
            }
        )
    return {
        "rows": len(rows),
        "unique_events": unique_event_count(rows),
        "resolved": len(resolved),
        "resolved_events": unique_event_count(resolved),
        "pending": pending,
        "pending_events": unique_event_count(unresolved),
        "score_scope": "espn_final_score_vs_after_extra_distribution",
        "metrics": summarize_metric_rows(metric_rows),
    }


def final_result_probabilities(row: dict[str, Any]) -> dict[str, float]:
    for key in ("advancement_probabilities", "final_outcomes", "calibrated_probabilities", "probabilities"):
        probabilities = coerce_probabilities(row.get(key) or {})
        if sum(probabilities.values()) > 0:
            return probabilities
    return {"home": 0.0, "draw": 0.0, "away": 0.0}


def coerce_probabilities(values: dict[str, Any]) -> dict[str, float]:
    probabilities: dict[str, float] = {}
    for outcome in ("home", "draw", "away"):
        try:
            probabilities[outcome] = float(values.get(outcome, 0.0) or 0.0)
        except (TypeError, ValueError):
            probabilities[outcome] = 0.0
    return probabilities


def resolved_actual_outcome(row: dict[str, Any]) -> str:
    home = int(row["actual_home_score"])
    away = int(row["actual_away_score"])
    if home > away:
        return "home"
    if home < away:
        return "away"
    return "draw"


def unique_event_count(rows: list[dict[str, Any]]) -> int:
    return len({str(row.get("event_id")) for row in rows if row.get("event_id") is not None})


def closing_line_value(row: dict[str, Any]) -> float:
    recommended = row.get("recommended_result")
    probabilities = row.get("probabilities") or {}
    closing = row.get("closing_odds") or {}
    closing_probabilities = closing.get("probabilities") or {}
    if not recommended or recommended not in probabilities or recommended not in closing_probabilities:
        return 0.0
    return float(probabilities[recommended]) - float(closing_probabilities[recommended])
