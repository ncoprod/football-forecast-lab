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

Implemented: metric evaluator in `backtest.py`.

Blocked: needs historical rows with pre-match probabilities and final scores.

## 7. Better score model

Implemented: Poisson baseline with extra-time modelling.

Next: Dixon-Coles low-score correction once historical fitting data exists.

## 8. Trained ML

Implemented: first softmax regression model trained on historical international results since 2000.

Current test performance from latest run:

- softmax log loss: 0.8683
- softmax Brier: 0.5103
- softmax accuracy: 0.6060
- Elo baseline log loss: 0.9263
- majority baseline log loss: 1.0537

Next: add historical odds and train CatBoost/LightGBM.

## 9. Calibration

Implemented: reliability-bin and market-shrink helpers in `calibration.py`.

## 10. Ensemble

Implemented: weighted probability blending in `ensemble.py`.

## 11. Score/result recommendation

Implemented: the recommended result is the most likely 1/N/2 outcome; the recommended exact score is the highest-probability score in the final-score distribution before penalties.

## 12. Bankroll and betting-agent guardrails

Planned: a paper-trading ledger, stake caps, daily loss limit, cooldown rules, model-vs-market edge thresholds and human confirmation before any real-money bet.

## 13. Player data

Implemented: ESPN leader extraction and news risk terms.

Next: add structured lineups/injuries from a keyed provider.

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
