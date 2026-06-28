from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.validation import validate_outputs

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs"


def main() -> None:
    validate_outputs(OUTPUT_DIR)
    print("OK: outputs are structurally valid.")


if __name__ == "__main__":
    main()
