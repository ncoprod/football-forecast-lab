from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.ml_models import run_model_grid, write_model_artifact
from football_forecast_lab.settings import OUTPUT_DIR
from football_forecast_lab.training_data import (
    build_examples,
    fetch_historical_results,
    load_historical_results,
    write_training_snapshot,
)


def main() -> None:
    raw_path = fetch_historical_results()
    rows = load_historical_results(raw_path)
    examples = build_examples(rows, start_year=2000)
    snapshot_path = write_training_snapshot(examples)
    result = run_model_grid(examples)
    result["training_snapshot"] = str(snapshot_path)
    write_model_artifact(OUTPUT_DIR / "ml_training_result.json", result)
    write_model_artifact(Path("models") / "international_softmax_v1.json", result["final_model"])
    (OUTPUT_DIR / "ml_training_report.md").write_text(build_report(result), encoding="utf-8")


def build_report(result: dict) -> str:
    lines = [
        "# ML Training Report",
        "",
        f"Source: `{result['source']}`",
        "",
        "## Rows",
        "",
        "| Split | Rows |",
        "|---|---:|",
    ]
    for split, count in result["row_counts"].items():
        lines.append(f"| {split} | {count} |")
    lines.extend(
        [
            "",
            "## Best Validation Model",
            "",
            "```json",
            json.dumps(result["best_validation"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Test Metrics",
            "",
            "```json",
            json.dumps(result["test_metrics"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Test Baselines",
            "",
            "```json",
            json.dumps(result["test_baselines"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Validation Leaderboard",
            "",
            "| Rank | Model | Features | Log loss | Brier | Accuracy |",
            "|---:|---|---|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(result["leaderboard"][:15], start=1):
        metrics = row["validation"]
        lines.append(
            f"| {index} | {row['model']} | {row['feature_set']} | "
            f"{metrics['log_loss']:.4f} | {metrics['brier_score']:.4f} | {metrics['accuracy']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a first trained model using historical international results and pre-match chronological features. It does not include historical bookmaker odds yet, so it should be treated as an ML layer to compare against market-calibrated live models, not as a replacement for market odds.",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
