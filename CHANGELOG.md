# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-10-25

The viral-release milestone: run ForgeFix on every pull request, display a live
score badge, generate the missing setup files, and share the result.

### Added

- Official GitHub composite action (`.github/actions/forgefix`): installs
  ForgeFix, scores the checkout, compares against the base branch, and creates
  or updates one pull-request comment when the score is below the threshold or
  regresses
- `.github/workflows/forgefix-example.yml` and `docs/github-action.md` with a
  copy-paste workflow, input/output reference, and fork-permission notes
- `forgefix badge --write` generates `.forgefix-badge.json` in the
  Shields.io endpoint format; `--branch`, `--owner`, and `--repo` control the
  generated URL
- `forgefix up --badge` writes the badge document during a bring-up
- Automatic badge commit on `main` through the action's `update-badge` input
  (only when the score changes; the commit uses `[skip ci]`)
- `forgefix share` prints a Rich panel with the score, repository link, and demo
  GIF for social posts
- `forgefix up --apply` now generates missing `SECURITY.md`, `CONTRIBUTING.md`,
  `.env.example`, and `Dockerfile` files
- `.env.example` generation scans Python, JavaScript/TypeScript, and Go sources
  for environment-variable references and writes the keys commented out
- Stack-specific, non-root Dockerfile templates for Python, Node, Go, and a
  placeholder for unknown stacks
- Interactive confirmation before generated files are written; `forgefix up --yes`
  (or `-y`) bypasses the prompt
- Tests for file generation, `.env.example` scanning, Dockerfile templates,
  badge documents/URLs, repository-slug detection, and share text

### Changed

- Version bumped to `0.3.0`
- `forgefix up` now includes the generated policy, env, and Docker files in its
  repair plan; existing files are still never overwritten
- README, CLI reference, and MkDocs navigation document the action, badge, and
  share command

## [0.1.2] - 2026-10-12

Documentation and release-tooling patch. No CLI or plugin behavior changes.
Ships the fixed README to PyPI: version 0.1.1's page still used repo-relative
image paths, which do not render on PyPI.

### Added

- `.github/workflows/docker.yml`: multi-arch (linux/amd64 + linux/arm64) image
  published to `ghcr.io/bistadinesh03/forgefix`, with a
  `docker run --rm ... --version` smoke test; triggers on Dockerfile changes
  to main, `v*` tags, and manual dispatch
- Static, human-only Contributors section (a dynamic contributor image would
  also render bot accounts)

### Changed

- README images (banner light/dark, demo GIF, score badge, demo links) now load
  from `cdn.jsdelivr.net/gh/...@main`, so the PyPI project page renders them;
  a source comment documents why they must stay absolute
- Downloads badge now links to pepy.tech from a shields badge instead of the
  empty `pypi/dm` badge; the Ruff/Bandit row is unchanged
- GIF workflow attributes refresh commits to the maintainer noreply identity
  instead of `github-actions[bot]`

## [0.1.1] - 2026-10-12

Packaging and documentation release. No CLI or plugin behavior changes.

### Added

- Visual identity in `assets/`: `logo.svg`, `logo-dark.svg`, `logo-mono.svg`,
  `favicon.svg`, `badge-score.svg`, `banner.svg`, `banner-dark.svg`,
  `social-preview.svg`, plus rendered `logo.png` and `social-preview.png`
- `assets/brand.md` (palette, grid, regeneration commands) and
  `assets/render_rasters.py` (PNG regeneration via Pillow)
- `scripts/validate_assets.py` (local gate for the asset rules)
- `CITATION.cff`, `.github/CODEOWNERS`, `.github/FUNDING.yml`,
  `.github/ISSUE_TEMPLATE/` (bug report, feature request, config),
  `.github/PULL_REQUEST_TEMPLATE.md`, `.gitattributes`
- Demo media: `demo/demo.mp4`, `demo/demo-thumb.png`, `demo/prep_scratch.py`

### Changed

- README rewritten and restructured into 16 sections; every claim traced to a
  code path or command
- `demo/demo.tape` refreshed; `demo/demo.gif` regenerated from it
- `CONTRIBUTING.md`, `Makefile`, `docs/index.md`, `.gitignore` updated
- CI: `actions/checkout` v7, `github/codeql-action` v4, `actions/setup-python` v7,
  `actions/upload-artifact` v7, `actions/download-artifact` v8
- GIF workflow hardened (size gates, pinned tool installs)

### Fixed

- `forgefix/server.py`: path-escape handler re-raises with `raise ... from exc`
  (ruff B904)

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

[Unreleased]: https://github.com/BistaDinesh03/forgefix/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/BistaDinesh03/forgefix/compare/v0.1.2...v0.3.0
[0.1.2]: https://github.com/BistaDinesh03/forgefix/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/BistaDinesh03/forgefix/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/BistaDinesh03/forgefix/releases/tag/v0.1.0
