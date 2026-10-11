"""Repository scanning: run every rule (and plugin) against a checkout.

All detectors read only file names and text content from the repository being
scanned. Nothing is downloaded, executed, or copied.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from forgefix.core.rules import (
    CI_FILES,
    DOCKER_FILES,
    GIF_SEARCH_DIRS,
    INSTALL_MARKERS,
    LICENSE_NAMES,
    LOCKFILE_NAMES,
    MANIFEST_NAMES,
    PYTHON_MANIFEST_NAMES,
    README_NAMES,
    RULES,
    SECURITY_NAMES,
    Finding,
    Rule,
    Status,
)
from forgefix.core.score import ScoreResult, score_findings

Detector = Callable[[Path], tuple[Status, str]]


def _find_named(root: Path, names: Sequence[str]) -> Path | None:
    for name in names:
        candidate = root / name
        if candidate.exists():
            return candidate
    return None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _detect_readme(root: Path) -> tuple[Status, str]:
    found = _find_named(root, README_NAMES)
    if found is None:
        return "fail", "no README at the repository root"
    return "pass", f"{found.name} found"


def _detect_install(root: Path) -> tuple[Status, str]:
    readme = _find_named(root, README_NAMES)
    if readme is None:
        return "fail", "cannot verify an install line without a README"
    text = _read_text(readme)
    for marker in INSTALL_MARKERS:
        if marker in text:
            return "pass", f"`{marker}` documented in README"
    return "warn", "README has no one-command install line"


def _detect_demo(root: Path) -> tuple[Status, str]:
    for directory in GIF_SEARCH_DIRS:
        base = root / directory if directory else root
        if base.is_dir():
            for gif in sorted(base.glob("*.gif")):
                return "pass", f"{gif.relative_to(root).as_posix()} found"
    readme = _find_named(root, README_NAMES)
    if readme is not None and ".gif" in _read_text(readme):
        return "fail", "README links a GIF that does not exist in the repository"
    return "warn", "no demo GIF found (demo/, docs/, assets/, or root)"


def _detect_lockfile(root: Path) -> tuple[Status, str]:
    found = _find_named(root, LOCKFILE_NAMES)
    if found is not None:
        return "pass", f"{found.name} found"
    if _find_named(root, MANIFEST_NAMES) is not None:
        return "warn", "dependency manifest present but no lockfile"
    return "skip", "no dependency manifest to lock"


def _detect_pinned(root: Path) -> tuple[Status, str]:
    if _find_named(root, LOCKFILE_NAMES) is not None:
        return "pass", "pins provided by the lockfile"
    requirements = root / "requirements.txt"
    if requirements.is_file():
        lines = [
            line.strip()
            for line in _read_text(requirements).splitlines()
            if line.strip() and not line.lstrip().startswith(("#", "-"))
        ]
        if not lines:
            return "skip", "requirements.txt is empty"
        unpinned = [
            line
            for line in lines
            if "==" not in line and not line.startswith(("git+", "http", "-e ", "."))
        ]
        if unpinned:
            return "warn", f"{len(unpinned)} unpinned requirement(s) in requirements.txt"
        return "pass", "every requirement is pinned with =="
    if _find_named(root, MANIFEST_NAMES) is not None:
        return "warn", "dependencies are declared but not pinned"
    return "skip", "no dependencies detected"


def _detect_devcontainer(root: Path) -> tuple[Status, str]:
    found = _find_named(root, DOCKER_FILES)
    if found is not None:
        return "pass", f"{found.name} found"
    if (root / ".devcontainer").is_dir():
        return "pass", ".devcontainer found"
    return "warn", "no Dockerfile or .devcontainer"


def _detect_ci(root: Path) -> tuple[Status, str]:
    workflows = root / ".github" / "workflows"
    if workflows.is_dir():
        count = len(list(workflows.glob("*.yml"))) + len(list(workflows.glob("*.yaml")))
        if count:
            return "pass", f"{count} GitHub workflow file(s) found"
    for name in CI_FILES[1:]:
        if (root / name).exists():
            return "pass", f"{name} found"
    return "fail", "no CI workflow found"


def _detect_security(root: Path) -> tuple[Status, str]:
    found = _find_named(root, SECURITY_NAMES)
    if found is None:
        return "fail", "no SECURITY.md"
    return "pass", f"{found.name} found"


def _detect_license(root: Path) -> tuple[Status, str]:
    found = _find_named(root, LICENSE_NAMES)
    if found is None:
        return "fail", "no LICENSE file"
    return "pass", f"{found.name} found"


def _detect_dev_env(root: Path) -> tuple[Status, str]:
    if _find_named(root, PYTHON_MANIFEST_NAMES) is None:
        return "skip", "not a Python project"
    if (root / ".venv").is_dir():
        return "pass", ".venv found"
    return "fail", "no .venv - run `forgefix up --apply`"


DETECTORS: dict[str, Detector] = {
    "readme": _detect_readme,
    "install": _detect_install,
    "demo": _detect_demo,
    "lockfile": _detect_lockfile,
    "pinned_deps": _detect_pinned,
    "devcontainer": _detect_devcontainer,
    "ci": _detect_ci,
    "security": _detect_security,
    "license": _detect_license,
    "dev_env": _detect_dev_env,
}


def make_finding(rule: Rule, root: Path) -> Finding:
    """Evaluate one rule against ``root`` and return its finding."""
    detector = DETECTORS.get(rule.id)
    if detector is None:
        status: Status = "skip"
        detail = "no detector registered"
    else:
        status, detail = detector(root)
    return Finding(
        rule_id=rule.id,
        category=rule.category,
        title=rule.title,
        status=status,
        detail=detail,
        suggestion=rule.suggestion,
        weight=rule.weight,
        warn_weight=rule.warn_weight,
        source="builtin",
    )


@dataclass(frozen=True)
class ScanResult:
    """Everything a report or API response needs about one repository."""

    root: Path
    findings: list[Finding]
    score: ScoreResult
    plugins: list[str]


def scan(
    root: Path | str,
    *,
    use_plugins: bool = True,
    disabled: Sequence[str] = (),
) -> ScanResult:
    """Scan ``root`` with every enabled rule plus discovered plugins."""
    resolved = Path(root).expanduser().resolve()
    if not resolved.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")
    disabled_ids = set(disabled)
    findings = [make_finding(rule, resolved) for rule in RULES if rule.id not in disabled_ids]
    plugin_names: list[str] = []
    if use_plugins:
        from forgefix.plugins import load_plugins

        for plugin in load_plugins():
            try:
                findings.extend(
                    finding
                    for finding in plugin.check(resolved)
                    if finding.rule_id not in disabled_ids
                )
            except Exception as exc:  # a broken plugin must never break the scan
                print(f"[forgefix] plugin '{plugin.name}' failed: {type(exc).__name__}")
                continue
            plugin_names.append(plugin.name)
    return ScanResult(
        root=resolved,
        findings=findings,
        score=score_findings(findings),
        plugins=plugin_names,
    )
