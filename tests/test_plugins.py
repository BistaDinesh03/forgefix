"""Plugin loading tests: entry points, broken plugins, example check."""

from pathlib import Path

from forgefix.plugins import load_plugins
from forgefix.plugins.example import ExamplePlugin


class BrokenPlugin:
    name = "broken"

    def check(self, root: Path):  # type: ignore[no-untyped-def]
        raise RuntimeError("boom")


class NoCheck:
    name = "nocheck"


class FakeEntryPoint:
    def __init__(self, name: str, payload: object) -> None:  # type: ignore[no-untyped-def]
        self.name = name
        self._payload = payload

    def load(self) -> object:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_example_plugin_passes_with_editorconfig(tmp_path: Path) -> None:
    (tmp_path / ".editorconfig").write_text("root = true\n", encoding="utf-8")
    findings = ExamplePlugin().check(tmp_path)
    assert len(findings) == 1
    assert findings[0].status == "pass"
    assert findings[0].source == "plugin:example"
    assert findings[0].rule_id == "editorconfig"


def test_example_plugin_warns_without_editorconfig(tmp_path: Path) -> None:
    findings = ExamplePlugin().check(tmp_path)
    assert findings[0].status == "warn"
    assert findings[0].deduction == 1


def test_bundled_example_is_discoverable() -> None:
    assert "example" in [plugin.name for plugin in load_plugins()]


def test_broken_plugin_is_skipped_and_logged(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    entry_points = [
        FakeEntryPoint("broken", BrokenPlugin()),
        FakeEntryPoint("nocheck", NoCheck()),
        FakeEntryPoint("ok", ExamplePlugin()),
        FakeEntryPoint("explodes", RuntimeError("cannot import")),
    ]
    monkeypatch.setattr("forgefix.plugins._iter_entry_points", lambda: entry_points)
    plugins = load_plugins()
    # A plugin with the right shape is loaded even if its check() is broken;
    # the scanner isolates check() failures. Unloadable entry points are logged.
    assert [plugin.name for plugin in plugins] == ["broken", "example"]
    output = capsys.readouterr().out
    assert "failed to load plugin 'explodes'" in output


def test_entry_point_discovery_failure_is_graceful(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    def explode():  # type: ignore[no-untyped-def]
        raise RuntimeError("metadata unavailable")

    monkeypatch.setattr("forgefix.plugins.importlib.metadata.entry_points", explode)
    assert load_plugins() == []
    assert "entry-point discovery failed" in capsys.readouterr().out
