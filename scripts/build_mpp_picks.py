from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.settings import OUTPUT_DIR


DEFAULT_CSV = OUTPUT_DIR / "mpp_picks_current.csv"
DEFAULT_MD = OUTPUT_DIR / "mpp_picks_current.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build one clear MPP-style pick per match.")
    parser.add_argument("--audit", type=Path, default=OUTPUT_DIR / "match_predictions_2026_r32_audit.json")
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    rows = build_mpp_rows(audit)
    write_csv(args.csv_output, rows)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.write_text(build_markdown(audit, rows), encoding="utf-8")
    print(f"OK: wrote {args.csv_output} and {args.md_output} ({len(rows)} rows)")


def build_mpp_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for prediction in audit.get("predictions", []):
        status = prediction.get("forecast_status", "")
        no_bet_reason = prediction.get("no_bet_reason", "")
        decision = "enter_mpp" if status == "pre_match" else "skip_not_pre_match"
        rows.append(
            {
                "generated_at_utc": audit.get("generated_at_utc"),
                "event_id": prediction.get("event_id"),
                "kickoff_utc": prediction.get("match_utc"),
                "match": prediction.get("match"),
                "forecast_status": status,
                "decision": decision,
                "mpp_score_scope": "final_score_after_extra_before_penalties",
                "score_a_jouer": prediction.get("recommended_score_after_extra"),
                "score_a_jouer_probability": pct_value(prediction.get("recommended_exact_probability_after_extra")),
                "top3_score_mass": pct_value(prediction.get("score_top3_mass_after_extra")),
                "top5_score_mass": pct_value(prediction.get("score_top5_mass_after_extra")),
                "resultat_a_jouer": prediction.get("recommended_advancement_result"),
                "resultat_probability": pct_value(prediction.get("recommended_advancement_probability")),
                "score_90_reference": prediction.get("recommended_score_90"),
                "resultat_90_reference": prediction.get("recommended_result"),
                "no_bet_reason": no_bet_reason,
                "stake_eur": f"{float(prediction.get('stake_eur', 0.0) or 0.0):.2f}",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "generated_at_utc",
        "event_id",
        "kickoff_utc",
        "match",
        "forecast_status",
        "decision",
        "mpp_score_scope",
        "score_a_jouer",
        "score_a_jouer_probability",
        "top3_score_mass",
        "top5_score_mass",
        "resultat_a_jouer",
        "resultat_probability",
        "score_90_reference",
        "resultat_90_reference",
        "no_bet_reason",
        "stake_eur",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(audit: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# MPP Picks Current",
        "",
        f"Generated UTC: `{audit.get('generated_at_utc')}`",
        "",
        "One score is exposed as `score_a_jouer`: final score after possible extra time, before penalties.",
        "",
        "| Match | Status | Decision | Score a jouer | P(score) | Resultat | P(resultat) | No-bet reason |",
        "|---|---|---|---:|---:|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['match']} | {row['forecast_status']} | {row['decision']} | "
            f"{row['score_a_jouer']} | {row['score_a_jouer_probability']} | "
            f"{row['resultat_a_jouer']} | {row['resultat_probability']} | {row['no_bet_reason']} |"
        )
    lines.append("")
    return "\n".join(lines)


def pct_value(value: Any) -> str:
    if value is None:
        return ""
    return f"{100 * float(value):.1f}%"


if __name__ == "__main__":
    main()
