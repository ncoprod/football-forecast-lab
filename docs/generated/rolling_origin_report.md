# Rolling-Origin Backtest Report

This report only accepts clean pre-match ledger rows. Rows generated at or after kickoff are rejected.

Ledger: `C:\Users\nicoc\Documents\Codex\2026-06-28\je\outputs\ledger\pre_match_predictions.jsonl`
Rows: `30`; resolved: `0`; pending: `30`.

## Ledger Metrics

No resolved pre-match ledger rows yet. Keep capturing snapshots before kickoff, then add final scores to evaluate them.

## Historical ML Outcome Backtest

| Model | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| Softmax ML | 0.606 | 0.510 | 0.868 |
| Elo baseline | 0.605 | 0.542 | 0.926 |
| Majority baseline | 0.472 | 0.636 | 1.054 |

The historical ML layer still lacks historical bookmaker odds and player availability; it remains advisory.
