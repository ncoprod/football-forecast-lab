# Football Forecast Lab

Public football forecasting lab for match result, exact-score and tournament-winner probabilities.

The current live target is the 2026 World Cup round of 32, but the code is structured as a reusable pipeline:

- ESPN public data ingestion for fixtures, results, market odds, leaders and news
- World Football Elo team-strength ingestion
- optional The Odds API multi-book odds via a local free-tier key
- market-calibrated Poisson score model with controlled context adjustments
- historical softmax ML layer trained on international results since 2000
- bracket propagation to estimate tournament winner probabilities
- generated dashboard, public CSV snapshots and README charts

## Quick Start

```powershell
python .\scripts\refresh_once.py
```

This refreshes the live data, validates generated outputs and rebuilds the static dashboard.

Main local outputs:

- `outputs/match_predictions_2026_r32.md`
- `outputs/match_predictions_2026_r32.csv`
- `outputs/champion_simulation_2026.csv`
- `outputs/feature_store_current_matches.csv`
- `outputs/football_forecast_dashboard.html`
- `outputs/match_predictions_2026_r32_audit.json`

Public snapshots copied into the repo live under `docs/generated/`.

## Data Sources

- [ESPN public soccer endpoints](https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard) for fixtures, summaries, market odds and news
- [World Football Elo](https://www.eloratings.net/) for team-strength ratings
- [The Odds API v4](https://the-odds-api.com/liveapi/guides/v4/) for optional multi-book h2h/totals odds and quota headers
- [API-Football](https://www.api-football.com/) as the next keyed source for lineups, injuries, player stats and extra odds
- [football-data.org](https://www.football-data.org/documentation/api) as a possible fixtures/results supplement, not a primary odds source

## Secure API Keys

Never paste API keys in chat, issues, commits or shell history. Use the local masked prompt:

```powershell
.\scripts\set_secret.ps1 -Name THE_ODDS_API_KEY
```

The script writes the value to `.env`, which is ignored by Git. Optional non-secret knobs:

```powershell
THE_ODDS_API_REGIONS=eu,uk
THE_ODDS_API_MARKETS=h2h,totals
```

The default request is intentionally modest for the free tier. The pipeline reads The Odds API quota headers when available and stores only counts such as remaining/used credits.

## Refresh Loop

For an aggressive local monitor with a quota safety stop:

```powershell
python .\scripts\watch_refresh.py --minutes 30 --min-odds-credits 25
```

With a 500-credit free monthly plan, do not run a high-cost odds call every few minutes for weeks. The practical pattern is frequent refresh near match windows, slower refresh outside them, and a hard minimum-credit stop.

## Validation

```powershell
python .\scripts\train_ml.py
python -m compileall -q .\src .\scripts .\tests
python -m unittest discover -s tests
python .\scripts\validate_outputs.py
python .\scripts\build_readme_assets.py
```

## Model

The live model is market-calibrated first and ML-assisted second:

1. convert 1X2 and totals odds into fair probabilities
2. blend optional multi-book odds when a local key is configured
3. fit a Poisson score distribution
4. adjust modestly with Elo, group form, rest and player leaders
5. simulate extra time for knockout matches, before penalties
6. attach historical ML probabilities as an advisory signal
7. propagate the bracket to champion probabilities

The recommended exact score is simply the most likely score in the distribution. No app-specific optimizer or league strategy is applied.

## Betting-Agent Direction

This repo is a decision-support lab, not an automatic real-money betting bot. A future bankroll agent should start with paper trading, stake caps, daily loss limits, model-vs-market edge thresholds, quota tracking and human confirmation before any real-money action.

Exact scorer forecasts are a separate, harder model: they need expected minutes, lineups, injuries/suspensions, penalty and set-piece roles, recent shot/xG volume and player prop odds. Until those inputs are reliable, publishing scorer picks would be fake precision.

See `MODEL_CARD.md` and `docs/ROADMAP_15.md` for the current model limits and next steps.

<!-- forecast-snapshot:start -->

## Public Snapshot

![Exact score probabilities](docs/assets/exact_score_probabilities.svg)

![Champion probabilities](docs/assets/champion_probabilities.svg)

![ML backtest log loss](docs/assets/ml_backtest_log_loss.svg)

Generated UTC: `2026-06-28T20:43:30.948927+00:00`

## Match Forecasts

| Match | Status | Result | P(result) | Exact score | P(score) |
|---|---|---|---:|---:|---:|
| South Africa - Canada | after_kickoff_or_unknown | Canada gagne | 60.9% | 0-1 | 16.9% |
| Brazil - Japan | pre_match | Brazil gagne | 65.4% | 1-0 | 15.5% |
| Germany - Paraguay | pre_match | Germany gagne | 80.2% | 2-0 | 14.0% |
| Netherlands - Morocco | pre_match | Netherlands gagne | 51.3% | 1-0 | 14.7% |
| Ivory Coast - Norway | pre_match | Norway gagne | 54.8% | 0-1 | 12.1% |
| France - Sweden | pre_match | France gagne | 85.0% | 2-0 | 13.0% |
| Mexico - Ecuador | pre_match | Mexico gagne | 54.6% | 1-0 | 19.6% |
| England - Congo DR | pre_match | England gagne | 82.9% | 2-0 | 16.3% |
| Belgium - Senegal | pre_match | Belgium gagne | 51.3% | 1-0 | 15.3% |
| United States - Bosnia-Herzegovina | pre_match | United States gagne | 76.4% | 1-0 | 14.7% |
| Spain - Austria | pre_match | Spain gagne | 81.0% | 1-0 | 15.9% |
| Portugal - Croatia | pre_match | Portugal gagne | 60.7% | 1-0 | 15.5% |
| Switzerland - Algeria | pre_match | Switzerland gagne | 61.8% | 1-0 | 15.3% |
| Australia - Egypt | pre_match | Egypt gagne | 45.2% | 0-1 | 17.4% |
| Argentina - Cape Verde | pre_match | Argentina gagne | 89.9% | 2-0 | 16.5% |
| Colombia - Ghana | pre_match | Colombia gagne | 71.4% | 1-0 | 18.3% |

## Tournament Simulation

| Rank | Team | Champion | Final | Semi |
|---:|---|---:|---:|---:|
| 1 | Argentina | 25.4% | 40.2% | 67.5% |
| 2 | France | 18.8% | 29.3% | 47.7% |
| 3 | Spain | 18.1% | 34.2% | 53.0% |
| 4 | Brazil | 9.8% | 21.3% | 38.4% |
| 5 | Germany | 9.3% | 22.4% | 43.6% |
| 6 | England | 6.2% | 12.5% | 26.3% |
| 7 | Portugal | 3.3% | 9.1% | 19.0% |
| 8 | Netherlands | 2.1% | 4.7% | 11.0% |
| 9 | Mexico | 1.7% | 4.2% | 10.6% |
| 10 | Colombia | 1.1% | 3.9% | 14.9% |

## Historical ML Backtest

Rows: train `18164`, validation `3581`, test `3670`.

| Model | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| Softmax ML | 0.606 | 0.510 | 0.868 |
| Elo baseline | 0.605 | 0.542 | 0.926 |
| Majority baseline | 0.472 | 0.636 | 1.054 |

<!-- forecast-snapshot:end -->
