from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.ledger import ODDS_JSONL, load_jsonl
from football_forecast_lab.odds_movement import build_odds_movement_rows
from football_forecast_lab.settings import LEDGER_DIR, OUTPUT_DIR
from football_forecast_lab.utils import pct


DEFAULT_CSV = OUTPUT_DIR / "odds_movement_current.csv"
DEFAULT_MD = OUTPUT_DIR / "odds_movement_current.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze pre-match odds movement from the odds ledger.")
    parser.add_argument("--ledger", type=Path, default=LEDGER_DIR / ODDS_JSONL)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    rows = build_odds_movement_rows(load_jsonl(args.ledger))
    write_csv(args.csv_output, rows)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.write_text(build_markdown(rows, args.ledger), encoding="utf-8")
    print(f"OK: wrote {args.csv_output} and {args.md_output} ({len(rows)} rows)")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "event_id",
        "match",
        "kickoff_utc",
        "snapshots",
        "first_generated_at_utc",
        "latest_generated_at_utc",
        "minutes_to_kickoff_latest",
        "p_home_first",
        "p_home_latest",
        "p_home_move",
        "p_draw_first",
        "p_draw_latest",
        "p_draw_move",
        "p_away_first",
        "p_away_latest",
        "p_away_move",
        "strongest_h2h_move",
        "strongest_h2h_move_points",
        "total_line_first",
        "total_line_latest",
        "p_over_first",
        "p_over_latest",
        "p_over_move",
        "latest_bookmaker_count",
        "latest_provider",
        "quota_remaining",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(rows: list[dict[str, Any]], ledger_path: Path) -> str:
    lines = [
        "# Odds Movement Current",
        "",
        f"Ledger: `{ledger_path}`",
        "",
        "Only clean pre-match odds snapshots are analyzed. Movement is latest probability minus first probability.",
        "",
    ]
    if not rows:
        lines.extend(["No odds snapshots available yet.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Match | Snapshots | Latest T-kickoff | Strongest H2H move | Home | Draw | Away | Over move |",
            "|---|---:|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in sorted(rows, key=lambda item: abs(item.get("strongest_h2h_move_points") or 0.0), reverse=True):
        lines.append(
            f"| {row['match']} | {row['snapshots']} | {minutes(row.get('minutes_to_kickoff_latest'))} | "
            f"{row.get('strongest_h2h_move') or ''} {signed_pct(row.get('strongest_h2h_move_points'))} | "
            f"{pct(row.get('p_home_latest'))} | {pct(row.get('p_draw_latest'))} | "
            f"{pct(row.get('p_away_latest'))} | {signed_pct(row.get('p_over_move'))} |"
        )
    lines.append("")
    return "\n".join(lines)


def signed_pct(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{100 * float(value):+.1f} pts"


def minutes(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.0f} min"


if __name__ == "__main__":
    main()
