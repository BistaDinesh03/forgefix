# Product Hunt draft

**Tagline:** One command to set up, health-check, and repair any open-source project.

**Description:**

ForgeFix turns "can a human actually onboard into this repository?" into a deterministic
0–100 score — and then fixes what's missing.

- **Doctor:** README, one-command install line, lockfile, pinned deps, CI, security
  policy, LICENSE, dev environment — pass/warn/fail with concrete fixes. `--json`,
  `--min-score` for CI gates.
- **Up:** dry-run by default; `--apply` repairs missing setup files (create-only, never
  overwrites), creates the venv, installs deps, writes a lockfile, runs the tests.
- **Report & API:** markdown report plus a FastAPI server (`/health`, `/doctor`,
  `/report`) for dashboards.
- **Plugins:** custom checks via the `forgefix.plugins` entry-point group.

Built for maintainers who keep answering the same setup questions, and for newcomers who
just want the thing to run. Original code, MIT licensed, read-only scans, no telemetry.

**First comment:**

Hi! I'm the maintainer. ForgeFix started because I typed "how do I run this?" in issue
threads one too many times. Everything you see in the demo is a real CLI session — the
GIF is generated from a scripted tape that runs the actual commands against a fixture
repo (42/100 before, 91/100 after one `forgefix up --apply`).

Honest limitations: bring-up currently detects python/node/go; the hosted dashboard is a
documented plan, not a product — the CLI is the whole product today. Would love your
feedback on the weights and which checks deserve to exist. MIT, PRs welcome:
https://github.com/BistaDinesh03/forgefix
