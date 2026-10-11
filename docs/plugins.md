# Plugins

ForgeFix discovers checks from the `forgefix.plugins` entry-point group. A plugin can
never break a scan: load failures and `check()` exceptions are logged and skipped.

## Contract

A plugin is any object with:

- `name: str`
- `check(root: Path) -> Sequence[Finding]`

```python
from pathlib import Path

from forgefix.core.rules import Finding


class NoSwearingPlugin:
    name = "no-swearing"

    def check(self, root: Path) -> list[Finding]:
        readme = root / "README.md"
        ok = readme.is_file() and "TODO" not in readme.read_text(encoding="utf-8")
        return [
            Finding(
                rule_id="readme_quality",
                category="docs",
                title="README has no leftover TODOs",
                status="pass" if ok else "warn",
                detail="clean" if ok else "README still contains TODO markers",
                suggestion="Finish the TODO sections before announcing the project.",
                weight=3,
                warn_weight=1,
                source="plugin:no-swearing",
            )
        ]
```

## Registering

In the plugin's `pyproject.toml`:

```toml
[project.entry-points."forgefix.plugins"]
no-swearing = "my_package.plugin:NoSwearingPlugin"
```

Findings follow the same scoring rules as builtin checks: `weight` is deducted on
`fail`, `warn_weight` on `warn`, nothing on `pass`/`skip`.

## The bundled example

`forgefix/plugins/example.py` adds an `.editorconfig` check and is registered under the
same group, so the example doubles as a working integration test of the plugin path.

## Tips

- Keep plugins **read-only**; they run inside every scan.
- Pin your own weights in tests so your score stays deterministic.
- Return `Finding(...)` objects, not raw dicts — the report/API layers rely on them.
