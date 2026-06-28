# Task
- Goal: make the forecast lab public-ready, secure optional API key setup, remove MPP-specific optimization, and publish readable results/backtests in the README.
- Scope: local Python pipeline, optional odds connectors, score/result reporting, README charts/assets, docs, tests, Git/GitHub visibility.
- Non-goals: placing real-money bets automatically; scraping proprietary MPP coefficients; storing or printing API secrets.
- Risks: external API shape drift, missing user-owned API keys, limited player-level data, no historical odds archive bundled yet.

## Plan
- [x] Explore current project and tool auth
- [x] Promote prototype into a repo-style package
- [x] Add roadmap modules for metrics, features, history, backtest, calibration, ensemble, strategy, refresh and dashboard
- [x] Run pipeline and validations
- [x] Initialize Git/GitHub
- [x] Add secure local secret setup and redact secret-bearing URLs
- [x] Wire The Odds API quota headers and multi-book h2h/totals blending
- [x] Replace MPP optimization outputs with plain result + exact-score forecasts
- [x] Generate public README charts and result/backtest snapshot
- [x] Run training, refresh, tests and output validation
- [ ] Commit, push, and switch the GitHub repo to public

## Review / Results
- Commands run: `python .\scripts\train_ml.py`; `python .\scripts\refresh_once.py`; `python .\scripts\build_readme_assets.py`; `python -m compileall -q .\src .\scripts .\tests`; `python -m unittest discover -s tests`; `python .\scripts\validate_outputs.py`; `git diff --check`.
- Evidence: 16 predictions, 32 tournament teams, valid advancement probability totals, dashboard generated, README SVG charts generated, public CSV snapshots copied to `docs/generated/`, and 8 tests pass.
- Risks / rollback: The Odds API live blending is unverified until a user-owned key is added; scorer/buteur modeling remains intentionally disabled until structured player inputs exist.
- Follow-ups: add `THE_ODDS_API_KEY` locally, refresh once to verify quota headers/matched markets, then consider API-Football for lineups/injuries.
