from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def prediction_feature_rows(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for pred in predictions:
        home = pred["home"]["name"]
        away = pred["away"]["name"]
        rows.append(
            {
                "event_id": pred["event_id"],
                "match_paris": pred["match_paris"],
                "home": home,
                "away": away,
                "home_elo": pred["elo_home"].get("rating"),
                "away_elo": pred["elo_away"].get("rating"),
                "elo_diff": _num(pred["elo_home"].get("rating")) - _num(pred["elo_away"].get("rating")),
                "home_group_points": pred["group_home"].get("points"),
                "away_group_points": pred["group_away"].get("points"),
                "home_group_gd": pred["group_home"].get("gd"),
                "away_group_gd": pred["group_away"].get("gd"),
                "market_home": pred["odds"].get("moneyline_fair", {}).get("home"),
                "market_draw": pred["odds"].get("moneyline_fair", {}).get("draw"),
                "market_away": pred["odds"].get("moneyline_fair", {}).get("away"),
                "lambda_home_90": pred["lambda_home_90"],
                "lambda_away_90": pred["lambda_away_90"],
                "p_home_after_extra": pred["final_outcomes"]["home"],
                "p_draw_after_extra": pred["final_outcomes"]["draw"],
                "p_away_after_extra": pred["final_outcomes"]["away"],
                "recommended_result": pred["recommended_result_key"],
                "recommended_result_probability": pred["recommended_result_probability"],
                "recommended_score": pred["recommended_score"],
                "recommended_exact_probability": pred["recommended_exact_probability"],
            }
        )
    return rows


def write_feature_store(path: Path, predictions: list[dict[str, Any]]) -> None:
    rows = prediction_feature_rows(predictions)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
