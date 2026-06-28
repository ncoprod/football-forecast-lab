from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.refresh_once import main as refresh_once


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh forecasts on a loop.")
    parser.add_argument("--minutes", type=float, default=30.0)
    args = parser.parse_args()

    while True:
        refresh_once()
        time.sleep(max(1.0, args.minutes * 60.0))


if __name__ == "__main__":
    main()
