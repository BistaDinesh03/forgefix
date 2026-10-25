"""Social-proof text for ``forgefix share``."""

from __future__ import annotations

from pathlib import Path

from forgefix.core.rules import GIF_SEARCH_DIRS

SHARE_TEXT = (
    "My repo just scored a {score}/100 on Setup Health with ForgeFix! 🛠️ "
    "Check yours: pip install forgefix"
)


def find_demo_gif(root: Path) -> Path | None:
    """Return the first demo GIF in the conventional ForgeFix locations."""
    for directory in GIF_SEARCH_DIRS:
        base = root / directory if directory else root
        if base.is_dir():
            for gif in sorted(base.glob("*.gif")):
                return gif
    return None


def build_share_text(
    score: int,
    repo_url: str | None = None,
    gif_url: str | None = None,
) -> str:
    """Build a ready-to-post update with the required ForgeFix sentence."""
    lines = [SHARE_TEXT.format(score=score)]
    if repo_url:
        lines += ["", f"Repo: {repo_url}"]
    if gif_url:
        lines.append(f"Demo: {gif_url}")
    return "\n".join(lines)
