from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.dashboard import build_dashboard
from football_forecast_lab.ledger import append_pre_match_snapshots
from football_forecast_lab.pipeline import main as run_pipeline
from football_forecast_lab.validation import validate_outputs


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    run_pipeline()
    output_dir = REPO_ROOT / "outputs"
    validate_outputs(output_dir)
    build_dashboard(
        output_dir / "match_predictions_2026_r32_audit.json",
        output_dir / "football_forecast_dashboard.html",
    )
    append_pre_match_snapshots(
        json.loads((output_dir / "match_predictions_2026_r32_audit.json").read_text(encoding="utf-8")),
        output_dir / "ledger",
    )


if __name__ == "__main__":
    main()
