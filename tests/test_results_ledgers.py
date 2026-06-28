from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from football_forecast_lab.backtest import evaluate_ledger_predictions
from football_forecast_lab.ledger import append_resolved_results, load_resolved_results
from football_forecast_lab.results import completed_event_result_rows
from scripts.build_mpp_picks import build_mpp_rows


class ResultLedgerTest(unittest.TestCase):
    def test_completed_event_result_rows_extracts_final_scores(self) -> None:
        scoreboard = {
            "events": [
                {
                    "id": "760486",
                    "date": "2026-06-28T19:00Z",
                    "competitions": [
                        {
                            "status": {
                                "type": {
                                    "completed": True,
                                    "state": "post",
                                    "name": "STATUS_FULL_TIME",
                                    "detail": "FT",
                                }
                            },
                            "competitors": [
                                {
                                    "homeAway": "home",
                                    "score": "0",
                                    "winner": False,
                                    "team": {"id": "1", "displayName": "South Africa"},
                                },
                                {
                                    "homeAway": "away",
                                    "score": "1",
                                    "winner": True,
                                    "team": {"id": "2", "displayName": "Canada"},
                                },
                            ],
                        }
                    ],
                }
            ]
        }

        rows = completed_event_result_rows(scoreboard, "https://example.test", "2026-06-29T00:00:00+00:00")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event_id"], "760486")
        self.assertEqual(rows[0]["actual_home_score"], 0)
        self.assertEqual(rows[0]["actual_away_score"], 1)
        self.assertEqual(rows[0]["actual_result"], "away")
        self.assertEqual(rows[0]["actual_score_scope"], "espn_final_score")

    def test_append_resolved_results_skips_existing_event_ids(self) -> None:
        row = {
            "resolved_at_utc": "2026-06-29T00:00:00+00:00",
            "event_id": "a",
            "actual_home_score": 1,
            "actual_away_score": 0,
        }
        with tempfile.TemporaryDirectory() as tmp:
            ledger_dir = Path(tmp)
            first = append_resolved_results([row], ledger_dir)
            second = append_resolved_results([row], ledger_dir)

            self.assertEqual(first["appended_rows"], 1)
            self.assertEqual(second["appended_rows"], 0)
            self.assertEqual(load_resolved_results(ledger_dir / "resolved_results.jsonl")["a"]["actual_home_score"], 1)

    def test_backtest_joins_results_without_mutating_prediction_rows(self) -> None:
        rows = [
            {
                "generated_at_utc": "2026-06-28T18:00:00+00:00",
                "kickoff_utc": "2026-06-28T19:00:00+00:00",
                "forecast_status": "pre_match",
                "event_id": "a",
                "advancement_probabilities": {"home": 0.2, "draw": 0.1, "away": 0.7},
                "score_distribution_after_extra": [
                    {"score": "0-1", "probability": 0.2},
                    {"score": "1-1", "probability": 0.1},
                ],
                "recommended_result": "away",
            }
        ]
        results = {
            "a": {
                "actual_home_score": 0,
                "actual_away_score": 1,
                "actual_score_scope": "espn_final_score",
            }
        }

        report = evaluate_ledger_predictions(rows, results)

        self.assertEqual(report["resolved"], 1)
        self.assertEqual(report["metrics"]["final_accuracy"], 1.0)
        self.assertEqual(report["metrics"]["final_score_top1"], 1.0)
        self.assertNotIn("actual_home_score", rows[0])

    def test_mpp_rows_use_after_extra_score_as_single_pick(self) -> None:
        rows = build_mpp_rows(
            {
                "generated_at_utc": "2026-06-29T00:00:00+00:00",
                "predictions": [
                    {
                        "event_id": "a",
                        "match_utc": "2026-06-29T17:00:00+00:00",
                        "match": "Brazil - Japan",
                        "forecast_status": "pre_match",
                        "recommended_score_after_extra": "2-1",
                        "recommended_exact_probability_after_extra": 0.11,
                        "score_top3_mass_after_extra": 0.29,
                        "score_top5_mass_after_extra": 0.41,
                        "recommended_advancement_result": "Brazil gagne",
                        "recommended_advancement_probability": 0.62,
                        "recommended_score_90": "1-1",
                        "recommended_result": "Nul",
                        "no_bet_reason": "",
                        "stake_eur": 0.1,
                    }
                ],
            }
        )

        self.assertEqual(rows[0]["score_a_jouer"], "2-1")
        self.assertEqual(rows[0]["score_90_reference"], "1-1")
        self.assertEqual(rows[0]["decision"], "enter_mpp")


if __name__ == "__main__":
    unittest.main()
