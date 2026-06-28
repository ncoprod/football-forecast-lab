# Task
- Goal: turn the football forecasting prototype into a clean GitHub-ready repo and implement the 15-step roadmap as code, scaffolding, docs and validation.
- Scope: local Python pipeline, optional odds connectors, model/backtest scaffolding, dashboard generation, tests, Git/GitHub init.
- Non-goals: creating accounts or storing API secrets; claiming trained ML quality without a historical training dataset.
- Risks: external API shape drift, missing API keys, limited player-level data, no historical odds archive bundled yet.

## Plan
- [x] Explore current project and tool auth
- [x] Promote prototype into a repo-style package
- [x] Add roadmap modules for metrics, features, history, backtest, calibration, ensemble, strategy, refresh and dashboard
- [x] Run pipeline and validations
- [x] Initialize Git/GitHub

## Review / Results
- Commands run: `python .\scripts\refresh_once.py`; `python -m compileall -q .\src .\scripts .\tests`; `python -m unittest discover -s tests`; `python .\scripts\validate_outputs.py`.
- Evidence: 16 predictions, 32 tournament teams, valid advancement probability totals, dashboard and feature store generated. GitHub repo created at `https://github.com/ncoprod/football-forecast-lab`.
- Risks / rollback: optional odds connectors need user-owned API keys; trained ML requires a historical dataset before claims can be made.
- Follow-ups: add The Odds API key, add historical odds/player dataset, then run real backtests and calibrate trained models.
