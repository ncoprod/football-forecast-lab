from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.dashboard import build_dashboard
from football_forecast_lab.pipeline import main as run_pipeline
from football_forecast_lab.validation import validate_outputs


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    run_pipeline()
    validate_outputs(REPO_ROOT / "outputs")
    build_dashboard(
        REPO_ROOT / "outputs" / "mpp_pronostics_2026_16es_audit.json",
        REPO_ROOT / "outputs" / "football_forecast_dashboard.html",
    )


if __name__ == "__main__":
    main()
