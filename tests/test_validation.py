from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.validation import validate_outputs
from football_forecast_lab.settings import OUTPUT_DIR


class ValidationTest(unittest.TestCase):
    def test_generated_outputs_are_valid(self) -> None:
        validate_outputs(OUTPUT_DIR)


if __name__ == "__main__":
    unittest.main()
