# Rolling-Origin Backtest Report

This report only accepts clean pre-match ledger rows. Rows generated at or after kickoff are rejected.
Final scores are joined from a separate immutable results ledger; pre-match predictions are never edited.

Ledger: `C:\Users\nicoc\Documents\Codex\2026-06-28\je\outputs\ledger\pre_match_predictions.jsonl`
Results: `C:\Users\nicoc\Documents\Codex\2026-06-28\je\outputs\ledger\resolved_results.jsonl`
Rows: `142` across `15` events; resolved rows: `23` across `3` events; pending rows: `119` across `12` events.

## Ledger Metrics

Score scope: `espn_final_score_vs_after_extra_distribution`.

| Metric | Value |
|---|---:|
| closing_line_value | 0.0000 |
| final_accuracy | 0.2609 |
| final_brier_score | 0.9242 |
| final_log_loss | 1.5358 |
| final_score_log_loss | 2.7293 |
| final_score_top1 | 0.0000 |
| final_score_top3 | 0.2609 |
| final_score_top5 | 0.2609 |

## Historical ML Outcome Backtest

| Model | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| Softmax ML | 0.606 | 0.510 | 0.868 |
| Elo baseline | 0.605 | 0.542 | 0.926 |
| Majority baseline | 0.472 | 0.636 | 1.054 |

The historical ML layer still lacks historical bookmaker odds and player availability; it remains advisory.
