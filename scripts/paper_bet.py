from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.settings import OUTPUT_DIR, PAPER_BETS_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Write conservative paper-betting recommendations.")
    parser.add_argument("--audit", type=Path, default=OUTPUT_DIR / "match_predictions_2026_r32_audit.json")
    parser.add_argument("--output", type=Path, default=PAPER_BETS_DIR / "current_ledger.csv")
    parser.add_argument("--bankroll-eur", type=float, default=3.0)
    parser.add_argument("--max-stake-eur", type=float, default=0.10)
    parser.add_argument("--daily-limit-eur", type=float, default=0.30)
    args = parser.parse_args()

    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    rows = build_paper_rows(audit, args.bankroll_eur, args.max_stake_eur, args.daily_limit_eur)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_rows(args.output, rows)
    print(f"OK: wrote {args.output} ({len(rows)} rows)")


def build_paper_rows(audit: dict, bankroll: float, max_stake: float, daily_limit: float) -> list[dict]:
    rows = []
    spent = 0.0
    for prediction in audit.get("predictions", []):
        stake = min(float(prediction.get("stake_eur", 0.0)), max_stake, bankroll - spent, daily_limit - spent)
        if stake < 0:
            stake = 0.0
        reason = prediction.get("no_bet_reason", "")
        if reason:
            stake = 0.0
        spent += stake
        rows.append(
            {
                "generated_at_utc": audit.get("generated_at_utc"),
                "event_id": prediction.get("event_id"),
                "match": prediction.get("match"),
                "forecast_status": prediction.get("forecast_status"),
                "market": "1X2_90",
                "selection": prediction.get("recommended_result_key"),
                "model_probability": prediction.get("recommended_result_probability"),
                "stake_eur": f"{stake:.2f}",
                "bankroll_eur": f"{bankroll:.2f}",
                "mode": "paper_only",
                "no_bet_reason": reason,
            }
        )
    return rows


def write_rows(path: Path, rows: list[dict]) -> None:
    fieldnames = [
        "generated_at_utc",
        "event_id",
        "match",
        "forecast_status",
        "market",
        "selection",
        "model_probability",
        "stake_eur",
        "bankroll_eur",
        "mode",
        "no_bet_reason",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
