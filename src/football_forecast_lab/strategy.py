from __future__ import annotations

from typing import Any


STRATEGIES = {
    "safe": {"underdog_multiplier": 0.4, "exact_multiplier": 0.8},
    "balanced": {"underdog_multiplier": 1.0, "exact_multiplier": 1.0},
    "chase": {"underdog_multiplier": 1.8, "exact_multiplier": 1.15},
}


def choose_strategy(rank_gap: int | None = None) -> str:
    if rank_gap is None:
        return "balanced"
    if rank_gap <= 0:
        return "safe"
    if rank_gap >= 20:
        return "chase"
    return "balanced"


def score_strategy_label(prediction: dict[str, Any]) -> str:
    if prediction["risk"] == "prudent":
        return "safe"
    if prediction["risk"] == "agressif":
        return "chase"
    return "balanced"
