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
- [x] Commit, push, and switch the GitHub repo to public
- [x] Add immutable pre-match prediction and odds ledgers
- [x] Add required prediction fields: model version, 90/after-extra score distributions, calibration, no-bet reason and stake
- [x] Add Dixon-Coles 90-minute score distribution and separate after-extra-time output
- [x] Add leakage-safe backtest, calibration, score-model and paper-bet scripts
- [x] Wire API-Football fixture mapping with quota-protected detail calls
- [x] Add separate append-only resolved-results ledger
- [x] Add ESPN result resolver for completed matches
- [x] Join pre-match predictions with resolved results during backtest/calibration
- [x] Add one-score MPP-style picks view using after-extra-time score scope
- [x] Add full matchday cycle orchestration script
- [x] Regenerate public reports, README assets and validation outputs
- [x] Add odds movement analysis from repeated pre-match snapshots
- [x] Add availability coverage report for rosters, lineups, injuries/news and manual lineup checks
- [x] Add market-edge strategy report across 1X2 and totals with calibration/availability gates
- [x] Publish odds movement, availability and market-edge reports in README/docs

## Review / Results
- Commands run: `python .\scripts\train_ml.py`; `python .\scripts\refresh_once.py`; `python .\scripts\run_matchday_cycle.py`; `python .\scripts\resolve_results.py`; `python .\scripts\analyze_odds_movement.py`; `python .\scripts\build_availability_report.py`; `python .\scripts\build_market_edges.py`; `python .\scripts\backtest_models.py`; `python .\scripts\calibrate_models.py`; `python .\scripts\paper_bet.py`; `python .\scripts\build_mpp_picks.py`; `python .\scripts\train_score_model.py`; `python .\scripts\build_readme_assets.py`; `python -m compileall -q .\src .\scripts .\tests`; `python -m unittest discover -s tests`; `python .\scripts\validate_outputs.py`; `git diff --check`.
- Evidence: 16 predictions, 32 tournament teams, normalized 90/after-extra score distributions, ledger rows captured only for pre-match predictions, South Africa 0-1 Canada resolved in `outputs/ledger/resolved_results.jsonl`, odds movement report generated for 15 unresolved clean events, availability report generated for all 16 matches, market-edge report generated with 77 candidate rows, reports generated under `outputs/backtests`, MPP one-score picks generated, paper ledger generated, public snapshots copied to `docs/generated/`, 21 tests pass, and GitHub visibility is `PUBLIC`.
- Risks / rollback: API-Football key works but returns no fixtures for the tested 2026 World Cup window; scorer/buteur modeling remains intentionally disabled until structured player inputs exist; the first resolved match was not captured as a clean pre-match ledger row, so live rolling metrics remain pending until current clean snapshots finish; market-edge real staking remains locked until enough clean resolved rows exist.
- Follow-ups: add final scores to ledger after matches, evaluate calibration/CLV, then only consider real-money micro-stakes if paper betting beats baselines without leakage.
