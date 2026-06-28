from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.metrics import accuracy, brier_score, log_loss, score_top_k


class MetricsTest(unittest.TestCase):
    def test_outcome_metrics(self) -> None:
        probs = {"home": 0.7, "draw": 0.2, "away": 0.1}
        self.assertEqual(accuracy(probs, "home"), 1.0)
        self.assertLess(log_loss(probs, "home"), log_loss(probs, "away"))
        self.assertAlmostEqual(brier_score(probs, "home"), 0.14)

    def test_score_top_k(self) -> None:
        scores = [{"score": "1-0"}, {"score": "2-0"}, {"score": "1-1"}]
        self.assertEqual(score_top_k(scores, "2-0", k=2), 1.0)
        self.assertEqual(score_top_k(scores, "0-2", k=3), 0.0)


if __name__ == "__main__":
    unittest.main()
