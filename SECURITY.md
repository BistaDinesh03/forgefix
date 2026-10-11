# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 0.1.x | ✔ |

## Reporting a vulnerability

Please report vulnerabilities **privately**: use GitHub's *Security → Report a
vulnerability* (private advisory) on this repository, or contact the maintainer
through the GitHub profile. Do **not** open a public issue for vulnerabilities.

- **Acknowledgement SLA: 48 hours** from report receipt.
- Target remediation: 7 days for high severity, 30 days for the rest, or a
  published mitigation/workaround.

## Threat model notes

- `forgefix doctor` / `forgefix report` / `forgefix serve?path=` are **read-only**:
  they read file names and text. They do not execute repository code and make no
  network requests.
- `forgefix up --apply` **does** execute project-defined commands (venv creation,
  the package manager's install, the test runner). Always review the dry-run
  (`forgefix up` without `--apply`) in repositories you do not trust.
- Repairs are create-if-missing. Existing files are never overwritten, and a
  LICENSE is never generated automatically.
- No `shell=True`, no `eval`: external commands are sanitized argument lists with
  full executable paths and bounded timeouts.
- `forgefix serve` binds `127.0.0.1` by default and scans the path given per
  request; do not expose it to untrusted networks.
- Dependency updates arrive weekly via Dependabot (pip + github-actions);
  `bandit`, `gitleaks`, and CodeQL run in CI.
