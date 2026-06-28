from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .settings import LEDGER_DIR
from .utils import parse_dt


PRE_MATCH_JSONL = "pre_match_predictions.jsonl"
PRE_MATCH_CSV = "pre_match_predictions.csv"
ODDS_JSONL = "odds_snapshots.jsonl"
RESOLVED_RESULTS_JSONL = "resolved_results.jsonl"
RESOLVED_RESULTS_CSV = "resolved_results.csv"


def append_pre_match_snapshots(audit: dict[str, Any], ledger_dir: Path = LEDGER_DIR) -> dict[str, int]:
    ledger_dir.mkdir(parents=True, exist_ok=True)
    prediction_rows = pre_match_prediction_rows(audit)
    odds_rows = odds_snapshot_rows(audit)
    append_jsonl(ledger_dir / PRE_MATCH_JSONL, prediction_rows)
    append_jsonl(ledger_dir / ODDS_JSONL, odds_rows)
    append_prediction_csv(ledger_dir / PRE_MATCH_CSV, prediction_rows)
    return {"prediction_rows": len(prediction_rows), "odds_rows": len(odds_rows)}


def pre_match_prediction_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    generated_at = parse_dt(audit.get("generated_at_utc"))
    rows = []
    for prediction in audit.get("predictions", []):
        kickoff = parse_dt(prediction.get("match_utc"))
        if not is_clean_pre_match(generated_at, kickoff, prediction.get("forecast_status")):
            continue
        rows.append(
            {
                "generated_at_utc": audit.get("generated_at_utc"),
                "kickoff_utc": prediction.get("match_utc"),
                "forecast_status": prediction.get("forecast_status"),
                "event_id": prediction.get("event_id"),
                "model_version": prediction.get("model_version"),
                "home": prediction.get("home", {}).get("name"),
                "away": prediction.get("away", {}).get("name"),
                "market": prediction.get("odds", {}),
                "features": compact_features(prediction),
                "probabilities": {
                    "home": prediction.get("regular_outcomes", {}).get("home"),
                    "draw": prediction.get("regular_outcomes", {}).get("draw"),
                    "away": prediction.get("regular_outcomes", {}).get("away"),
                },
                "advancement_probabilities": {
                    "home": prediction.get("final_outcomes", {}).get("home"),
                    "draw": prediction.get("final_outcomes", {}).get("draw"),
                    "away": prediction.get("final_outcomes", {}).get("away"),
                },
                "calibrated_probabilities": prediction.get("calibrated_probabilities", {}),
                "score_distribution_90": prediction.get("score_distribution_90", []),
                "score_distribution_after_extra": prediction.get("score_distribution_after_extra", []),
                "top_scores_90": prediction.get("top_scores_90", []),
                "top_scores_after_extra": prediction.get("top_scores_after_extra", []),
                "recommended_result": prediction.get("recommended_result_key"),
                "recommended_advancement_result": prediction.get("recommended_advancement_result_key"),
                "recommended_score_90": prediction.get("recommended_score_90"),
                "recommended_score_after_extra": prediction.get("recommended_score_after_extra"),
                "no_bet_reason": prediction.get("no_bet_reason", ""),
                "stake_eur": prediction.get("stake_eur", 0.0),
                "closing_odds": None,
            }
        )
    return rows


def odds_snapshot_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    generated_at = parse_dt(audit.get("generated_at_utc"))
    rows = []
    for prediction in audit.get("predictions", []):
        kickoff = parse_dt(prediction.get("match_utc"))
        if not is_clean_pre_match(generated_at, kickoff, prediction.get("forecast_status")):
            continue
        rows.append(
            {
                "generated_at_utc": audit.get("generated_at_utc"),
                "kickoff_utc": prediction.get("match_utc"),
                "event_id": prediction.get("event_id"),
                "home": prediction.get("home", {}).get("name"),
                "away": prediction.get("away", {}).get("name"),
                "market": prediction.get("odds", {}),
                "source_status": audit.get("optional_odds", {}).get("sources", {}),
            }
        )
    return rows


def is_clean_pre_match(generated_at: datetime | None, kickoff: datetime | None, status: str | None) -> bool:
    return bool(generated_at and kickoff and generated_at < kickoff and status == "pre_match")


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("a", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str) + "\n")


def append_prediction_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    exists = path.exists()
    fieldnames = [
        "generated_at_utc",
        "kickoff_utc",
        "forecast_status",
        "event_id",
        "model_version",
        "home",
        "away",
        "p_home",
        "p_draw",
        "p_away",
        "recommended_result",
        "recommended_score_90",
        "recommended_score_after_extra",
        "no_bet_reason",
        "stake_eur",
    ]
    with path.open("a", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        for row in rows:
            probabilities = row.get("probabilities", {})
            writer.writerow(
                {
                    "generated_at_utc": row.get("generated_at_utc"),
                    "kickoff_utc": row.get("kickoff_utc"),
                    "forecast_status": row.get("forecast_status"),
                    "event_id": row.get("event_id"),
                    "model_version": row.get("model_version"),
                    "home": row.get("home"),
                    "away": row.get("away"),
                    "p_home": probabilities.get("home"),
                    "p_draw": probabilities.get("draw"),
                    "p_away": probabilities.get("away"),
                    "recommended_result": row.get("recommended_result"),
                    "recommended_score_90": row.get("recommended_score_90"),
                    "recommended_score_after_extra": row.get("recommended_score_after_extra"),
                    "no_bet_reason": row.get("no_bet_reason"),
                    "stake_eur": row.get("stake_eur"),
                }
            )


def compact_features(prediction: dict[str, Any]) -> dict[str, Any]:
    return {
        "lambda_home_90": prediction.get("lambda_home_90"),
        "lambda_away_90": prediction.get("lambda_away_90"),
        "elo_home": prediction.get("elo_home", {}).get("rating"),
        "elo_away": prediction.get("elo_away", {}).get("rating"),
        "group_home": prediction.get("group_home"),
        "group_away": prediction.get("group_away"),
        "api_football": prediction.get("api_football", {}),
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def append_resolved_results(rows: list[dict[str, Any]], ledger_dir: Path = LEDGER_DIR) -> dict[str, int]:
    """Append newly completed match results without rewriting prior facts."""
    ledger_dir.mkdir(parents=True, exist_ok=True)
    existing = load_resolved_results(ledger_dir / RESOLVED_RESULTS_JSONL)
    new_rows = [row for row in rows if str(row.get("event_id")) not in existing]
    append_jsonl(ledger_dir / RESOLVED_RESULTS_JSONL, new_rows)
    append_results_csv(ledger_dir / RESOLVED_RESULTS_CSV, new_rows)
    return {"input_rows": len(rows), "appended_rows": len(new_rows), "skipped_existing": len(rows) - len(new_rows)}


def append_results_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    exists = path.exists()
    fieldnames = [
        "resolved_at_utc",
        "event_id",
        "match_utc",
        "home",
        "away",
        "actual_home_score",
        "actual_away_score",
        "actual_score_scope",
        "actual_result",
        "status",
        "status_detail",
        "source",
    ]
    with path.open("a", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def load_resolved_results(path: Path) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(path):
        event_id = str(row.get("event_id", ""))
        if event_id:
            results[event_id] = row
    return results


def attach_resolved_results(
    rows: list[dict[str, Any]],
    resolved_results: dict[str, dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not resolved_results:
        return [dict(row) for row in rows]
    merged_rows = []
    for row in rows:
        merged = dict(row)
        result = resolved_results.get(str(row.get("event_id")))
        if result:
            merged.update(result)
        merged_rows.append(merged)
    return merged_rows


def validate_ledger_rows(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        generated_at = parse_dt(row.get("generated_at_utc"))
        kickoff = parse_dt(row.get("kickoff_utc"))
        if not is_clean_pre_match(generated_at, kickoff, row.get("forecast_status")):
            raise AssertionError(f"Ledger row is not clean pre-match: {row.get('event_id')}")
