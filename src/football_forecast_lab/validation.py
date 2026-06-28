from __future__ import annotations

import csv
import json
from pathlib import Path


def validate_outputs(output_dir: Path) -> None:
    audit = read_json(output_dir / "mpp_pronostics_2026_16es_audit.json")
    predictions = audit["predictions"]
    advancement = audit["tournament"]["advancement"]
    champion_rows = read_csv(output_dir / "mpp_champion_simulation_2026.csv")

    if len(predictions) != 16:
        raise AssertionError(f"Expected 16 Round-of-32 predictions, got {len(predictions)}")
    if len(champion_rows) != 32:
        raise AssertionError(f"Expected 32 tournament teams, got {len(champion_rows)}")
    if "optional_odds" not in audit:
        raise AssertionError("Missing optional odds source audit")
    if "trained_ml" not in audit:
        raise AssertionError("Missing trained ML audit")

    expected_round_totals = {
        "reach_r16": 16.0,
        "reach_qf": 8.0,
        "reach_sf": 4.0,
        "reach_final": 2.0,
        "champion": 1.0,
    }
    for key, expected in expected_round_totals.items():
        actual = sum(team[key] for team in advancement.values())
        if abs(actual - expected) > 1e-9:
            raise AssertionError(f"{key}: expected {expected}, got {actual}")


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))
