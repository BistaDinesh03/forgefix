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
make gif            # writes demo/demo.gif + demo/demo.mp4
```

CI runs the same tape on `workflow_dispatch` (or when the tape files change) and commits
the refreshed GIF and MP4 back to `main` via `PUSH_TOKEN`. The workflow fails if the GIF
is larger than 4 MB or smaller than 800 KB.

Notes that save re-recording time:

- `forgefix up --apply` streams its outcomes only when the whole plan finishes, so the
  tape waits out the full run (`Sleep 45s`). Expect a session of about 65 seconds.
- If your checkout lives inside a sync client (OneDrive, Dropbox), record from a plain
  copy of `demo/` + `tests/fixtures/` outside the sync root: sync engines can drop or
  relocate files that appear mid-recording, which leaves a half-repaired scratch repo.
  The CI recorder (a clean Linux checkout) is unaffected.

**Fallback when vhs is unavailable:** record an asciinema cast instead and attach it to
the PR — the tape commands are exactly the CLI session you would record:

```bash
pip install asciinema          # Linux/macOS only; Windows needs WSL
asciinema rec demo/demo.cast   # run: forgefix --help; forgefix doctor --path tests/fixtures/broken_repo
```

Commit `demo/demo.cast` (a few KB, reviewable text) and mention in the PR that the GIF
needs regeneration via the Demo GIF workflow.

## Visual identity

Colors, typography, and asset rules live in [assets/brand.md](assets/brand.md). Summary:

- Use the documented palette tokens only. Flat fills; no multi-stop gradients on the mark.
- No custom web fonts in docs or README — GitHub's rendered defaults only.
- Raster assets (`logo.png`, `social-preview.png`) are generated from the SVG geometry by
  `python assets/render_rasters.py`; edit the SVGs, then re-render.
- New docs and READMEs: no emoji headers, no ALL CAPS words, no marketing superlatives
  ("revolutionary", "blazing fast", "10x"). Short sentences, active voice, verifiable claims.

## Pull request checklist

1. `make test lint type` pass locally.
2. Score-pinning tests updated if you touched weights.
3. CHANGELOG.md entry under `[Unreleased]`.
4. No secrets (gitleaks runs as a pre-commit hook — let it).

## Code of conduct

This project follows the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md).
