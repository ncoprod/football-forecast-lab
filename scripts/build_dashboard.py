from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.dashboard import build_dashboard


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    build_dashboard(
        REPO_ROOT / "outputs" / "match_predictions_2026_r32_audit.json",
        REPO_ROOT / "outputs" / "football_forecast_dashboard.html",
    )


if __name__ == "__main__":
    main()
