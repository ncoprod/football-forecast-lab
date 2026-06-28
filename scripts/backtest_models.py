from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.backtest import evaluate_ledger_predictions
from football_forecast_lab.ledger import load_jsonl, load_resolved_results
from football_forecast_lab.settings import BACKTEST_DIR, LEDGER_DIR


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build leakage-safe rolling-origin backtest report.")
    parser.add_argument("--ledger", type=Path, default=LEDGER_DIR / "pre_match_predictions.jsonl")
    parser.add_argument("--results", type=Path, default=LEDGER_DIR / "resolved_results.jsonl")
    parser.add_argument("--ml-result", type=Path, default=REPO_ROOT / "outputs" / "ml_training_result.json")
    parser.add_argument("--output", type=Path, default=BACKTEST_DIR / "rolling_origin_report.md")
    args = parser.parse_args()

    rows = load_jsonl(args.ledger)
    resolved_results = load_resolved_results(args.results)
    ledger_result = evaluate_ledger_predictions(rows, resolved_results)
    ml_result = json.loads(args.ml_result.read_text(encoding="utf-8")) if args.ml_result.exists() else {}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_report(ledger_result, ml_result, args.ledger, args.results), encoding="utf-8")
    print(f"OK: wrote {args.output}")


def build_report(ledger_result: dict, ml_result: dict, ledger_path: Path, results_path: Path) -> str:
    lines = [
        "# Rolling-Origin Backtest Report",
        "",
        "This report only accepts clean pre-match ledger rows. Rows generated at or after kickoff are rejected.",
        "Final scores are joined from a separate immutable results ledger; pre-match predictions are never edited.",
        "",
        f"Ledger: `{ledger_path}`",
        f"Results: `{results_path}`",
        (
            f"Rows: `{ledger_result.get('rows', 0)}` across `{ledger_result.get('unique_events', 0)}` events; "
            f"resolved rows: `{ledger_result.get('resolved', 0)}` across `{ledger_result.get('resolved_events', 0)}` events; "
            f"pending rows: `{ledger_result.get('pending', 0)}` across `{ledger_result.get('pending_events', 0)}` events."
        ),
        "",
    ]
    metrics = ledger_result.get("metrics", {})
    if metrics:
        lines.extend(
            [
                "## Ledger Metrics",
                "",
                f"Score scope: `{ledger_result.get('score_scope', 'unknown')}`.",
                "",
                "| Metric | Value |",
                "|---|---:|",
            ]
        )
        for key, value in sorted(metrics.items()):
            lines.append(f"| {key} | {value:.4f} |")
        lines.append("")
    else:
        lines.extend(
            [
                "## Ledger Metrics",
                "",
                "No resolved pre-match ledger rows yet. Keep capturing snapshots before kickoff, then resolve final scores after full time.",
                "",
            ]
        )

    if ml_result:
        test = ml_result.get("test_metrics", {})
        baselines = ml_result.get("test_baselines", {})
        lines.extend(
            [
                "## Historical ML Outcome Backtest",
                "",
                "| Model | Accuracy | Brier | Log loss |",
                "|---|---:|---:|---:|",
                metric_row("Softmax ML", test),
                metric_row("Elo baseline", baselines.get("elo_baseline", {})),
                metric_row("Majority baseline", baselines.get("majority", {})),
                "",
                "The historical ML layer still lacks historical bookmaker odds and player availability; it remains advisory.",
                "",
            ]
        )
    return "\n".join(lines)


def metric_row(label: str, metrics: dict) -> str:
    return (
        f"| {label} | {float(metrics.get('accuracy', 0.0)):.3f} | "
        f"{float(metrics.get('brier_score', 0.0)):.3f} | "
        f"{float(metrics.get('log_loss', 0.0)):.3f} |"
    )


if __name__ == "__main__":
    main()
