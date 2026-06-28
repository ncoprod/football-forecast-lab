from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ml_models import CLASS_NAMES, dot, softmax
from .settings import REPO_ROOT


MODEL_PATH = REPO_ROOT / "models" / "international_softmax_v1.json"


def load_trained_model() -> dict[str, Any] | None:
    if not MODEL_PATH.exists():
        return None
    return json.loads(MODEL_PATH.read_text(encoding="utf-8"))


def predict_from_match_features(model: dict[str, Any], features: dict[str, float]) -> dict[str, float]:
    values = [1.0]
    for index, name in enumerate(model["feature_names"]):
        mean = float(model["means"][index])
        scale = float(model["scales"][index]) or 1.0
        values.append((float(features.get(name, 0.0)) - mean) / scale)
    weights = model["weights"]
    probabilities = softmax([dot(weights[class_index], values) for class_index in range(3)])
    return {CLASS_NAMES[index]: probabilities[index] for index in range(3)}


def live_ml_features(prediction: dict[str, Any]) -> dict[str, float]:
    return {
        "home_elo": float(prediction["elo_home"].get("rating", 1500.0)),
        "away_elo": float(prediction["elo_away"].get("rating", 1500.0)),
        "elo_diff": float(prediction["elo_home"].get("rating", 1500.0)) - float(prediction["elo_away"].get("rating", 1500.0)),
        "home_advantage": 1.0,
        "form_points_diff": float(prediction["group_home"].get("ppg", 0.0)) - float(prediction["group_away"].get("ppg", 0.0)),
        "form_gd_diff": float(prediction["group_home"].get("gd_pg", 0.0)) - float(prediction["group_away"].get("gd_pg", 0.0)),
        "form_gf_diff": float(prediction["group_home"].get("gf_pg", 0.0)) - float(prediction["group_away"].get("gf_pg", 0.0)),
        "form_ga_diff": float(prediction["group_away"].get("ga_pg", 0.0)) - float(prediction["group_home"].get("ga_pg", 0.0)),
        "rest_diff": 0.0,
        "is_world_cup": 1.0,
        "is_qualifier": 0.0,
        "is_friendly": 0.0,
        "is_continental": 0.0,
    }


def enrich_predictions_with_ml(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    model = load_trained_model()
    if model is None:
        return {"status": "missing_model", "path": str(MODEL_PATH)}
    for prediction in predictions:
        ml_probs = predict_from_match_features(model, live_ml_features(prediction))
        prediction["trained_ml"] = {
            "model": MODEL_PATH.name,
            "probabilities": ml_probs,
            "note": "Historical softmax layer trained without historical odds; use as a secondary signal, not a market replacement.",
        }
    return {
        "status": "ok",
        "path": str(MODEL_PATH),
        "feature_names": model["feature_names"],
        "model_type": model.get("type", "unknown"),
    }
