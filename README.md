# Football Forecast Lab

Forecasting lab for football score predictions, MPP-style recommendations and tournament simulation.

The current implementation targets the 2026 World Cup knockout stage, but the code is structured as a general pipeline:

- public ESPN data ingestion,
- World Football Elo ingestion,
- optional free-key odds connectors,
- market-calibrated score model,
- feature store export,
- bracket simulation,
- validation,
- dashboard generation.

## Quick Start

```powershell
python .\scripts\refresh_once.py
```

This runs the pipeline, validates outputs and builds the dashboard.

Outputs:

- `outputs/mpp_pronostics_2026_16es.md`
- `outputs/mpp_pronostics_2026_16es.csv`
- `outputs/mpp_champion_simulation_2026.csv`
- `outputs/feature_store_current_matches.csv`
- `outputs/football_forecast_dashboard.html`
- `outputs/mpp_pronostics_2026_16es_audit.json`

## Optional API Keys

Copy `.env.example` to `.env` and add personal keys only if you have them.

```powershell
Copy-Item .env.example .env
```

Supported optional keys:

- `THE_ODDS_API_KEY`
- `API_FOOTBALL_KEY`

No secret is required for the baseline ESPN + Elo pipeline.

## Validation

```powershell
python .\scripts\train_ml.py
python -m compileall -q .\src .\scripts .\tests
python -m unittest discover -s tests
python .\scripts\validate_outputs.py
```

## Model

The active live model is market-calibrated and now also exports an advisory trained ML layer:

1. convert 1X2 and totals odds into fair probabilities,
2. fit a Poisson score distribution,
3. adjust with Elo, group form, rest and player leaders,
4. simulate extra time and penalties for advancement,
5. propagate the official bracket.
6. attach a trained historical softmax model as a secondary signal.

See `MODEL_CARD.md` and `docs/ROADMAP_15.md`.
