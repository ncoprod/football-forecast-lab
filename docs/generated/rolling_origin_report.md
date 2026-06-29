# Rolling-Origin Backtest Report

This report only accepts clean pre-match ledger rows. Rows generated at or after kickoff are rejected.
Final scores are joined from a separate immutable results ledger; pre-match predictions are never edited.

Ledger: `C:\Users\nicoc\Documents\Codex\2026-06-28\je\outputs\ledger\pre_match_predictions.jsonl`
Results: `C:\Users\nicoc\Documents\Codex\2026-06-28\je\outputs\ledger\resolved_results.jsonl`
Rows: `131` across `15` events; resolved rows: `6` across `1` events; pending rows: `125` across `14` events.

## Ledger Metrics

Score scope: `espn_final_score_vs_after_extra_distribution`.

| Metric | Value |
|---|---:|
| closing_line_value | 0.0000 |
| final_accuracy | 1.0000 |
| final_brier_score | 0.2410 |
| final_log_loss | 0.5057 |
| final_score_log_loss | 2.0999 |
| final_score_top1 | 0.0000 |
| final_score_top3 | 1.0000 |
| final_score_top5 | 1.0000 |

## Historical ML Outcome Backtest

| Model | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| Softmax ML | 0.606 | 0.510 | 0.868 |
| Elo baseline | 0.605 | 0.542 | 0.926 |
| Majority baseline | 0.472 | 0.636 | 1.054 |

The historical ML layer still lacks historical bookmaker odds and player availability; it remains advisory.
