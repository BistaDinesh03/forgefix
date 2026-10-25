"""Generate missing setup files (SECURITY.md, CONTRIBUTING.md, .env.example, Dockerfile).

Everything here is deterministic and create-if-missing: the same repository
produces the same content, and an existing file is never overwritten. This
module only *builds* fixes; the caller decides whether to write them and
whether to ask for confirmation.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from forgefix.core.rules import DOCKER_FILES, SECURITY_NAMES

CONTRIBUTING_NAMES = (
    "CONTRIBUTING.md",
    "CONTRIBUTING.rst",
    "CONTRIBUTING.txt",
    ".github/CONTRIBUTING.md",
)
ENV_EXAMPLE_NAMES = (".env.example", ".env.sample", ".env.template")

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "htmlcov",
    "node_modules",
    "site-packages",
    "target",
    "venv",
    "vendor",
}
SCAN_SUFFIXES = {
    ".bash",
    ".cjs",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".mjs",
    ".php",
    ".py",
    ".pyi",
    ".rb",
    ".rs",
    ".sh",
    ".ts",
    ".tsx",
    ".zsh",
}
MAX_SCAN_BYTES = 1_000_000

ENV_PATTERNS = (
    re.compile(r"""os\.getenv\(\s*["']([A-Za-z_][A-Za-z0-9_]*)["']"""),
    re.compile(r"""os\.environ\.get\(\s*["']([A-Za-z_][A-Za-z0-9_]*)["']"""),
    re.compile(r"""os\.environ\[\s*["']([A-Za-z_][A-Za-z0-9_]*)["']\s*\]"""),
    re.compile(r"""os\.Getenv\(\s*["']([A-Za-z_][A-Za-z0-9_]*)["']"""),
    re.compile(r"""process\.env\.([A-Za-z_][A-Za-z0-9_]*)"""),
    re.compile(r"""process\.env\[\s*["']([A-Za-z_][A-Za-z0-9_]*)["']\s*\]"""),
)

SECURITY_TEMPLATE = """# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| latest | :white_check_mark: |

## Reporting a Vulnerability

Please do **not** open a public issue for security problems.

Report privately through GitHub Security Advisories:

    https://github.com/OWNER/REPO/security/advisories/new

If you cannot use advisories, email `security@example.com`.

We acknowledge reports within 48 hours and aim to publish a fix or mitigation
within 7 days for high-severity issues. Include reproduction steps, affected
versions, and any suggested fix.

## Scope

This policy covers the code in this repository. Third-party dependencies are
covered by their own security policies.
"""

CONTRIBUTING_TEMPLATE = """# Contributing to {name}

Thanks for taking the time to contribute.

## Before you start

- Search [existing issues](https://github.com/OWNER/REPO/issues) before opening a new one.
- For non-trivial changes, open an issue first so the approach can be agreed on.
- Never commit secrets, tokens, or personal data.

## Development setup

```bash
{install}
```

## Running tests

```bash
{test}
```

## Pull requests

- Keep each pull request focused on one change.
- Add or update tests for behavior changes.
- Update `CHANGELOG.md` when the change is user-visible.
- Describe what changed, why, and how you tested it.
- Make sure the test suite and linters pass before requesting review.

## Code style

- Run the project's linter and formatter before pushing.
- Keep public behavior documented in the README or docs.
- Prefer small, readable functions over clever one-liners.

## Reporting bugs

Include the version, operating system, a minimal reproduction, and the full
error output. Redact secrets before pasting logs.
"""

PYTHON_DOCKERFILE = """# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --create-home app

{install}

USER app

EXPOSE 8000

# TODO: replace `app` with the module that starts your application.
CMD ["python", "-m", "app"]
"""

NODE_DOCKERFILE = """# syntax=docker/dockerfile:1
FROM node:20-slim

ENV NODE_ENV=production

WORKDIR /app

COPY package*.json ./
RUN npm ci --omit=dev || npm install --omit=dev

COPY --chown=node:node . .

USER node

EXPOSE 3000

# TODO: make sure package.json defines a production `start` script.
CMD ["npm", "start"]
"""

GO_DOCKERFILE = """# syntax=docker/dockerfile:1
FROM golang:1.23-alpine AS build

WORKDIR /src

{copy_mod}
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/app .

FROM gcr.io/distroless/static-debian12:nonroot

COPY --from=build /out/app /app

USER nonroot:nonroot

EXPOSE 8080

ENTRYPOINT ["/app"]
"""

NONE_DOCKERFILE = """# syntax=docker/dockerfile:1
# TODO: replace this placeholder base image with the one your project needs.
FROM alpine:3.20

RUN adduser -D -H -s /sbin/nologin app

WORKDIR /app

USER app

CMD ["sh"]
"""


@dataclass(frozen=True)
class Fix:
    """One file that ForgeFix can create, with deterministic content."""

    kind: str
    label: str
    target: Path
    content: str


def _find_first(root: Path, names: Sequence[str]) -> Path | None:
    for name in names:
        candidate = root / name
        if candidate.exists():
            return candidate
    return None


def stack_commands(stack: str) -> tuple[str, str]:
    """Return the (install, test) commands shown in generated docs."""
    if stack == "python":
        return "pip install -e .", "pytest -q"
    if stack == "node":
        return "npm install", "npm test"
    if stack == "go":
        return "go mod download", "go test ./..."
    return (
        "# TODO: add the one-command install for this project",
        "# TODO: add the test command for this project",
    )


def render_contributing(name: str, stack: str) -> str:
    """Render CONTRIBUTING.md for ``name`` using the detected stack commands."""
    install, test = stack_commands(stack)
    return CONTRIBUTING_TEMPLATE.format(name=name, install=install, test=test)


def render_env_example(keys: Sequence[str]) -> str:
    """Render .env.example with every detected key commented out."""
    lines = [
        "# Copy this file to .env and fill in the values.",
        "# Generated by ForgeFix from environment-variable references in source.",
        "# Review before committing; never commit real secrets.",
        "",
    ]
    if keys:
        lines.extend(f"# {key}=" for key in keys)
    else:
        lines.append("# No environment variables were detected in source files.")
    return "\n".join(lines) + "\n"


def render_dockerfile(root: Path, stack: str) -> str:
    """Render a basic, non-root Dockerfile for the detected stack."""
    if stack == "python":
        if (root / "requirements.txt").is_file():
            install = (
                "COPY requirements.txt ./\n"
                "RUN pip install --no-cache-dir -r requirements.txt\n"
                "COPY --chown=app:app . ."
            )
        else:
            install = "COPY --chown=app:app . .\nRUN pip install --no-cache-dir ."
        return PYTHON_DOCKERFILE.format(install=install)
    if stack == "node":
        return NODE_DOCKERFILE
    if stack == "go":
        copy_mod = "COPY go.mod go.sum ./" if (root / "go.sum").is_file() else "COPY go.mod ./"
        return GO_DOCKERFILE.format(copy_mod=copy_mod)
    return NONE_DOCKERFILE


def _iter_source_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name for name in dirnames if name not in SKIP_DIRS and not name.startswith(".git")
        )
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            if path.suffix.lower() in SCAN_SUFFIXES and not filename.startswith(".env"):
                yield path


def scan_env_keys(root: Path) -> list[str]:
    """Find environment-variable names referenced by source files under ``root``."""
    keys: set[str] = set()
    for path in _iter_source_files(root):
        try:
            if path.stat().st_size > MAX_SCAN_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in ENV_PATTERNS:
            keys.update(pattern.findall(text))
    return sorted(keys, key=str.upper)


def plan_fixes(root: Path, stack: str) -> list[Fix]:
    """Build every missing setup file for ``root`` without touching the disk."""
    resolved = root.resolve()
    fixes: list[Fix] = []
    if _find_first(resolved, SECURITY_NAMES) is None:
        fixes.append(
            Fix(
                kind="security",
                label="create SECURITY.md",
                target=resolved / "SECURITY.md",
                content=SECURITY_TEMPLATE,
            )
        )
    if _find_first(resolved, CONTRIBUTING_NAMES) is None:
        fixes.append(
            Fix(
                kind="contributing",
                label="create CONTRIBUTING.md",
                target=resolved / "CONTRIBUTING.md",
                content=render_contributing(resolved.name or "project", stack),
            )
        )
    if _find_first(resolved, ENV_EXAMPLE_NAMES) is None:
        fixes.append(
            Fix(
                kind="env",
                label="create .env.example",
                target=resolved / ".env.example",
                content=render_env_example(scan_env_keys(resolved)),
            )
        )
    if _find_first(resolved, DOCKER_FILES) is None:
        fixes.append(
            Fix(
                kind="dockerfile",
                label="create Dockerfile",
                target=resolved / "Dockerfile",
                content=render_dockerfile(resolved, stack),
            )
        )
    return fixes
