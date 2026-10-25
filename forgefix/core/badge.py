"""Dynamic Shields.io endpoint badges.

The badge is a tiny JSON document committed to the repository; Shields reads it
through raw.githubusercontent.com. Keeping the document in git means the badge
has no server, no token, and no runtime dependency.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

BADGE_FILENAME = ".forgefix-badge.json"
DEFAULT_BRANCH = "main"

_GITHUB_URL = re.compile(
    r"github\.com[/:](?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


def parse_github_remote(url: str) -> tuple[str, str] | None:
    """Parse an HTTPS, SSH, or scp-style GitHub remote into ``(owner, repo)``."""
    cleaned = url.strip().rstrip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    match = _GITHUB_URL.search(cleaned)
    if match is None:
        return None
    owner, repo = match.group("owner"), match.group("repo")
    if not owner or not repo:
        return None
    return owner, repo


def _git_config_file(root: Path) -> Path | None:
    dot_git = root / ".git"
    git_dir = dot_git
    if dot_git.is_file():
        try:
            marker = dot_git.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            return None
        if not marker.startswith("gitdir:"):
            return None
        git_dir = Path(marker.split(":", 1)[1].strip())
        if not git_dir.is_absolute():
            git_dir = (root / git_dir).resolve()
        common = git_dir / "commondir"
        if common.is_file():
            try:
                git_dir = (git_dir / common.read_text(encoding="utf-8").strip()).resolve()
            except OSError:
                return None
    config = git_dir / "config"
    return config if config.is_file() else None


def _slug_from_git_config(config: Path) -> tuple[str, str] | None:
    try:
        lines = config.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    in_origin = False
    for raw in lines:
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            in_origin = line == '[remote "origin"]'
            continue
        if in_origin and line.startswith("url") and "=" in line:
            return parse_github_remote(line.split("=", 1)[1].strip())
    return None


def detect_repo_slug(root: Path) -> tuple[str, str] | None:
    """Find ``(owner, repo)`` from ``GITHUB_REPOSITORY`` or the origin remote."""
    env_slug = os.environ.get("GITHUB_REPOSITORY", "").strip()
    parts = env_slug.split("/")
    if len(parts) == 2 and all(parts):
        return parts[0], parts[1]
    config = _git_config_file(root)
    if config is None:
        return None
    return _slug_from_git_config(config)


def badge_color(score: int) -> str:
    """Map a 0-100 health score to a Shields color name."""
    if score >= 90:
        return "brightgreen"
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    if score >= 40:
        return "orange"
    return "red"


def badge_payload(score: int) -> dict[str, str | int]:
    """Build the Shields endpoint document for ``score``."""
    clamped = max(0, min(100, int(score)))
    return {
        "schemaVersion": 1,
        "label": "ForgeFix",
        "message": f"{clamped}/100",
        "color": badge_color(clamped),
    }


def badge_json(score: int) -> str:
    """Serialize the endpoint document exactly as it is committed."""
    return json.dumps(badge_payload(score), indent=2) + "\n"


def write_badge(root: Path, score: int, *, filename: str = BADGE_FILENAME) -> Path:
    """Write (or refresh) the badge document and return its path."""
    target = root / filename
    target.write_text(badge_json(score), encoding="utf-8", newline="\n")
    return target


def badge_url(
    owner: str,
    repo: str,
    *,
    branch: str = DEFAULT_BRANCH,
    filename: str = BADGE_FILENAME,
) -> str:
    """Return the Shields endpoint URL for a committed badge document."""
    raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filename}"
    return f"https://img.shields.io/endpoint?url={raw}"


def badge_markdown(
    owner: str,
    repo: str,
    *,
    branch: str = DEFAULT_BRANCH,
    filename: str = BADGE_FILENAME,
) -> str:
    """Return a README-ready markdown badge linked to the repository."""
    url = badge_url(owner, repo, branch=branch, filename=filename)
    return f"[![ForgeFix health]({url})](https://github.com/{owner}/{repo})"
