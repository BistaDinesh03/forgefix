# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-11

### Added

- `forgefix doctor` — deterministic 0–100 health score, pass/warn/fail/skip table,
  `--json`, `--min-score` gate, `.forgefix.yml` overrides
- `forgefix up` — one-command bring-up: stack detection (python/node/go),
  create-if-missing setup repairs, virtualenv + dependencies, `pip freeze` lockfile,
  test run, optional dev server; dry-run by default, `--apply` to execute
- `forgefix report` — markdown health report with category breakdown and top fixes
- `forgefix serve` — FastAPI server exposing `/health`, `/doctor`, `/report`
- `forgefix init` — scaffolds `.forgefix.yml`
- `forgefix cloud` — stub pointing at the (not enabled) hosted offering
- Plugin API via the `forgefix.plugins` entry-point group plus an example plugin
- Bundled fixtures: `tests/fixtures/broken_repo` (42/100) and
  `tests/fixtures/minimal_repo` (100/100)
- CI matrix (py3.11/3.12 × ubuntu/macos), CodeQL, trusted-publisher PyPI release
  workflow, vhs-driven demo recording workflow
- pre-commit (ruff, ruff-format, bandit, gitleaks), `.gitleaks.toml`,
  multi-stage non-root Docker image, devcontainer, Makefile
- Docs site (mkdocs-material): index, cli, plugins, api, faq, monetization

[Unreleased]: https://github.com/BistaDinesh03/forgefix/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/BistaDinesh03/forgefix/releases/tag/v0.1.0
