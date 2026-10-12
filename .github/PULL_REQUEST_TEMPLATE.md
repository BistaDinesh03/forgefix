## What changed

<!-- One or two sentences. Close related issues with "Fixes #N". -->

## Checklist

- [ ] `python -m pytest -q` passes (coverage gate 85%)
- [ ] `ruff check .` and `ruff format --check .` pass
- [ ] `mypy forgefix` passes
- [ ] `bandit -r forgefix -lll -q` reports nothing
- [ ] Docs updated if behavior changed
- [ ] No unrelated refactors; no secrets or `.env` files
