from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.refresh_once import main as refresh_once


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh forecasts on a loop.")
    parser.add_argument("--minutes", type=float, default=30.0)
    parser.add_argument("--min-odds-credits", type=int, default=25)
    args = parser.parse_args()

    while True:
        refresh_once()
        remaining = read_the_odds_remaining_credits()
        if remaining is not None and remaining <= args.min_odds_credits:
            print(
                "Stopping refresh loop: The Odds API remaining credits "
                f"({remaining}) <= threshold ({args.min_odds_credits})."
            )
            break
        time.sleep(max(1.0, args.minutes * 60.0))


def read_the_odds_remaining_credits() -> int | None:
    audit_path = Path(__file__).resolve().parents[1] / "outputs" / "match_predictions_2026_r32_audit.json"
    if not audit_path.exists():
        return None
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    quota = (
        audit.get("optional_odds", {})
        .get("sources", {})
        .get("the_odds_api", {})
        .get("quota", {})
    )
    remaining = quota.get("requests_remaining")
    if isinstance(remaining, int) and remaining >= 0:
        return remaining
    return None


if __name__ == "__main__":
    main()
