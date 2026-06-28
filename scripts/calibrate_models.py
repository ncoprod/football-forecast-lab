from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.calibration import expected_calibration_error, is_monotone_calibration, reliability_bins
from football_forecast_lab.ledger import load_jsonl, validate_ledger_rows
from football_forecast_lab.settings import BACKTEST_DIR, LEDGER_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Build calibration report from resolved pre-match ledger rows.")
    parser.add_argument("--ledger", type=Path, default=LEDGER_DIR / "pre_match_predictions.jsonl")
    parser.add_argument("--output", type=Path, default=BACKTEST_DIR / "calibration_report.md")
    args = parser.parse_args()

    rows = load_jsonl(args.ledger)
    validate_ledger_rows(rows)
    resolved_rows = calibration_rows(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_report(resolved_rows), encoding="utf-8")
    print(f"OK: wrote {args.output}")


def calibration_rows(rows: list[dict]) -> list[dict]:
    output = []
    for row in rows:
        if row.get("actual_home_score") is None or row.get("actual_away_score") is None:
            continue
        actual = actual_outcome(row)
        probabilities = row.get("calibrated_probabilities") or row.get("probabilities") or {}
        for outcome in ("home", "draw", "away"):
            if outcome in probabilities:
                output.append(
                    {
                        "probability": float(probabilities[outcome]),
                        "actual": 1.0 if outcome == actual else 0.0,
                    }
                )
    return output


def actual_outcome(row: dict) -> str:
    home = int(row["actual_home_score"])
    away = int(row["actual_away_score"])
    if home > away:
        return "home"
    if home < away:
        return "away"
    return "draw"


def build_report(rows: list[dict]) -> str:
    lines = ["# Calibration Report", ""]
    if not rows:
        lines.extend(
            [
                "No resolved pre-match rows yet. Capture forecasts before kickoff and add final scores before trusting calibration.",
                "",
            ]
        )
        return "\n".join(lines)

    bins = reliability_bins(rows, "probability", "actual", bins=10)
    lines.extend(
        [
            f"Rows evaluated: `{len(rows)}`",
            f"Expected calibration error: `{expected_calibration_error(bins):.4f}`",
            f"Monotone observed rates: `{is_monotone_calibration(bins)}`",
            "",
            "| Bin | Count | Mean probability | Observed rate |",
            "|---:|---:|---:|---:|",
        ]
    )
    for bucket in bins:
        lines.append(
            f"| {bucket['bin']} | {bucket['count']} | "
            f"{bucket['mean_probability']:.3f} | {bucket['observed_rate']:.3f} |"
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
