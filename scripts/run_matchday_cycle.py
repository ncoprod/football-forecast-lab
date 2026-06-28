from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    for script_name in (
        "refresh_once.py",
        "resolve_results.py",
        "backtest_models.py",
        "calibrate_models.py",
        "paper_bet.py",
        "build_mpp_picks.py",
        "build_readme_assets.py",
        "validate_outputs.py",
    ):
        script = REPO_ROOT / "scripts" / script_name
        print(f"==> {script_name}", flush=True)
        subprocess.run([sys.executable, str(script)], cwd=REPO_ROOT, check=True)


if __name__ == "__main__":
    main()
