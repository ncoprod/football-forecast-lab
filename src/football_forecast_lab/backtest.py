from __future__ import annotations

from typing import Any

from .history import actual_outcome
from .metrics import accuracy, brier_score, log_loss, summarize_metric_rows


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
