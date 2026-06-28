from __future__ import annotations

from typing import Any

from .history import actual_outcome
from .ledger import validate_ledger_rows
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


def evaluate_ledger_predictions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate resolved clean pre-match ledger rows.

    Rows without `actual_home_score` and `actual_away_score` are counted as pending.
    """
    validate_ledger_rows(rows)
    resolved = [
        row for row in rows
        if row.get("actual_home_score") is not None and row.get("actual_away_score") is not None
    ]
    pending = len(rows) - len(resolved)
    if not resolved:
        return {"rows": len(rows), "resolved": 0, "pending": pending, "metrics": {}}

    metric_rows = []
    for row in resolved:
        actual = resolved_actual_outcome(row)
        probabilities = row.get("calibrated_probabilities") or row.get("probabilities") or {}
        actual_score = f"{int(row['actual_home_score'])}-{int(row['actual_away_score'])}"
        scores = row.get("score_distribution_90", [])
        metric_rows.append(
            {
                "log_loss": log_loss(probabilities, actual),
                "brier_score": brier_score(probabilities, actual),
                "accuracy": accuracy(probabilities, actual),
                "score_top1": score_top_k(scores, actual_score, 1),
                "score_top3": score_top_k(scores, actual_score, 3),
                "score_top5": score_top_k(scores, actual_score, 5),
                "score_log_loss": score_log_loss(scores, actual_score),
                "closing_line_value": closing_line_value(row),
            }
        )
    return {
        "rows": len(rows),
        "resolved": len(resolved),
        "pending": pending,
        "metrics": summarize_metric_rows(metric_rows),
    }


def resolved_actual_outcome(row: dict[str, Any]) -> str:
    home = int(row["actual_home_score"])
    away = int(row["actual_away_score"])
    if home > away:
        return "home"
    if home < away:
        return "away"
    return "draw"


def closing_line_value(row: dict[str, Any]) -> float:
    recommended = row.get("recommended_result")
    probabilities = row.get("probabilities") or {}
    closing = row.get("closing_odds") or {}
    closing_probabilities = closing.get("probabilities") or {}
    if not recommended or recommended not in probabilities or recommended not in closing_probabilities:
        return 0.0
    return float(probabilities[recommended]) - float(closing_probabilities[recommended])
