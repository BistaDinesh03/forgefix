"""Plugin discovery via the ``forgefix.plugins`` entry-point group.

A plugin is any object with a ``name`` attribute and a
``check(root: Path) -> list[Finding]`` method. ForgeFix itself ships an
example plugin registered under this group in ``pyproject.toml``.
"""

from __future__ import annotations

import importlib.metadata
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, cast

from forgefix.core.rules import Finding

ENTRY_POINT_GROUP = "forgefix.plugins"


class ForgeFixPlugin(Protocol):
    """Contract every ForgeFix plugin must satisfy."""

    name: str

    def check(self, root: Path) -> Sequence[Finding]:
        """Inspect ``root`` and return zero or more findings."""
        ...


def _iter_entry_points() -> list[importlib.metadata.EntryPoint]:
    try:
        entry_points = importlib.metadata.entry_points()
    except Exception as exc:  # pragma: no cover - extremely defensive
        print(f"[forgefix] entry-point discovery failed: {type(exc).__name__}")
        return []
    if hasattr(entry_points, "select"):
        return list(entry_points.select(group=ENTRY_POINT_GROUP))
    legacy = cast("dict[str, list[importlib.metadata.EntryPoint]]", entry_points)
    return list(legacy.get(ENTRY_POINT_GROUP, []))  # pragma: no cover - legacy API


def load_plugins() -> list[ForgeFixPlugin]:
    """Load every importable plugin; a broken plugin never breaks the scan."""
    plugins: list[ForgeFixPlugin] = []
    for entry_point in _iter_entry_points():
        try:
            loaded = entry_point.load()
            plugin = loaded() if isinstance(loaded, type) else loaded
            if hasattr(plugin, "name") and hasattr(plugin, "check"):
                plugins.append(cast("ForgeFixPlugin", plugin))
        except Exception as exc:
            print(f"[forgefix] failed to load plugin '{entry_point.name}': {type(exc).__name__}")
    return sorted(plugins, key=lambda plugin: plugin.name)
