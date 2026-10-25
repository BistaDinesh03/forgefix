# GitHub Action and live badge

The official ForgeFix action scores every pull request, comments when setup
health regresses, and refreshes a Shields.io badge on `main`. It is a composite
action: no Docker image, no server, and no secrets beyond `GITHUB_TOKEN`.

## Quick start

Copy this workflow to `.github/workflows/forgefix.yml`:

```yaml
name: ForgeFix

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: write       # needed only for the badge commit on main
  pull-requests: write  # needed to comment on pull requests

jobs:
  forgefix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - name: Run ForgeFix
        uses: BistaDinesh03/forgefix/.github/actions/forgefix@v0.3.0
        with:
          threshold: "80"
          update-badge: ${{ github.event_name == 'push' }}
```

The same workflow is checked in at
[`.github/workflows/forgefix-example.yml`](https://github.com/BistaDinesh03/forgefix/blob/main/.github/workflows/forgefix-example.yml)
for the ForgeFix repository itself. Because that copy runs from the same
checkout, it uses the local action and `install: source`.

## What the action does

1. Installs ForgeFix (from PyPI by default).
2. Runs `forgefix doctor --json` on the checkout and exposes the score.
3. On a pull request, checks out the base branch in a temporary worktree and
   scores it too.
4. Creates or updates one pull-request comment when the score is below
   `threshold` or lower than the base branch. The comment has a hidden marker,
   so a re-run updates the existing comment instead of spamming the thread.
5. On `main`, optionally writes `.forgefix-badge.json` and commits it if the
   document changed.

The regression comment looks like:

> ⚠️ ForgeFix Health Score dropped to 78/100. Run `forgefix doctor` locally to see how to fix it.
>
> **Base:** 82/100 → **This PR:** 78/100 (-4)
>
> **Top fixes:**
> - **CI workflow** (-8): Add a CI workflow under `.github/workflows/` that runs lint and tests.

## Inputs

| Input | Default | Description |
| --- | --- | --- |
| `path` | `.` | Repository path to scan. |
| `threshold` | `80` | Minimum acceptable score. |
| `github-token` | `${{ github.token }}` | Token used for the comment. |
| `comment` | `true` | Set to `false` to score without commenting. |
| `base-ref` | PR base branch | Branch used for the regression comparison. |
| `update-badge` | `false` | Commit `.forgefix-badge.json` on `main`. |
| `install` | `pypi` | Use `source` to install the action's checkout. |
| `version` | latest | Pin a ForgeFix version from PyPI. |

## Outputs

| Output | Description |
| --- | --- |
| `score` | Health score for the checked-out revision. |
| `base_score` | Health score for the base branch, or empty when unavailable. |

```yaml
- uses: BistaDinesh03/forgefix/.github/actions/forgefix@v0.3.0
  id: forgefix
- run: echo "score=${{ steps.forgefix.outputs.score }}"
```

## Permissions and forks

- Same-repository pull requests can be commented on with
  `pull-requests: write`.
- Pull requests from forks receive a read-only `GITHUB_TOKEN` on the
  `pull_request` event. The action skips the comment on those runs instead of
  failing. If you need comments on fork PRs, use a separate
  `pull_request_target` workflow that does **not** check out or execute the
  fork's code.
- The badge commit needs `contents: write` and branch protection that allows
  the bot to push to `main`. The commit message includes `[skip ci]` so the
  badge update does not trigger another run.

## Dynamic badge

Write the endpoint document locally:

```bash
forgefix badge --write
```

`forgefix up --badge` writes the same file as part of a bring-up (including a
dry-run, because the badge is metadata rather than a repair). The document looks
like:

```json
{
  "schemaVersion": 1,
  "label": "ForgeFix",
  "message": "96/100",
  "color": "brightgreen"
}
```

Commit it, then copy the URL printed by:

```bash
forgefix badge
```

The URL points at
`raw.githubusercontent.com/<owner>/<repo>/main/.forgefix-badge.json`; Shields
renders it as a live badge:

```markdown
[![ForgeFix health](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/OWNER/REPO/main/.forgefix-badge.json)](https://github.com/OWNER/REPO)
```

Use `--branch` when the badge document lives on a branch other than `main`.
Use `--owner` and `--repo` when there is no GitHub `origin` remote (for example
in a CI checkout with a stripped `.git` directory).

## Local check

```bash
pip install -e .
forgefix doctor --path . --min-score 80
forgefix badge --write
```
