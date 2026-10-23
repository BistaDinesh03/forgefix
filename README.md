<!-- Images use absolute jsDelivr URLs, not repo-relative paths, because this
     README is also rendered on PyPI (long_description), where relative paths
     resolve to pypi.org and show broken images. @main keeps them current. -->
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://cdn.jsdelivr.net/gh/BistaDinesh03/forgefix@main/assets/banner-dark.svg">
    <img src="https://cdn.jsdelivr.net/gh/BistaDinesh03/forgefix@main/assets/banner.svg" alt="ForgeFix - one command to fix any repo's setup" width="100%">
  </picture>
</p>

<p align="center">
  <strong>One command to set up, health-check, and repair any open-source project.</strong>
</p>

<p align="center">
  <a href="https://github.com/BistaDinesh03/forgefix/actions/workflows/ci.yml"><img src="https://github.com/BistaDinesh03/forgefix/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/BistaDinesh03/forgefix/actions/workflows/codeql.yml"><img src="https://github.com/BistaDinesh03/forgefix/actions/workflows/codeql.yml/badge.svg" alt="CodeQL"></a>
  <img src="https://img.shields.io/pypi/v/forgefix" alt="PyPI version">
  <a href="https://pepy.tech/project/forgefix"><img src="https://img.shields.io/badge/downloads-see%20pepy.tech-blue" alt="Downloads: see pepy.tech"></a>
  <img src="https://img.shields.io/pypi/pyversions/forgefix" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-2563EB" alt="License: MIT">
  <img src="https://img.shields.io/badge/ruff-checked-2563EB" alt="Ruff checked">
  <img src="https://img.shields.io/badge/bandit-pass-16A34A" alt="Bandit pass">
  <img src="https://img.shields.io/badge/coverage%20gate-85%25-16A34A" alt="Coverage gate: 85%">
</p>

<p align="center">
  <a href="#quickstart">Install</a> ·
  <a href="docs/index.md">Docs</a> ·
  <a href="#demo">Demo</a> ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

## Demo

<p align="center">
  <img src="https://cdn.jsdelivr.net/gh/BistaDinesh03/forgefix@main/demo/demo.gif" alt="ForgeFix fixing a broken repo: score 42 → 91 in one command" width="100%">
</p>

What you are watching:

1. `forgefix doctor` on a deliberately broken repo — an `app.py` and a `pyproject.toml`,
   but no README, no lockfile, no CI, no security policy. Score: **42/100**.
2. `forgefix report` — the same findings as markdown, with the highest-value fixes first.
3. `forgefix up --apply` — creates the missing setup files, makes `.venv`, installs the
   project, writes `requirements.lock`, and runs the test suite.
4. `forgefix doctor` again — the same repo now scores **91/100**.

<img src="https://cdn.jsdelivr.net/gh/BistaDinesh03/forgefix@main/assets/badge-score.svg" alt="health: 42 to 91" height="20">

Still frame: [demo/demo-thumb.png](https://cdn.jsdelivr.net/gh/BistaDinesh03/forgefix@main/demo/demo-thumb.png) · MP4 for social:
[demo/demo.mp4](https://cdn.jsdelivr.net/gh/BistaDinesh03/forgefix@main/demo/demo.mp4)

## The problem

Cloning a new repository usually starts a scavenger hunt. There is no lockfile, so the
install is not reproducible. The README says "install dependencies" without saying how.
There is no CI, so nobody knows whether `main` even passes its own tests. There is no
security policy, so vulnerability reports arrive as public issues.

```console
$ git clone https://github.com/example/project && cd project
$ make dev
make: *** No rule to make target 'dev'.  Stop.
$ pip install -r requirements.txt
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
```

Every one of those gaps is visible in file names and metadata alone. ForgeFix reads that
metadata, scores the gaps, and fixes the ones it can fix.

## What ForgeFix does

`forgefix doctor` checks a repository against a fixed set of onboarding rules and prints
a pass/warn/fail table with a concrete fix for each gap. `forgefix up` performs the
bring-up: stack detection, create-if-missing repairs, virtual environment, dependencies,
tests. Scans are read-only and never execute repository code.

| Command | What it does | Example |
| --- | --- | --- |
| `forgefix init` | Write a starter `.forgefix.yml` (disable rules, set a score gate) | `forgefix init` |
| `forgefix doctor` | Print the health table with fix suggestions | `forgefix doctor --min-score 80` |
| `forgefix up` | Dry-run the bring-up plan (nothing is executed) | `forgefix up --no-serve` |
| `forgefix up --apply` | Repair setup, create `.venv`, install, run tests | `forgefix up --apply` |
| `forgefix report` | Write the markdown health report | `forgefix report --output health.md` |
| `forgefix serve` | Run the HTTP API (`/health`, `/doctor`, `/report`) | `forgefix serve --port 8000` |

`doctor` also emits `--json` for machines. `up` never overwrites an existing file and
never invents a LICENSE for you.

## How the score works

Every rule carries two fixed weights: the points lost when the check fails, and the
points lost when it only warns. The score starts at 100, subtracts every deduction, and
stays in the 0–100 range. No heuristics and no network calls — the same repository always
scores the same, and unit tests pin the exact numbers.

| Check | Category | Fail | Warn |
| --- | --- | ---: | ---: |
| README present | docs | 12 | 6 |
| One-command install line | docs | 8 | 4 |
| Demo GIF or screenshot | docs | 3 | 2 |
| Dependency lockfile | deps | 6 | 3 |
| Pinned dependency versions | deps | 5 | 2 |
| Dockerfile or devcontainer | automation | 4 | 1 |
| CI workflow | automation | 8 | 6 |
| Security policy | security | 8 | 4 |
| Open-source license | legal | 6 | 3 |
| Ready dev environment | environment | 7 | 3 |

Plugins add checks with their own weights — the bundled example checks for an
`.editorconfig` at 3 fail / 1 warn points in the `polish` category.

A real report from the broken fixture, abridged:

```markdown
# ForgeFix health report

- Repository: `demo-scratch`
- Health score: **42/100** (critical)
- Checks: 0 pass, 5 warn, 6 fail, 0 skip

## Category breakdown

| Category | Points lost |
| --- | --- |
| automation | 9 |
| deps | 5 |
| docs | 22 |
| environment | 7 |
| legal | 6 |
| polish | 1 |
| security | 8 |

## Top fixes

1. **README present** (-12): Add a README.md with a one-line pitch and a getting-started section.
2. **One-command install line** (-8): Add a copy-pasteable install command (pip install / npm install / make setup).
3. **CI workflow** (-8): Add a CI workflow under .github/workflows/ that runs lint and tests.
```

The check table above it lists all 11 findings (for example: `FAIL | CI workflow |
automation | no CI workflow found`).

## What it checks

Ten built-in rules. A scan reads file names and text only - nothing is
executed, downloaded, or copied:

| Rule | What it looks for |
| --- | --- |
| `readme` | A README (`.md`, `.markdown`, `.rst`, `.txt`) at the repository root |
| `install` | An install line in the README (`pip install`, `npm install`, `make setup`, ...) |
| `demo` | A `.gif` in the root, `demo/`, `docs/`, `assets/`, `images/`, or `.github/` |
| `lockfile` | A committed lockfile (`requirements.lock`, `poetry.lock`, `uv.lock`, `package-lock.json`, `yarn.lock`, `go.sum`, `Cargo.lock`) |
| `pinned_deps` | `==` pins in `requirements.txt`, or a committed lockfile |
| `devcontainer` | A `Dockerfile`, `Containerfile`, `docker-compose.*`, or `.devcontainer/` |
| `ci` | `.github/workflows/`, `.gitlab-ci.yml`, `.circleci/`, `Jenkinsfile`, `.travis.yml` |
| `security` | A `SECURITY.md` (or `.github/SECURITY.md`) |
| `license` | A `LICENSE`, `LICENCE`, or `COPYING` file (plain, `.md`, or `.txt`) |
| `dev_env` | A `.venv` in a Python project (`WARN` until created, skipped outside Python projects) |

Each rule maps 1:1 to the weight table above. Disable rules per repository
with `.forgefix.yml` (`forgefix init`): `disabled_rules: [demo]` or
`ignore: [lockfile, pinned_deps]` both skip the listed rule ids.

## Quickstart

```bash
pipx install forgefix    # from PyPI once published
# or straight from the repository:
pip install "git+https://github.com/BistaDinesh03/forgefix"
cd your-repo
forgefix doctor
```

To auto-fix what `doctor` found:

```bash
forgefix up --apply
```

Try the bundled fixtures right now: `forgefix doctor --path tests/fixtures/broken_repo`
scores 42, `--path tests/fixtures/minimal_repo` scores 100.

## What it is NOT

Compared by category, not by name:

| Category | What it covers | What ForgeFix adds |
| --- | --- | --- |
| Static linters | Style and correctness inside files | Repository-level onboarding health: docs, CI, license, lockfile |
| Dependency scanners | Vulnerable and outdated dependencies | A score and repairs; it does not audit package contents |
| Setup wizards | Bootstrapping brand-new projects | Works on the repositories you already cloned |
| CI gate tools | Enforcing checks in pipelines | The check itself, runnable locally and over HTTP |

What ForgeFix is not:

- Not a security scanner. It checks whether a security *policy* exists, not for vulnerabilities.
- Not a package manager. It never resolves, pins, or vendors dependencies for you.
- Not a linter replacement. Keep ruff, eslint, and their friends; they work inside files.
- Not a bot. It never opens pull requests and never pushes to your repository.

## Plugins

A plugin is a class with a `name` and a `check(root)` method that returns `Finding`
objects. This is the bundled example, verbatim from
[`forgefix/plugins/example.py`](forgefix/plugins/example.py):

```python
from pathlib import Path

from forgefix.core.rules import Finding


class ExamplePlugin:
    """Bundled example plugin registered under the ``forgefix.plugins`` group."""

    name = "example"

    def check(self, root: Path) -> list[Finding]:
        """Report whether the repository ships an .editorconfig."""
        present = (root / ".editorconfig").is_file()
        return [
            Finding(
                rule_id="editorconfig",
                category="polish",
                title="EditorConfig present",
                status="pass" if present else "warn",
                detail=(
                    ".editorconfig found"
                    if present
                    else "no .editorconfig (indentation and charset may drift between editors)"
                ),
                suggestion=(
                    "Add an .editorconfig with basic indentation, charset, and newline rules."
                ),
                weight=3,
                warn_weight=1,
                source="plugin:example",
            )
        ]
```

Register it under the `forgefix.plugins` entry-point group and ForgeFix discovers it
automatically. A broken plugin is logged and skipped; it cannot break a scan.
Details in [docs/plugins.md](docs/plugins.md).

## HTTP API

```bash
forgefix serve                       # http://127.0.0.1:8000
```

```console
$ curl http://127.0.0.1:8000/health
{"status":"ok","version":"0.2.0"}

$ curl "http://127.0.0.1:8000/doctor?path=."
{"path": "...", "score": {"total": 42, ...}, "findings": [...], "plugins": [...]}

$ curl "http://127.0.0.1:8000/report?path=."
{"path": "...", "score": 42, "markdown": "# ForgeFix health report ..."}
```

The API is the same scanner as the CLI: same weights, same score, same findings.

## Use it as a CI gate

`forgefix doctor` exits with code 2 when the score is below `--min-score`, so
one pipeline step can fail a pull request that drops the health score:

```yaml
- name: ForgeFix health gate
  run: |
    pipx install "git+https://github.com/BistaDinesh03/forgefix"
    forgefix doctor --path . --min-score 80 --json
```

Run `forgefix init` first to store the threshold in `.forgefix.yml`
(`min_score`); the file's value applies whenever the flag is absent. `--json`
prints the score and every finding for downstream steps.

## Roadmap

| Version | Focus |
| --- | --- |
| v0.2 | Rust and Java/Gradle stack detection · per-rule fix scripts · published JSON schema for `--json` |
| v0.3 | SARIF export for GitHub code scanning · plugin authoring guide · richer `.forgefix.yml` (per-rule weights) |
| v1.0 | Stable plugin API · `forgefix cloud` dashboard for private repos ([docs/monetization.md](docs/monetization.md)) · migration guide from 0.x |

## Contributing

- Setup: `make setup` — editable install plus pre-commit hooks.
- Tests: `make test` — the 85% coverage gate is enforced in `pyproject.toml`.
- Lint: `make lint` (ruff check + format) and `make type` (mypy).
- Pull requests: focused changes, tests included, CHANGELOG entry, no secrets.

Full guidelines in [CONTRIBUTING.md][contributing].

## License

[MIT](LICENSE) © ForgeFix contributors. Original code; repository metadata reads only,
nothing is copied from inspected projects.

---

Built with Typer, FastAPI, and Pydantic. Demo recorded with [VHS](https://github.com/charmbracelet/vhs).

## Contributors

- [@BistaDinesh03](https://github.com/BistaDinesh03) - maintainer

<!-- Hand-maintained, human-only list on purpose. A dynamic contributor image
     (contrib.rocks / all-contributors) also renders bot accounts -
     dependabot[bot], github-actions[bot], github-advanced-security[bot] -
     which are automation, not people. Add humans here by hand. -->

[contributing]: CONTRIBUTING.md
