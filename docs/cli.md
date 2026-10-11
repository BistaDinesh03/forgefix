# CLI reference

Global: `forgefix --version`, `forgefix --help` (also `forgefix -h`).

## `forgefix doctor`

Scan a repository and print the health table.

| Flag | Effect |
| --- | --- |
| `--path DIR` | Repository to scan (default `.`) |
| `--json` | Machine-readable output (findings, score, breakdown, plugins) |
| `--min-score N` | Exit code `2` when the score is below N (CI gate) |

Exit codes: `0` healthy, `2` below threshold / usage error.

```bash
forgefix doctor --path ../some-repo --json | jq .score.total
forgefix doctor --min-score 80        # fail CI on regressions
```

## `forgefix up`

One-command bring-up. **Dry-run by default** — nothing runs without `--apply`.

| Flag | Effect |
| --- | --- |
| `--path DIR` | Repository to bring up (default `.`) |
| `--apply` | Execute the plan |
| `--no-serve` | Never start a detected dev server |

The plan, in order:

1. **Repairs (create-if-missing):** `README.md` skeleton, `SECURITY.md`,
   `.editorconfig`, `.github/workflows/ci.yml`. Existing files are never touched and a
   LICENSE is never invented.
2. **Environment (python):** `.venv` via `python -m venv`, `pip install -e .`
   (+ `pytest` when a `tests/` directory exists).
3. **Lockfile (python):** `pip freeze --all > requirements.lock`.
4. **Tests:** `pytest` / `npm test` / `go test ./...` when detectable.
5. **Dev server** when unambiguous (npm `dev` script, `[tool.forgefix].serve`,
   `main.go`), started detached; skip with `--no-serve`.

Stack detection first-match: `pyproject.toml`/`setup.py`/`setup.cfg`/`requirements.txt`
→ python; `package.json` → node; `go.mod` → go; otherwise none.

## `forgefix report`

Writes `reports/forgefix-report.md` (configurable via `.forgefix.yml` `report_path`)
with the score, category breakdown, and top fixes.

| Flag | Effect |
| --- | --- |
| `--path DIR` | Repository to scan |
| `--output FILE` | Alternate destination |

## `forgefix serve`

Runs the FastAPI app (`/health`, `/doctor`, `/report`) — see [HTTP API](api.md).

| Flag | Effect |
| --- | --- |
| `--host` | Default `127.0.0.1` |
| `--port` | Default `8000` |

## `forgefix init`

Scaffolds `.forgefix.yml` in `--path` (default `.`); never overwrites an existing file.

```yaml
report_path: reports/forgefix-report.md
disabled_rules: []
min_score: 80
```

## `forgefix cloud`

Placeholder for the hosted offering — prints a pointer to
[monetization](monetization.md). No billing code, no paywall, MIT unchanged.
