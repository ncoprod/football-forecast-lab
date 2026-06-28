from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.http_client import fetch_json
from football_forecast_lab.ledger import append_resolved_results
from football_forecast_lab.results import completed_event_result_rows
from football_forecast_lab.settings import LEDGER_DIR, R32_SCOREBOARD_URL


def main() -> None:
    parser = argparse.ArgumentParser(description="Append completed match results to the immutable results ledger.")
    parser.add_argument("--scoreboard-url", default=R32_SCOREBOARD_URL)
    parser.add_argument("--cache-name", default="espn_r32_scoreboard.json")
    parser.add_argument("--ledger-dir", type=Path, default=LEDGER_DIR)
    args = parser.parse_args()

    scoreboard = fetch_json(args.scoreboard_url, args.cache_name)
    rows = completed_event_result_rows(scoreboard, args.scoreboard_url)
    summary = append_resolved_results(rows, args.ledger_dir)
    print(
        "OK: resolved results "
        f"input={summary['input_rows']} appended={summary['appended_rows']} "
        f"skipped_existing={summary['skipped_existing']}"
    )


if __name__ == "__main__":
    main()
