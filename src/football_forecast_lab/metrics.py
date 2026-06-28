from __future__ import annotations

import math
from typing import Any


OUTCOMES = ("home", "draw", "away")


def log_loss(probs: dict[str, float], actual: str, epsilon: float = 1e-12) -> float:
    probability = max(epsilon, min(1.0 - epsilon, probs.get(actual, 0.0)))
    return -math.log(probability)


def brier_score(probs: dict[str, float], actual: str) -> float:
    return sum((probs.get(outcome, 0.0) - (1.0 if outcome == actual else 0.0)) ** 2 for outcome in OUTCOMES)


def accuracy(probs: dict[str, float], actual: str) -> float:
    predicted = max(OUTCOMES, key=lambda outcome: probs.get(outcome, 0.0))
    return 1.0 if predicted == actual else 0.0


def score_top_k(scores: list[dict[str, Any]], actual_score: str, k: int = 3) -> float:
    return 1.0 if actual_score in {item["score"] for item in scores[:k]} else 0.0


def score_log_loss(scores: list[dict[str, Any]], actual_score: str, epsilon: float = 1e-12) -> float:
    probability = epsilon
    for item in scores:
        if item.get("score") == actual_score:
            probability = max(epsilon, min(1.0 - epsilon, float(item.get("probability", 0.0))))
            break
    return -math.log(probability)


def summarize_metric_rows(rows: list[dict[str, float]]) -> dict[str, float]:
    if not rows:
        return {}
    keys = sorted({key for row in rows for key in row})
    return {key: sum(row.get(key, 0.0) for row in rows) / len(rows) for key in keys}
