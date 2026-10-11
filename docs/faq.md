# FAQ

## Does ForgeFix execute code from the repos it scans?

No. `doctor`, `report`, and the HTTP API only read file names and text. Only
`forgefix up --apply` runs commands, and it runs **your project's own** standard
toolchain (venv, pip/npm/go, test runner) after showing you the dry-run plan.

## Will it modify my files?

Only with `up --apply`, and only by **creating missing** setup files (README skeleton,
SECURITY.md, .editorconfig, CI workflow). Existing files are never overwritten, and it
never generates a LICENSE for you.

## Why is my score different from a colleague's?

It should not be — the score is deterministic: fixed rule weights, no network, no
timestamps in the math. If scores differ, diff the `--json` output; a disabled rule or
a plugin is almost always the cause.

## Can I gate CI on it?

```yaml
- run: forgefix doctor --min-score 80
```

## How do I turn a rule off?

`.forgefix.yml`:

```yaml
disabled_rules: [demo]
```

## Does it work on non-Python repositories?

Yes. Scans are language-agnostic; bring-up detects python, node, and go today
(rust/java are on the roadmap).

## Is there a hosted version?

Not yet — the plan (free MIT CLI, paid hosted dashboard) is described in
[monetization](monetization.md). No billing code exists today.

## How does this relate to linters?

It does not replace them. Linters check code inside files; ForgeFix checks whether a
human can onboard into the repository at all.
