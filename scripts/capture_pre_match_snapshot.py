from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.ledger import append_pre_match_snapshots


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Append clean pre-match forecasts to immutable ledgers.")
    parser.add_argument(
        "--audit",
        type=Path,
        default=REPO_ROOT / "outputs" / "match_predictions_2026_r32_audit.json",
    )
    parser.add_argument("--ledger-dir", type=Path, default=REPO_ROOT / "outputs" / "ledger")
    args = parser.parse_args()

    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    result = append_pre_match_snapshots(audit, args.ledger_dir)
    print(
        "OK: appended "
        f"{result['prediction_rows']} pre-match prediction rows and "
        f"{result['odds_rows']} odds rows."
    )


if __name__ == "__main__":
    main()
