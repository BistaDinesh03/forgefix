"""Rule definitions and finding types for ForgeFix health checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Status = Literal["pass", "warn", "fail", "skip"]

# File-name vocabulary shared by the scanner and the bring-up repairer.
README_NAMES = ("README.md", "README.markdown", "README.rst", "README.txt", "README")
LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING", "COPYING.md")
SECURITY_NAMES = ("SECURITY.md", "SECURITY.txt", ".github/SECURITY.md")
CHANGELOG_NAMES = (
    "CHANGELOG.md",
    "CHANGELOG.markdown",
    "CHANGELOG.rst",
    "CHANGELOG.txt",
    "CHANGELOG",
    "CHANGES.md",
    "CHANGES",
    "HISTORY.md",
    "HISTORY",
)
LOCKFILE_NAMES = (
    "requirements.lock",
    "poetry.lock",
    "uv.lock",
    "Pipfile.lock",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "go.sum",
    "Cargo.lock",
)
MANIFEST_NAMES = (
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "package.json",
    "go.mod",
    "Cargo.toml",
)
PYTHON_MANIFEST_NAMES = ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt")
DOCKER_FILES = ("Dockerfile", "Containerfile", "docker-compose.yml", "docker-compose.yaml")
CI_FILES = (
    ".github/workflows",
    ".gitlab-ci.yml",
    ".circleci/config.yml",
    "azure-pipelines.yml",
    "Jenkinsfile",
    ".travis.yml",
)
GIF_SEARCH_DIRS = ("", "demo", "docs", "assets", "images", ".github")
INSTALL_MARKERS = (
    "pip install",
    "pip3 install",
    "uv sync",
    "npm install",
    "npm ci",
    "yarn add",
    "pnpm install",
    "go install",
    "cargo install",
    "make setup",
    "docker compose up",
    "docker run ",
)


@dataclass(frozen=True)
class Rule:
    """One health check: identity, scoring weights, and remediation hint."""

    id: str
    category: str
    title: str
    weight: int
    warn_weight: int
    suggestion: str


@dataclass(frozen=True)
class Finding:
    """The result of evaluating one rule against a repository."""

    rule_id: str
    category: str
    title: str
    status: Status
    detail: str
    suggestion: str
    weight: int
    warn_weight: int
    source: str = "builtin"

    @property
    def deduction(self) -> int:
        """Points removed from 100 for this finding (0 for pass/skip)."""
        if self.status == "fail":
            return self.weight
        if self.status == "warn":
            return self.warn_weight
        return 0


RULES: tuple[Rule, ...] = (
    Rule(
        "readme",
        "docs",
        "README present",
        12,
        6,
        "Add a README.md with a one-line pitch and a getting-started section.",
    ),
    Rule(
        "install",
        "docs",
        "One-command install line",
        8,
        4,
        "Add a copy-pasteable install command (pip install / npm install / make setup).",
    ),
    Rule(
        "demo",
        "docs",
        "Demo GIF or screenshot",
        3,
        2,
        "Record a short demo GIF (see CONTRIBUTING.md) and link it at the top of the README.",
    ),
    Rule(
        "changelog",
        "docs",
        "Changelog present",
        3,
        2,
        "Add a CHANGELOG.md (Keep a Changelog style is fine) so users see what changed "
        "between releases.",
    ),
    Rule(
        "lockfile",
        "deps",
        "Dependency lockfile",
        6,
        3,
        "Commit a lockfile (requirements.lock, poetry.lock, package-lock.json, go.sum).",
    ),
    Rule(
        "pinned_deps",
        "deps",
        "Pinned dependency versions",
        5,
        2,
        "Pin dependency versions with ==, or rely on a committed lockfile.",
    ),
    Rule(
        "devcontainer",
        "automation",
        "Dockerfile or devcontainer",
        4,
        1,
        "Add a Dockerfile or .devcontainer so contributors start from a known environment.",
    ),
    Rule(
        "ci",
        "automation",
        "CI workflow",
        8,
        6,
        "Add a CI workflow under .github/workflows/ that runs lint and tests.",
    ),
    Rule(
        "security",
        "security",
        "Security policy",
        8,
        4,
        "Add SECURITY.md describing how to report vulnerabilities (48h ack SLA).",
    ),
    Rule(
        "license",
        "legal",
        "Open-source license",
        6,
        3,
        "Add a LICENSE file so others know how they may use the code.",
    ),
    Rule(
        "dev_env",
        "environment",
        "Ready dev environment",
        7,
        3,
        "Run `forgefix up --apply` to create .venv and install dependencies.",
    ),
)

RULES_BY_ID: dict[str, Rule] = {rule.id: rule for rule in RULES}
