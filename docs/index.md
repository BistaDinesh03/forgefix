# ForgeFix

**One command to set up, health-check, and repair any open-source project.**

```bash
pip install forgefix
cd your-project
forgefix doctor     # deterministic 0-100 health score + fixes
forgefix up         # dry-run bring-up plan
forgefix up --apply # repair setup, install deps, run tests
```

## The problem

The first hour in a new repository is always the same loop: guess the install command,
discover there is no lockfile, hunt for the test runner, wonder if the project is
maintained. Maintainers re-explain the same missing pieces in every issue.

## The idea

Turn that tribal knowledge into a deterministic check with a score, a report, and a
bring-up command — usable by humans, CI, and other tools (HTTP API + JSON + plugins).

## Principles

- **Original code, MIT.** Metadata reads only; nothing is copied from inspected repos.
- **Read-only scans.** `doctor`/`report` never execute repository code.
- **Dry-run by default.** `up` only executes with `--apply`, only *creates* missing
  files, and never overwrites existing ones.
- **Deterministic scores.** Fixed per-rule weights, pinned by unit tests.

Next: [CLI reference](cli.md) · [Plugins](plugins.md) · [HTTP API](api.md)
