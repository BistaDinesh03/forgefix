# Contributing to ForgeFix

Thanks for helping. This project ships original code only — **do not copy source code
from other repositories, trending or otherwise.** Metadata-inspired ideas are fine;
pasted code is not.

## Development setup

```bash
git clone https://github.com/BistaDinesh03/forgefix.git
cd forgefix
make setup          # pip install -e ".[dev]" + pre-commit hooks
make test           # pytest, coverage gate 85% (enforced in pyproject.toml)
make lint && make type
```

Windows without `make`? Every target is a one-liner: `python -m pytest -q`,
`ruff check .`, `ruff format --check .`, `mypy forgefix`, `bandit -r forgefix -lll`.

## Quality bar (all enforced in CI)

| Check | Command |
| --- | --- |
| Tests + coverage ≥ 85% | `python -m pytest -q` |
| Lint | `ruff check .` (E,F,I,B,S,UP; line length 100) |
| Format | `ruff format --check .` |
| Types | `mypy forgefix` |
| Security | `bandit -r forgefix -lll -q` (0 high/medium) + `gitleaks detect --no-banner` |

New behavior needs tests. New rules need weights *and* tests that pin the exact score.

## Recording the demo GIF

The canonical recorder is [vhs](https://github.com/charmbracelet/vhs) (Charm), driven by
`demo/demo.tape`:

```bash
# macOS
brew install vhs ffmpeg
# Linux (Debian/Ubuntu)
sudo apt-get install -y ffmpeg
# Windows (winget)
winget install charmbracelet.vhs Gyan.FFmpeg
make gif            # writes demo/demo.gif, keep it under 3 MB
```

CI runs the same tape on `workflow_dispatch` (or when `demo/demo.tape` changes) and
commits the refreshed GIF back to `main`.

**Fallback when vhs is unavailable:** record an asciinema cast instead and attach it to
the PR — the tape commands are exactly the CLI session you would record:

```bash
pip install asciinema          # Linux/macOS only; Windows needs WSL
asciinema rec demo/demo.cast   # run: forgefix --help; forgefix doctor --path tests/fixtures/broken_repo
```

Commit `demo/demo.cast` (a few KB, reviewable text) and mention in the PR that the GIF
needs regeneration via the Demo GIF workflow.

## Pull request checklist

1. `make test lint type` pass locally.
2. Score-pinning tests updated if you touched weights.
3. CHANGELOG.md entry under `[Unreleased]`.
4. No secrets (gitleaks runs as a pre-commit hook — let it).

## Code of conduct

This project follows the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md).
