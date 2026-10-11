# Reddit drafts

Rules: no cross-posting spam, one post per subreddit, plain language, disclose it's your
project.

## r/opensource

**Title:** I built ForgeFix: a deterministic health check + one-command bring-up for any
open-source repo (MIT, original code)

**Body:**

Maintainers kept answering the same questions in my issues: how do I install this? where's
the lockfile? how do I run tests? So I wrote a CLI that answers them for everyone, before
they ask:

`forgefix doctor` scores a repo 0–100 across README, install line, lockfile, pinned deps,
CI, security policy, LICENSE, and dev environment — with concrete fixes. `forgefix up
--apply` repairs what's missing (create-only, never overwrites) and does the actual
bring-up. On the included broken fixture: 42/100 -> 91/100 with tests passing.

It's MIT, the code is original, and scans are read-only (metadata only, no network, no
code execution). Plugins load via a standard entry-point group.

Would love feedback: which checks would you add/remove? Weights are deterministic and
pinned by tests, so changing them is a deliberate PR.

https://github.com/BistaDinesh03/forgefix

## r/devops

**Title:** ForgeFix: a CLI + HTTP API that gates on "can a human actually onboard into
this repo?"

**Body:**

Think of it as a health check one layer above linters — repository onboarding instead of
files: lockfile present? pinned deps? CI? SECURITY.md with an ack SLA? one-command
install? Ready dev environment?

```bash
forgefix doctor --min-score 80   # CI gate, exit 2 below threshold
forgefix serve                   # /health /doctor /report JSON for dashboards
```

Deterministic scoring (unit-tested weights), `--json` output, plugin system for custom
checks. `up --apply` does bring-up (venv, deps, lockfile via pip freeze, tests) and only
creates missing files. MIT, original code, bandit + gitleaks + CodeQL in CI.

https://github.com/BistaDinesh03/forgefix

## r/Python

**Title:** ForgeFix — Typer + FastAPI CLI that scores a Python repo's onboarding health
(0–100) and can repair it

**Body:**

Built with Typer + Rich, pydantic config, FastAPI server, pytest with a coverage gate
(96%, fail-under 85), mypy + ruff clean. The scoring is the fun part: every rule has fixed
fail/warn weights, so the same repo always scores the same — tests pin the exact numbers
(fixtures score exactly 42 and 100).

`forgefix up --apply` on a bare project: creates README/SECURITY/.editorconfig/CI
skeletons (create-if-missing only), `python -m venv`, `pip install -e .`, `pip freeze >
requirements.lock`, runs pytest. Plugin checks via the `forgefix.plugins` entry-point
group.

https://github.com/BistaDinesh03/forgefix
