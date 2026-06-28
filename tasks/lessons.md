# Lessons learned

## PowerShell heredocs
- Mistake: Bash-style heredocs fail under PowerShell.
- Trigger: running inline Python with `python - <<'PY'`.
- Prevention rule: use PowerShell here-strings piped to Python.
- Example: `@' ... '@ | python -`
- Date: 2026-06-28

## Forecast output scope
- Mistake: keeping app-specific optimization labels when the user wants a general football model.
- Trigger: MPP initially shaped the prototype, then scope changed to plain match result and exact score.
- Prevention rule: public outputs should stay app-neutral: result, exact score, probabilities, model limits and backtests.
- Example: avoid safe/aggressive score variants unless a dedicated strategy module is explicitly requested.
- Date: 2026-06-28

## Pre-match leakage
- Mistake: blending odds captured after kickoff into what looked like a pre-match forecast.
- Trigger: external odds APIs can return live odds for matches already started.
- Prevention rule: every ledger/backtest row must satisfy `generated_at_utc < kickoff_utc`; post-kickoff rows can be displayed but never backtested or staked.
- Example: tag rows as `after_kickoff_or_unknown` and set `stake_eur=0`.
- Date: 2026-06-28
