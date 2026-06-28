from __future__ import annotations

import math
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.http_client import redact_url
from football_forecast_lab.calibration import expected_calibration_error, is_monotone_calibration
from football_forecast_lab.ledger import pre_match_prediction_rows, validate_ledger_rows
from football_forecast_lab.metrics import score_log_loss
from football_forecast_lab.model import dixon_coles_score_distribution, merge_external_odds, outcome_probs, score_distribution
from football_forecast_lab.tournament import combine_slots


class ModelMathTest(unittest.TestCase):
    def test_score_distribution_normalizes(self) -> None:
        scores = score_distribution(1.4, 0.9, 10)
        self.assertAlmostEqual(sum(scores.values()), 1.0)
        outcomes = outcome_probs(scores)
        self.assertAlmostEqual(sum(outcomes.values()), 1.0)

    def test_dixon_coles_distribution_normalizes(self) -> None:
        scores = dixon_coles_score_distribution(1.4, 0.9, max_goals=10)
        self.assertAlmostEqual(sum(scores.values()), 1.0)
        outcomes = outcome_probs(scores)
        self.assertAlmostEqual(sum(outcomes.values()), 1.0)
        self.assertGreater(scores[(0, 0)], 0.0)

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

    def test_ledger_filters_post_kickoff_rows(self) -> None:
        audit = {
            "generated_at_utc": "2026-06-28T20:00:00+00:00",
            "predictions": [
                {
                    "event_id": "future",
                    "match_utc": "2026-06-28T21:00:00+00:00",
                    "forecast_status": "pre_match",
                    "model_version": "test",
                    "home": {"name": "A"},
                    "away": {"name": "B"},
                    "odds": {},
                    "regular_outcomes": {"home": 0.4, "draw": 0.3, "away": 0.3},
                    "calibrated_probabilities": {"home": 0.4, "draw": 0.3, "away": 0.3},
                    "score_distribution_90": [{"score": "1-0", "probability": 1.0}],
                    "score_distribution_after_extra": [{"score": "1-0", "probability": 1.0}],
                    "top_scores_90": [],
                    "top_scores_after_extra": [],
                    "recommended_result_key": "home",
                    "recommended_score_90": "1-0",
                    "recommended_score_after_extra": "1-0",
                    "no_bet_reason": "",
                    "stake_eur": 0.1,
                },
                {
                    "event_id": "past",
                    "match_utc": "2026-06-28T19:00:00+00:00",
                    "forecast_status": "after_kickoff_or_unknown",
                },
            ],
        }
        rows = pre_match_prediction_rows(audit)
        self.assertEqual([row["event_id"] for row in rows], ["future"])
        validate_ledger_rows(rows)

    def test_score_log_loss_uses_exact_score_probability(self) -> None:
        scores = [{"score": "1-0", "probability": 0.2}, {"score": "0-0", "probability": 0.1}]
        self.assertAlmostEqual(score_log_loss(scores, "1-0"), -math.log(0.2))

    def test_calibration_helpers_are_bounded(self) -> None:
        bins = [
            {"bin": 0, "count": 2, "mean_probability": 0.2, "observed_rate": 0.0},
            {"bin": 1, "count": 2, "mean_probability": 0.7, "observed_rate": 1.0},
        ]
        self.assertGreaterEqual(expected_calibration_error(bins), 0.0)
        self.assertTrue(is_monotone_calibration(bins))


if __name__ == "__main__":
    unittest.main()
