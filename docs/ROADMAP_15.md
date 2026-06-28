# Fifteen-Step Implementation Map

## 1. Baseline

Implemented: ESPN/DraftKings + Elo + form + Poisson + bracket.

## 2. Metrics

Implemented: log loss, Brier score, accuracy and score top-k helpers in `metrics.py`.

## 3. Multi-book odds

Implemented: optional The Odds API connector via `THE_ODDS_API_KEY`; API-Football key status wired via `API_FOOTBALL_KEY`.

Blocked without user-owned keys: live external odds calls.

## 4. Historical dataset

Implemented: CSV loader contract in `history.py`.

Blocked: no complete historical odds/player dataset bundled yet.

## 5. Feature store

Implemented: `outputs/feature_store_current_matches.csv`.

## 6. Backtest

Implemented: metric evaluator in `backtest.py`.

Blocked: needs historical rows with pre-match probabilities and final scores.

## 7. Better score model

Implemented: Poisson baseline with extra-time modelling.

Next: Dixon-Coles low-score correction once historical fitting data exists.

## 8. Trained ML

Implemented: package seams for feature rows and backtest.

Not claimed: no trained model is shipped because there is no validated historical training set yet.

## 9. Calibration

Implemented: reliability-bin and market-shrink helpers in `calibration.py`.

## 10. Ensemble

Implemented: weighted probability blending in `ensemble.py`.

## 11. MPP optimizer

Implemented: configurable score value function and safe/balanced/aggressive outputs.

## 12. League strategy

Implemented: strategy labels and rank-gap policy helpers in `strategy.py`.

## 13. Player data

Implemented: ESPN leader extraction and news risk terms.

Next: add structured lineups/injuries from a keyed provider.

## 14. Refresh automation

Implemented:

- `scripts/refresh_once.py`
- `scripts/watch_refresh.py --minutes 30`
- `scripts/refresh_once.ps1`

## 15. Dashboard

Implemented: `outputs/football_forecast_dashboard.html`.

Run with:

```powershell
python .\scripts\build_dashboard.py
```
