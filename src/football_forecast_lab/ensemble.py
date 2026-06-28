from __future__ import annotations


def blend_probabilities(*weighted_probs: tuple[float, dict[str, float]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for weight, probs in weighted_probs:
        for key, value in probs.items():
            totals[key] = totals.get(key, 0.0) + weight * value
    normalizer = sum(totals.values())
    if normalizer <= 0:
        return totals
    return {key: value / normalizer for key, value in totals.items()}
