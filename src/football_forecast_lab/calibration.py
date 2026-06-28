from __future__ import annotations

from typing import Any


def reliability_bins(rows: list[dict[str, Any]], probability_key: str, actual_key: str, bins: int = 10) -> list[dict[str, float]]:
    buckets = [{"count": 0, "prob_sum": 0.0, "actual_sum": 0.0} for _ in range(bins)]
    for row in rows:
        probability = max(0.0, min(1.0, float(row[probability_key])))
        index = min(bins - 1, int(probability * bins))
        buckets[index]["count"] += 1
        buckets[index]["prob_sum"] += probability
        buckets[index]["actual_sum"] += float(row[actual_key])
    output = []
    for index, bucket in enumerate(buckets):
        count = bucket["count"]
        output.append(
            {
                "bin": index,
                "count": count,
                "mean_probability": bucket["prob_sum"] / count if count else 0.0,
                "observed_rate": bucket["actual_sum"] / count if count else 0.0,
            }
        )
    return output


def shrink_to_market(model_probability: float, market_probability: float, model_weight: float) -> float:
    weight = max(0.0, min(1.0, model_weight))
    return weight * model_probability + (1.0 - weight) * market_probability
