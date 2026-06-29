from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.availability import build_availability_rows
from football_forecast_lab.settings import OUTPUT_DIR
from football_forecast_lab.utils import pct


DEFAULT_CSV = OUTPUT_DIR / "availability_report_current.csv"
DEFAULT_MD = OUTPUT_DIR / "availability_report_current.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build player availability and lineup coverage report.")
    parser.add_argument("--audit", type=Path, default=OUTPUT_DIR / "match_predictions_2026_r32_audit.json")
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    rows = build_availability_rows(audit)
    write_csv(args.csv_output, rows)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.write_text(build_markdown(audit, rows), encoding="utf-8")
    print(f"OK: wrote {args.csv_output} and {args.md_output} ({len(rows)} rows)")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "generated_at_utc",
        "event_id",
        "kickoff_utc",
        "match",
        "forecast_status",
        "home_roster_count",
        "away_roster_count",
        "api_football_fixture_id",
        "api_injury_count",
        "api_lineup_count",
        "api_player_stats_count",
        "risk_news_count",
        "risk_news_terms",
        "availability_status",
        "confidence_penalty",
        "manual_check_required",
        "notes",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(audit: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Availability Report Current",
        "",
        f"Generated UTC: `{audit.get('generated_at_utc')}`",
        "",
        "This report is a coverage audit, not a medical claim. Missing lineups lower confidence and trigger manual checks.",
        "",
        "| Match | Status | Rosters | API lineups | Risk news | Penalty | Action |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        action = "manual lineup check" if row["manual_check_required"] else "ok/no action"
        lines.append(
            f"| {row['match']} | {row['availability_status']} | "
            f"{row.get('home_roster_count') or 0}/{row.get('away_roster_count') or 0} | "
            f"{row['api_lineup_count']} | {row['risk_news_count']} | "
            f"{pct(row['confidence_penalty'])} | {action} |"
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
