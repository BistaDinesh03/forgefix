# X/Twitter thread draft (3 tweets)

**Tweet 1 (hook):**

Every new repo wastes your first hour: guess the install, find no lockfile, hunt for the
test runner.

ForgeFix fixes that in one command — a deterministic health score + repair for any
open-source project.

MIT. Original code. Demo 🧵

**Tweet 2 (demo):**

`forgefix doctor` → 42/100 on a bare repo, with the exact fixes.
`forgefix up --apply` → repairs missing setup files, creates venv, installs deps, writes
a lockfile, runs tests.
`forgefix doctor` again → 91/100.

Read-only scans. Dry-run by default. Never overwrites files.

Demo GIF: https://github.com/BistaDinesh03/forgefix#demo

**Tweet 3 (CTA):**

Plugins via the `forgefix.plugins` entry-point group.

Security isn't an afterthought: no shell=True, no eval, sanitized argv + timeouts, bandit
+ gitleaks + CodeQL in CI, 48h vuln ack SLA.

Try it + tell me which checks to add:
https://github.com/BistaDinesh03/forgefix
