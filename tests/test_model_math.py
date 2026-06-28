from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.http_client import redact_url
from football_forecast_lab.model import merge_external_odds, outcome_probs, score_distribution
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

    def test_redact_url_hides_api_keys(self) -> None:
        redacted = redact_url("https://example.test/odds?apiKey=secret-value&regions=eu")
        self.assertNotIn("secret-value", redacted)
        self.assertIn("apiKey=REDACTED", redacted)

    def test_external_odds_blend_normalizes(self) -> None:
        odds = {
            "provider": "DraftKings",
            "details": "HOME +120",
            "moneyline_fair": {"home": 0.45, "draw": 0.25, "away": 0.30},
            "total_line": 2.5,
            "over_fair": 0.48,
        }
        external = {
            "h2h_fair": {"France": 0.55, "Draw": 0.22, "Sweden": 0.23},
            "totals_fair": {"line": 2.5, "over": 0.51, "under": 0.49, "sample_count": 8},
        }

        merged = merge_external_odds(odds, external, "France", "Sweden")

        self.assertIn("The Odds API", merged["provider"])
        self.assertAlmostEqual(sum(merged["moneyline_fair"].values()), 1.0)
        self.assertGreater(merged["moneyline_fair"]["home"], odds["moneyline_fair"]["home"])
        self.assertGreater(merged["over_fair"], odds["over_fair"])

    def test_external_odds_blend_uses_team_aliases(self) -> None:
        odds = {"moneyline_fair": {"home": 0.40, "draw": 0.28, "away": 0.32}}
        external = {"h2h_fair": {"Cote d'Ivoire": 0.48, "Draw": 0.25, "Norway": 0.27}}

        merged = merge_external_odds(odds, external, "Ivory Coast", "Norway")

        self.assertIn("external_h2h_fair", merged)
        self.assertGreater(merged["moneyline_fair"]["home"], odds["moneyline_fair"]["home"])


if __name__ == "__main__":
    unittest.main()
