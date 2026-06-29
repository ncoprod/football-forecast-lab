# Rolling-Origin Backtest Report

This report only accepts clean pre-match ledger rows. Rows generated at or after kickoff are rejected.
Final scores are joined from a separate immutable results ledger; pre-match predictions are never edited.

Ledger: `C:\Users\nicoc\Documents\Codex\2026-06-28\je\outputs\ledger\pre_match_predictions.jsonl`
Results: `C:\Users\nicoc\Documents\Codex\2026-06-28\je\outputs\ledger\resolved_results.jsonl`
Rows: `118` across `15` events; resolved rows: `0` across `0` events; pending rows: `118` across `15` events.

## Ledger Metrics

No resolved pre-match ledger rows yet. Keep capturing snapshots before kickoff, then resolve final scores after full time.

## Historical ML Outcome Backtest

| Model | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| Softmax ML | 0.606 | 0.510 | 0.868 |
| Elo baseline | 0.605 | 0.542 | 0.926 |
| Majority baseline | 0.472 | 0.636 | 1.054 |

The historical ML layer still lacks historical bookmaker odds and player availability; it remains advisory.
