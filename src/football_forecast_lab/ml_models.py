from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .metrics import accuracy, brier_score, log_loss, summarize_metric_rows
from .training_data import MatchExample


CLASS_NAMES = ["home", "draw", "away"]


@dataclass
class Dataset:
    x: list[list[float]]
    y: list[int]
    examples: list[MatchExample]
    feature_names: list[str]
    means: list[float]
    scales: list[float]


def make_dataset(
    examples: list[MatchExample],
    feature_names: list[str],
    means: list[float] | None = None,
    scales: list[float] | None = None,
) -> Dataset:
    raw = [[float(example.features[name]) for name in feature_names] for example in examples]
    if means is None:
        means = column_means(raw)
    if scales is None:
        scales = column_scales(raw, means)
    x = [
        [(value - means[index]) / scales[index] for index, value in enumerate(row)]
        for row in raw
    ]
    return Dataset(x=x, y=[example.target for example in examples], examples=examples, feature_names=feature_names, means=means, scales=scales)


def train_softmax(
    dataset: Dataset,
    learning_rate: float = 0.04,
    l2: float = 0.001,
    epochs: int = 35,
    seed: int = 42,
) -> dict[str, Any]:
    rng = random.Random(seed)
    feature_count = len(dataset.feature_names)
    weights = [[0.0 for _ in range(feature_count + 1)] for _ in range(3)]
    indexes = list(range(len(dataset.x)))
    for _ in range(epochs):
        rng.shuffle(indexes)
        for index in indexes:
            row = [1.0, *dataset.x[index]]
            probs = softmax([dot(weights[class_index], row) for class_index in range(3)])
            for class_index in range(3):
                error = probs[class_index] - (1.0 if dataset.y[index] == class_index else 0.0)
                for feature_index, value in enumerate(row):
                    penalty = l2 * weights[class_index][feature_index] if feature_index else 0.0
                    weights[class_index][feature_index] -= learning_rate * (error * value + penalty)
    return {
        "type": "softmax_regression",
        "feature_names": dataset.feature_names,
        "means": dataset.means,
        "scales": dataset.scales,
        "weights": weights,
        "learning_rate": learning_rate,
        "l2": l2,
        "epochs": epochs,
    }


def predict_softmax(model: dict[str, Any], dataset: Dataset) -> list[dict[str, float]]:
    output = []
    weights = model["weights"]
    for row in dataset.x:
        values = [1.0, *row]
        probs = softmax([dot(weights[class_index], values) for class_index in range(3)])
        output.append({CLASS_NAMES[index]: probs[index] for index in range(3)})
    return output


def baseline_majority(train_examples: list[MatchExample], count: int) -> list[dict[str, float]]:
    totals = [1.0, 1.0, 1.0]
    for example in train_examples:
        totals[example.target] += 1.0
    total = sum(totals)
    probs = {CLASS_NAMES[index]: totals[index] / total for index in range(3)}
    return [dict(probs) for _ in range(count)]


def baseline_elo(dataset: Dataset) -> list[dict[str, float]]:
    output = []
    names = dataset.feature_names
    elo_idx = names.index("elo_diff")
    home_idx = names.index("home_advantage") if "home_advantage" in names else None
    for row in dataset.x:
        raw_diff = row[elo_idx] * dataset.scales[elo_idx] + dataset.means[elo_idx]
        if home_idx is not None:
            raw_diff += 65.0 * (row[home_idx] * dataset.scales[home_idx] + dataset.means[home_idx])
        decisive = 1.0 / (1.0 + math.exp(-raw_diff / 310.0))
        draw = 0.245 - 0.045 * min(1.0, abs(raw_diff) / 450.0)
        home = (1.0 - draw) * decisive
        away = (1.0 - draw) * (1.0 - decisive)
        output.append({"home": home, "draw": draw, "away": away})
    return output


def evaluate_predictions(probs: list[dict[str, float]], examples: list[MatchExample]) -> dict[str, float]:
    rows = []
    for prob, example in zip(probs, examples):
        actual = CLASS_NAMES[example.target]
        rows.append(
            {
                "log_loss": log_loss(prob, actual),
                "brier_score": brier_score(prob, actual),
                "accuracy": accuracy(prob, actual),
            }
        )
    return summarize_metric_rows(rows)


def split_examples(examples: list[MatchExample]) -> tuple[list[MatchExample], list[MatchExample], list[MatchExample]]:
    train = [example for example in examples if example.date.year <= 2018]
    validation = [example for example in examples if 2019 <= example.date.year <= 2022]
    test = [example for example in examples if example.date.year >= 2023]
    return train, validation, test


def run_model_grid(examples: list[MatchExample]) -> dict[str, Any]:
    train, validation, test = split_examples(examples)
    feature_sets = {
        "elo": ["elo_diff", "home_advantage", "is_world_cup", "is_qualifier", "is_friendly", "is_continental"],
        "elo_form": [
            "elo_diff",
            "home_advantage",
            "form_points_diff",
            "form_gd_diff",
            "form_gf_diff",
            "form_ga_diff",
            "rest_diff",
            "is_world_cup",
            "is_qualifier",
            "is_friendly",
            "is_continental",
        ],
        "full": [
            "home_elo",
            "away_elo",
            "elo_diff",
            "home_advantage",
            "form_points_diff",
            "form_gd_diff",
            "form_gf_diff",
            "form_ga_diff",
            "rest_diff",
            "is_world_cup",
            "is_qualifier",
            "is_friendly",
            "is_continental",
        ],
    }
    results = []

    baseline_dataset = make_dataset(validation, feature_sets["elo"], *normalizers(train, feature_sets["elo"]))
    results.append({"model": "majority", "feature_set": "none", "validation": evaluate_predictions(baseline_majority(train, len(validation)), validation)})
    results.append({"model": "elo_baseline", "feature_set": "elo", "validation": evaluate_predictions(baseline_elo(baseline_dataset), validation)})

    best: dict[str, Any] | None = None
    for feature_set_name, feature_names in feature_sets.items():
        means, scales = normalizers(train, feature_names)
        train_dataset = make_dataset(train, feature_names, means, scales)
        validation_dataset = make_dataset(validation, feature_names, means, scales)
        for learning_rate in (0.02, 0.05):
            for l2 in (0.0005, 0.005):
                for epochs in (12, 24):
                    model = train_softmax(train_dataset, learning_rate=learning_rate, l2=l2, epochs=epochs)
                    validation_metrics = evaluate_predictions(predict_softmax(model, validation_dataset), validation)
                    result = {
                        "model": "softmax",
                        "feature_set": feature_set_name,
                        "learning_rate": learning_rate,
                        "l2": l2,
                        "epochs": epochs,
                        "validation": validation_metrics,
                        "artifact": model,
                    }
                    results.append(result)
                    if best is None or validation_metrics["log_loss"] < best["validation"]["log_loss"]:
                        best = result

    assert best is not None
    feature_names = feature_sets[best["feature_set"]]
    train_plus_validation = train + validation
    means, scales = normalizers(train_plus_validation, feature_names)
    final_train_dataset = make_dataset(train_plus_validation, feature_names, means, scales)
    test_dataset = make_dataset(test, feature_names, means, scales)
    final_model = train_softmax(
        final_train_dataset,
        learning_rate=best["learning_rate"],
        l2=best["l2"],
        epochs=best["epochs"],
    )
    test_metrics = evaluate_predictions(predict_softmax(final_model, test_dataset), test)
    test_baselines = {
        "majority": evaluate_predictions(baseline_majority(train_plus_validation, len(test)), test),
        "elo_baseline": evaluate_predictions(baseline_elo(make_dataset(test, feature_sets["elo"], *normalizers(train_plus_validation, feature_sets["elo"]))), test),
    }

    clean_results = [{key: value for key, value in result.items() if key != "artifact"} for result in results]
    clean_results.sort(key=lambda item: item["validation"]["log_loss"])
    return {
        "source": "martj42/international_results results.csv",
        "row_counts": {"train": len(train), "validation": len(validation), "test": len(test), "total": len(examples)},
        "best_validation": {key: value for key, value in best.items() if key != "artifact"},
        "test_metrics": test_metrics,
        "test_baselines": test_baselines,
        "leaderboard": clean_results[:20],
        "all_results_count": len(results),
        "final_model": final_model,
    }


def write_model_artifact(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def normalizers(examples: list[MatchExample], feature_names: list[str]) -> tuple[list[float], list[float]]:
    raw = [[float(example.features[name]) for name in feature_names] for example in examples]
    means = column_means(raw)
    scales = column_scales(raw, means)
    for index, name in enumerate(feature_names):
        if name == "home_advantage" or name.startswith("is_"):
            means[index] = 0.0
            scales[index] = 1.0
    return means, scales


def column_means(rows: list[list[float]]) -> list[float]:
    if not rows:
        return []
    return [sum(row[index] for row in rows) / len(rows) for index in range(len(rows[0]))]


def column_scales(rows: list[list[float]], means: list[float]) -> list[float]:
    if not rows:
        return []
    scales = []
    for index, mean in enumerate(means):
        variance = sum((row[index] - mean) ** 2 for row in rows) / len(rows)
        scales.append(math.sqrt(variance) or 1.0)
    return scales


def softmax(values: list[float]) -> list[float]:
    top = max(values)
    exps = [math.exp(value - top) for value in values]
    total = sum(exps)
    return [value / total for value in exps]


def dot(weights: list[float], values: list[float]) -> float:
    return sum(weight * value for weight, value in zip(weights, values))
