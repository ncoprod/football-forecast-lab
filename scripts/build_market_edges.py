from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.availability import build_availability_rows
from football_forecast_lab.backtest import evaluate_ledger_predictions
from football_forecast_lab.ledger import load_jsonl, load_resolved_results
from football_forecast_lab.settings import LEDGER_DIR, OUTPUT_DIR
from football_forecast_lab.strategy import build_market_edge_rows
from football_forecast_lab.utils import pct


DEFAULT_CSV = OUTPUT_DIR / "market_edges_current.csv"
DEFAULT_MD = OUTPUT_DIR / "market_edges_current.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build disciplined market-edge candidates.")
    parser.add_argument("--audit", type=Path, default=OUTPUT_DIR / "match_predictions_2026_r32_audit.json")
    parser.add_argument("--pre-match-ledger", type=Path, default=LEDGER_DIR / "pre_match_predictions.jsonl")
    parser.add_argument("--results-ledger", type=Path, default=LEDGER_DIR / "resolved_results.jsonl")
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    availability_rows = build_availability_rows(audit)
    live_result = evaluate_ledger_predictions(
        load_jsonl(args.pre_match_ledger),
        load_resolved_results(args.results_ledger),
    )
    rows = build_market_edge_rows(audit, availability_rows, int(live_result.get("resolved", 0)))
    write_csv(args.csv_output, rows)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.write_text(build_markdown(audit, rows, live_result), encoding="utf-8")
    print(f"OK: wrote {args.csv_output} and {args.md_output} ({len(rows)} rows)")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "generated_at_utc",
        "event_id",
        "kickoff_utc",
        "match",
        "forecast_status",
        "market",
        "selection",
        "selection_key",
        "model_probability",
        "market_probability",
        "edge",
        "availability_status",
        "availability_penalty",
        "live_resolved_rows",
        "calibration_gate",
        "decision",
        "rank_score",
        "paper_stake_eur",
        "real_stake_eur",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(audit: dict[str, Any], rows: list[dict[str, Any]], live_result: dict[str, Any]) -> str:
    lines = [
        "# Market Edges Current",
        "",
        f"Generated UTC: `{audit.get('generated_at_utc')}`",
        f"Live clean resolved rows: `{live_result.get('resolved', 0)}`.",
        "",
        "Real staking remains locked until enough clean live rows exist. Use this report for paper tracking and MPP judgment.",
        "",
        "| Match | Market | Selection | Model | Market | Edge | Decision | Paper stake |",
        "|---|---|---|---:|---:|---:|---|---:|",
    ]
    for row in visible_rows(rows):
        lines.append(
            f"| {row['match']} | {row['market']} | {row['selection']} | "
            f"{pct(row.get('model_probability'))} | {pct(row.get('market_probability'))} | "
            f"{signed_pct(row.get('edge'))} | {row['decision']} | {float(row.get('paper_stake_eur') or 0.0):.2f} |"
        )
    lines.append("")
    return "\n".join(lines)


def visible_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [row for row in rows if row["decision"].startswith("paper_candidate")]
    if not candidates:
        candidates = [row for row in rows if row["decision"].startswith("watch_only")]
    return sorted(candidates, key=lambda row: row.get("rank_score") or -1.0, reverse=True)[:20]


def signed_pct(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{100 * float(value):+.1f} pts"


if __name__ == "__main__":
    main()
