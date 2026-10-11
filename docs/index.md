# ForgeFix

**One command to set up, health-check, and repair any open-source project.**

```bash
pipx install forgefix
cd your-project
forgefix doctor      # deterministic 0-100 health score + fixes
forgefix up          # dry-run bring-up plan
forgefix up --apply  # repair setup, install deps, run tests
```

![ForgeFix fixing a broken repo: score 42 to 91 in one command](https://raw.githubusercontent.com/BistaDinesh03/forgefix/main/demo/demo.gif)

## The problem

The first hour in a new repository is always the same loop: guess the install command,
discover there is no lockfile, hunt for the test runner, wonder if the project is
maintained. Maintainers re-explain the same missing pieces in every issue.

## What ForgeFix does

`doctor` checks the repository against a fixed set of onboarding rules (README, install
line, lockfile, CI, security policy, license, ready dev environment) and prints a
pass/warn/fail table with concrete fixes. `up` performs the bring-up: stack detection,
create-if-missing repairs, virtual environment, dependencies, tests. `report` writes the
same findings as markdown; `serve` exposes them over HTTP.

## How the score works

Every rule carries fixed fail and warn weights (for example: README 12/6, CI workflow
8/6, security policy 8/4). The score starts at 100, subtracts deductions, and clamps to
0-100. Same repository, same score — pinned by unit tests.

## Principles

- **Original code, MIT.** Metadata reads only; nothing is copied from inspected repos.
- **Read-only scans.** `doctor`/`report` never execute repository code.
- **Dry-run by default.** `up` only executes with `--apply`, only *creates* missing
  files, and never overwrites existing ones.
- **Deterministic scores.** Fixed per-rule weights, pinned by unit tests.

## Beyond the CLI

- **HTTP API** — `forgefix serve` exposes `/health`, `/doctor?path=`, `/report?path=`.
- **Plugins** — third-party checks via the `forgefix.plugins` entry-point group.
- **CI gate** — `forgefix doctor --min-score 80` exits with code 2 below the threshold.

Next: [CLI reference](cli.md) · [Plugins](plugins.md) · [HTTP API](api.md) · [FAQ](faq.md)
