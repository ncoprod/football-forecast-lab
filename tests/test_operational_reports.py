from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from football_forecast_lab.availability import availability_status, build_availability_rows
from football_forecast_lab.odds_movement import build_odds_movement_rows
from football_forecast_lab.strategy import build_market_edge_rows, score_distribution_over_probability


class OperationalReportsTest(unittest.TestCase):
    def test_odds_movement_tracks_first_to_latest_probability(self) -> None:
        rows = build_odds_movement_rows(
            [
                {
                    "event_id": "a",
                    "home": "A",
                    "away": "B",
                    "generated_at_utc": "2026-06-29T10:00:00+00:00",
                    "kickoff_utc": "2026-06-29T20:00:00+00:00",
                    "market": {"moneyline_fair": {"home": 0.50, "draw": 0.25, "away": 0.25}},
                },
                {
                    "event_id": "a",
                    "home": "A",
                    "away": "B",
                    "generated_at_utc": "2026-06-29T18:00:00+00:00",
                    "kickoff_utc": "2026-06-29T20:00:00+00:00",
                    "market": {"moneyline_fair": {"home": 0.56, "draw": 0.23, "away": 0.21}},
                },
            ]
        )

        self.assertEqual(rows[0]["snapshots"], 2)
        self.assertAlmostEqual(rows[0]["p_home_move"], 0.06)
        self.assertEqual(rows[0]["strongest_h2h_move"], "home")

    def test_availability_status_prefers_confirmed_lineups(self) -> None:
        self.assertEqual(availability_status({"home": 0, "away": 0}, 2, []), "api_lineups_available")
        self.assertEqual(availability_status({"home": 25, "away": 25}, 0, []), "espn_rosters_available")
        self.assertEqual(availability_status({"home": 0, "away": 0}, 0, [{"risk_terms": "injury"}]), "news_risk_only")

    def test_availability_rows_mark_manual_check_when_lineups_missing(self) -> None:
        audit = {
            "generated_at_utc": "2026-06-29T10:00:00+00:00",
            "predictions": [
                {
                    "event_id": "x",
                    "match_utc": "2026-06-29T20:00:00+00:00",
                    "match": "A - B",
                    "forecast_status": "pre_match",
                    "home": {"name": "A"},
                    "away": {"name": "B"},
                    "api_football": {},
                    "news_notes": [],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            rows = build_availability_rows(audit, Path(tmp))

        self.assertEqual(rows[0]["availability_status"], "missing_structured_player_data")
        self.assertTrue(rows[0]["manual_check_required"])

    def test_strategy_locks_real_stakes_until_live_calibration_exists(self) -> None:
        audit = {
            "generated_at_utc": "2026-06-29T10:00:00+00:00",
            "predictions": [
                {
                    "event_id": "a",
                    "match_utc": "2026-06-29T20:00:00+00:00",
                    "match": "A - B",
                    "forecast_status": "pre_match",
                    "home": {"name": "A"},
                    "away": {"name": "B"},
                    "calibrated_probabilities": {"home": 0.62, "draw": 0.22, "away": 0.16},
                    "odds": {
                        "moneyline_fair": {"home": 0.55, "draw": 0.25, "away": 0.20},
                        "total_line": 2.5,
                        "over_fair": 0.50,
                    },
                    "score_distribution_90": [{"home_goals": 2, "away_goals": 1, "score": "2-1", "probability": 1.0}],
                }
            ],
        }
        availability = [{"event_id": "a", "availability_status": "espn_rosters_available", "confidence_penalty": 0.02}]

        rows = build_market_edge_rows(audit, availability, live_resolved_rows=0)
        home = next(row for row in rows if row["market"] == "1X2_90" and row["selection_key"] == "home")

        self.assertEqual(home["decision"], "paper_candidate_needs_live_calibration")
        self.assertEqual(home["real_stake_eur"], 0.0)
        self.assertEqual(home["paper_stake_eur"], 0.10)

    def test_score_distribution_over_probability_uses_total_line(self) -> None:
        scores = [
            {"home_goals": 1, "away_goals": 1, "probability": 0.4},
            {"home_goals": 2, "away_goals": 1, "probability": 0.6},
        ]
        self.assertAlmostEqual(score_distribution_over_probability(scores, 2.5), 0.6)


if __name__ == "__main__":
    unittest.main()
