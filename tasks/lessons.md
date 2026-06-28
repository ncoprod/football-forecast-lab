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
