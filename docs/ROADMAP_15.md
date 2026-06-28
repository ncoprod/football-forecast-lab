# Fifteen-Step Implementation Map

## 1. Baseline

Implemented: ESPN/DraftKings + Elo + form + Poisson + bracket.

## 2. Metrics

Implemented: log loss, Brier score, accuracy and score top-k helpers in `metrics.py`.

## 3. Multi-book odds

Implemented: optional The Odds API connector via `THE_ODDS_API_KEY`, quota headers, h2h/totals normalization and live blending with ESPN/DraftKings.

Blocked without user-owned keys: live external odds calls.

## 4. Historical dataset

Implemented: CSV loader contract in `history.py`.

Blocked: no complete historical odds/player dataset bundled yet.

## 5. Feature store

Implemented: `outputs/feature_store_current_matches.csv`.

## 6. Backtest

Implemented: leakage-safe ledger evaluator in `backtest.py` and `scripts/backtest_models.py`.

Blocked for live metrics: needs resolved ledger rows with pre-match probabilities and final scores.

## 7. Better score model

Implemented: Dixon-Coles-adjusted 90-minute score distribution plus separate after-extra-time distribution.

Next: fit Dixon-Coles parameters from richer historical odds/score data instead of using a conservative global default.

## 8. Trained ML

Implemented: first softmax regression model trained on historical international results since 2000.

Current test performance from latest run:

- softmax log loss: 0.8683
- softmax Brier: 0.5103
- softmax accuracy: 0.6060
- Elo baseline log loss: 0.9263
- majority baseline log loss: 1.0537

Next: add historical odds and train LightGBM/scikit-learn models through the optional `.[ml]` dependency set.

## 9. Calibration

Implemented: reliability-bin, ECE, monotonicity and market-shrink helpers in `calibration.py`; `scripts/calibrate_models.py` writes the current report.

## 10. Ensemble

Implemented: weighted probability blending in `ensemble.py`.

## 11. Score/result recommendation

Implemented: the recommended result is the most likely 90-minute 1/N/2 outcome; the recommended exact score is the highest-probability 90-minute score. After-extra-time scores are published separately.

## 12. Bankroll and betting-agent guardrails

Implemented: `scripts/paper_bet.py` writes a conservative paper ledger with stake caps and no-bet reasons.

Next: evaluate paper results after resolved matches before any real-money automation.

## 13. Player data

Implemented: ESPN leader extraction and news risk terms.

Implemented: API-Football fixture mapping with optional quota-protected detail calls for injuries, lineups and player stats.

Blocked: API-Football currently returns no 2026 fixtures for the tested World Cup window.

Future scorer model: only publish buteur forecasts after expected minutes, penalty/set-piece roles, recent shot/xG volume, injury status and player prop odds are available.

## 14. Refresh automation

Implemented:

- `scripts/refresh_once.py`
- `scripts/watch_refresh.py --minutes 30 --min-odds-credits 25`
- `scripts/refresh_once.ps1`

## 15. Dashboard

Implemented: `outputs/football_forecast_dashboard.html`.

Run with:

```powershell
python .\scripts\build_dashboard.py
```
