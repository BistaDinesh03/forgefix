"""Example ForgeFix plugin: adds an .editorconfig consistency check."""

from __future__ import annotations

from pathlib import Path

from forgefix.core.rules import Finding


class ExamplePlugin:
    """Bundled example plugin registered under the ``forgefix.plugins`` group."""

    name = "example"

    def check(self, root: Path) -> list[Finding]:
        """Report whether the repository ships an .editorconfig."""
        present = (root / ".editorconfig").is_file()
        return [
            Finding(
                rule_id="editorconfig",
                category="polish",
                title="EditorConfig present",
                status="pass" if present else "warn",
                detail=(
                    ".editorconfig found"
                    if present
                    else "no .editorconfig (indentation and charset may drift between editors)"
                ),
                suggestion=(
                    "Add an .editorconfig with basic indentation, charset, and newline rules."
                ),
                weight=3,
                warn_weight=1,
                source="plugin:example",
            )
        ]
