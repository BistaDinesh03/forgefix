"""End-to-end CLI tests via Typer's CliRunner."""

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from forgefix import __version__
from forgefix.cli import app
from forgefix.core.up import Outcome, Step

runner = CliRunner()
FIXTURES = Path(__file__).parent / "fixtures"
BROKEN = FIXTURES / "broken_repo"
MINIMAL = FIXTURES / "minimal_repo"


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"forgefix {__version__}" in result.stdout


def test_help_lists_every_command() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("init", "doctor", "report", "up", "serve", "cloud", "badge", "share"):
        assert command in result.stdout


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code == 2  # click treats bare invocation as a usage error
    assert "Usage" in result.stdout


def test_init_creates_config_and_keeps_existing(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / ".forgefix.yml").is_file()
    second = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert "kept existing" in second.stdout


def test_init_on_a_file_errors(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    target.write_text("x", encoding="utf-8")
    result = runner.invoke(app, ["init", "--path", str(target)])
    assert result.exit_code == 2


def test_doctor_broken_repo_prints_score_38() -> None:
    result = runner.invoke(app, ["doctor", "--path", str(BROKEN)])
    assert result.exit_code == 0
    assert "Health score: 38/100" in result.stdout
    assert "README present" in result.stdout
    assert "FAIL" in result.stdout
    assert "Top fixes:" in result.stdout


def test_doctor_minimal_repo_is_perfect() -> None:
    result = runner.invoke(app, ["doctor", "--path", str(MINIMAL)])
    assert result.exit_code == 0
    assert "Health score: 100/100" in result.stdout


def test_doctor_json_output() -> None:
    result = runner.invoke(app, ["doctor", "--path", str(BROKEN), "--json"])
    payload = json.loads(result.stdout)
    assert payload["score"]["total"] == 38
    assert payload["plugins"] == ["example"]
    assert len(payload["findings"]) == 14
    assert payload["score"]["top_fixes"]


def test_doctor_min_score_exits_2() -> None:
    result = runner.invoke(app, ["doctor", "--path", str(BROKEN), "--min-score", "80"])
    assert result.exit_code == 2


def test_doctor_min_score_satisfied() -> None:
    result = runner.invoke(app, ["doctor", "--path", str(BROKEN), "--min-score", "30"])
    assert result.exit_code == 0


def test_doctor_missing_path_errors() -> None:
    result = runner.invoke(app, ["doctor", "--path", "no-such-directory-xyz"])
    assert result.exit_code == 2


def test_doctor_uses_config_min_score(tmp_path: Path) -> None:
    (tmp_path / ".forgefix.yml").write_text("min_score: 90\n", encoding="utf-8")
    result = runner.invoke(app, ["doctor", "--path", str(tmp_path)])
    assert result.exit_code == 2
    override = runner.invoke(app, ["doctor", "--path", str(tmp_path), "--min-score", "0"])
    assert override.exit_code == 0


def test_doctor_respects_disabled_rules(tmp_path: Path) -> None:
    (tmp_path / ".forgefix.yml").write_text("disabled_rules: [readme]\n", encoding="utf-8")
    result = runner.invoke(app, ["doctor", "--path", str(tmp_path), "--json"])
    ids = [finding["rule_id"] for finding in json.loads(result.stdout)["findings"]]
    assert "readme" not in ids


def test_report_writes_default_path(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["report", "--path", str(BROKEN)])
    assert result.exit_code == 0
    content = (tmp_path / "reports" / "forgefix-report.md").read_text(encoding="utf-8")
    assert "# ForgeFix health report" in content
    assert "38/100" in content
    assert "Top fixes" in content


def test_report_custom_output(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "report.md"
    result = runner.invoke(app, ["report", "--path", str(MINIMAL), "--output", str(target)])
    assert result.exit_code == 0
    assert target.is_file()
    assert "100/100" in target.read_text(encoding="utf-8")


def test_up_dry_run_touches_nothing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(BROKEN, repo)
    result = runner.invoke(app, ["up", "--path", str(repo)])
    assert result.exit_code == 0
    assert "stack: python (pyproject.toml)" in result.stdout
    assert "[dry-run]" in result.stdout
    assert not (repo / "README.md").exists()
    assert not (repo / ".venv").exists()


def test_up_apply_reports_outcomes(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    repo = tmp_path / "repo"
    repo.mkdir()
    captured: dict[str, object] = {}

    def fake_execute(root, steps, *, runner=None, launcher=None):  # type: ignore[no-untyped-def]
        captured["root"] = root
        captured["steps"] = steps
        return [
            Outcome("create README.md skeleton", "done", "created README.md"),
            Outcome("install dependencies", "done", "ok"),
        ]

    monkeypatch.setattr("forgefix.cli.execute_plan", fake_execute)
    result = runner.invoke(app, ["up", "--path", str(repo), "--apply"])
    assert result.exit_code == 0
    assert "[ok] create README.md skeleton - created README.md" in result.stdout
    assert "[forgefix] bring-up complete" in result.stdout
    assert captured["steps"]


def test_up_apply_failure_exits_1(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    repo = tmp_path / "repo"
    repo.mkdir()

    def fake_execute(root, steps, *, runner=None, launcher=None):  # type: ignore[no-untyped-def]
        return [Outcome("install dependencies", "failed", "boom\nline two")]

    monkeypatch.setattr("forgefix.cli.execute_plan", fake_execute)
    result = runner.invoke(app, ["up", "--path", str(repo), "--apply"])
    assert result.exit_code == 1
    assert "[fail] install dependencies" in result.stdout
    assert "boom" in result.stdout


def test_serve_starts_uvicorn(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import uvicorn

    calls: dict[str, object] = {}

    def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        calls["args"] = args
        calls["kwargs"] = kwargs

    monkeypatch.setattr(uvicorn, "run", fake_run)
    result = runner.invoke(app, ["serve", "--port", "8123"])
    assert result.exit_code == 0
    assert calls["kwargs"]["port"] == 8123
    assert "http://127.0.0.1:8123" in result.stdout


def test_cloud_stub_message() -> None:
    result = runner.invoke(app, ["cloud"])
    assert result.exit_code == 0
    assert "Hosted version coming soon - see docs/monetization.md" in result.stdout


def test_badge_prints_endpoint_url(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("GITHUB_REPOSITORY", "acme/demo")
    result = runner.invoke(app, ["badge", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "img.shields.io/endpoint" in result.stdout
    assert "raw.githubusercontent.com/acme/demo/main/.forgefix-badge.json" in result.stdout
    assert "[![ForgeFix health]" in result.stdout


def test_badge_write_creates_json(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("GITHUB_REPOSITORY", "acme/demo")
    result = runner.invoke(app, ["badge", "--path", str(tmp_path), "--write"])
    assert result.exit_code == 0
    target = tmp_path / ".forgefix-badge.json"
    assert target.is_file()
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["schemaVersion"] == 1
    assert payload["message"].endswith("/100")
    assert "wrote .forgefix-badge.json" in result.stdout


def test_badge_without_remote_exits_2(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    result = runner.invoke(app, ["badge", "--path", str(tmp_path)])
    assert result.exit_code == 2
    assert "could not detect a GitHub remote" in result.output


def test_badge_rejects_partial_owner_repo(tmp_path: Path) -> None:
    result = runner.invoke(app, ["badge", "--path", str(tmp_path), "--owner", "acme"])
    assert result.exit_code == 2
    assert "pass both --owner and --repo" in result.output


def test_badge_accepts_explicit_owner_repo(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["badge", "--path", str(tmp_path), "--owner", "acme", "--repo", "demo"]
    )
    assert result.exit_code == 0
    assert "raw.githubusercontent.com/acme/demo/main/.forgefix-badge.json" in result.stdout


def test_up_badge_writes_during_dry_run(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    result = runner.invoke(app, ["up", "--path", str(repo), "--badge"])
    assert result.exit_code == 0
    assert (repo / ".forgefix-badge.json").is_file()
    assert not (repo / "README.md").exists()
    assert "[dry-run]" in result.stdout


def test_up_apply_accepts_yes(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    repo = tmp_path / "repo"
    repo.mkdir()

    def fake_execute(root, steps, *, runner=None, launcher=None):  # type: ignore[no-untyped-def]
        return [Outcome("install dependencies", "done", "ok")]

    monkeypatch.setattr("forgefix.cli.execute_plan", fake_execute)
    result = runner.invoke(app, ["up", "--path", str(repo), "--apply", "--yes"])
    assert result.exit_code == 0
    assert "[forgefix] bring-up complete" in result.stdout
    assert "[ok] install dependencies" in result.stdout


def test_up_apply_prompts_and_can_skip_files(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    repo = tmp_path / "repo"
    repo.mkdir()
    captured: dict[str, list[Step]] = {}

    def fake_execute(root, steps, *, runner=None, launcher=None):  # type: ignore[no-untyped-def]
        captured["steps"] = list(steps)
        return []

    monkeypatch.setattr("forgefix.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("forgefix.cli.typer.confirm", lambda *args, **kwargs: False)
    monkeypatch.setattr("forgefix.cli.execute_plan", fake_execute)
    result = runner.invoke(app, ["up", "--path", str(repo), "--apply"])
    assert result.exit_code == 0
    assert all(step.kind != "repair" for step in captured["steps"])
    assert "skipped generated files" in result.stdout


def test_up_badge_refreshes_after_apply(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    repo = tmp_path / "repo"
    repo.mkdir()

    def fake_execute(root, steps, *, runner=None, launcher=None):  # type: ignore[no-untyped-def]
        (root / "SECURITY.md").write_text("# Security\n", encoding="utf-8")
        return [Outcome("create SECURITY.md", "done", "created")]

    monkeypatch.setattr("forgefix.cli.execute_plan", fake_execute)
    result = runner.invoke(app, ["up", "--path", str(repo), "--apply", "--yes", "--badge"])
    assert result.exit_code == 0
    assert (repo / ".forgefix-badge.json").is_file()
    assert "wrote .forgefix-badge.json" in result.stdout


def test_share_prints_panel(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("GITHUB_REPOSITORY", "acme/demo")
    (tmp_path / "demo").mkdir()
    (tmp_path / "demo" / "demo.gif").write_bytes(b"GIF89a")
    result = runner.invoke(app, ["share", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "pip install forgefix" in result.stdout
    assert "Setup Health" in result.stdout
    assert "acme/demo" in result.stdout
    assert "demo/demo.gif" in result.stdout


def test_share_without_remote_still_prints(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    result = runner.invoke(app, ["share", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "pip install forgefix" in result.stdout


def test_init_does_not_rewrite_tuned_config(tmp_path: Path) -> None:
    custom = tmp_path / ".forgefix.yml"
    body = "report_path: reports/custom.md\ndisabled_rules: [demo]\nmin_score: 55\n"
    custom.write_text(body, encoding="utf-8")
    result = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "kept existing .forgefix.yml" in result.stdout
    assert custom.read_text(encoding="utf-8") == body
