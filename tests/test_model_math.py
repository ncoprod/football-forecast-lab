from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.model import outcome_probs, score_distribution
from football_forecast_lab.tournament import combine_slots


class ModelMathTest(unittest.TestCase):
    def test_score_distribution_normalizes(self) -> None:
        scores = score_distribution(1.4, 0.9, 10)
        self.assertAlmostEqual(sum(scores.values()), 1.0)
        outcomes = outcome_probs(scores)
        self.assertAlmostEqual(sum(outcomes.values()), 1.0)

    def test_combine_slots_normalizes(self) -> None:
        profiles = {
            "A": {"rating": 1900, "attack": 1.1, "defense": 1.0},
            "B": {"rating": 1700, "attack": 1.0, "defense": 1.0},
            "C": {"rating": 1800, "attack": 1.0, "defense": 1.0},
            "D": {"rating": 1600, "attack": 0.9, "defense": 0.95},
        }
        combined = combine_slots({"A": 0.7, "B": 0.3}, {"C": 0.6, "D": 0.4}, profiles)
        self.assertAlmostEqual(sum(combined.values()), 1.0)


if __name__ == "__main__":
    unittest.main()
