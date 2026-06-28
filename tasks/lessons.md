# Lessons learned

## PowerShell heredocs
- Mistake: Bash-style heredocs fail under PowerShell.
- Trigger: running inline Python with `python - <<'PY'`.
- Prevention rule: use PowerShell here-strings piped to Python.
- Example: `@' ... '@ | python -`
- Date: 2026-06-28
