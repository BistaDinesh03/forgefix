"""Repository scanner tests against fixtures and synthetic repos."""

from pathlib import Path

import pytest

from forgefix.core.rules import RULES
from forgefix.core.scanner import scan

FIXTURES = Path(__file__).parent / "fixtures"
BROKEN = FIXTURES / "broken_repo"
MINIMAL = FIXTURES / "minimal_repo"


def status_map(result) -> dict[str, str]:  # type: ignore[no-untyped-def]
    return {finding.rule_id: finding.status for finding in result.findings}


def test_broken_repo_scores_exactly_40() -> None:
    result = scan(BROKEN)
    assert result.score.total == 40
    assert result.score.failed == 6
    assert result.score.warned == 6


def test_broken_repo_statuses() -> None:
    assert status_map(scan(BROKEN)) == {
        "readme": "fail",
        "install": "fail",
        "demo": "warn",
        "changelog": "warn",
        "lockfile": "warn",
        "pinned_deps": "warn",
        "devcontainer": "warn",
        "ci": "fail",
        "security": "fail",
        "license": "fail",
        "dev_env": "fail",
        "editorconfig": "warn",
    }


def test_minimal_repo_scores_100() -> None:
    result = scan(MINIMAL)
    assert result.score.total == 100
    assert status_map(result)["dev_env"] == "skip"
    assert result.plugins == ["example"]


def test_every_builtin_rule_has_a_detector() -> None:
    from forgefix.core.scanner import DETECTORS

    assert {rule.id for rule in RULES} == set(DETECTORS)


def test_scan_missing_path_raises(tmp_path: Path) -> None:
    with pytest.raises(NotADirectoryError):
        scan(tmp_path / "definitely-missing-dir")


def test_disabled_rules_are_excluded() -> None:
    result = scan(BROKEN, disabled={"readme", "editorconfig"})
    ids = {finding.rule_id for finding in result.findings}
    assert "readme" not in ids
    assert "editorconfig" not in ids
    assert len(ids) == len(RULES) - 1  # ten builtin rules remain, plugin excluded


def test_plugins_can_be_disabled() -> None:
    result = scan(BROKEN, use_plugins=False)
    assert result.plugins == []
    assert all(finding.source == "builtin" for finding in result.findings)


def test_readme_referencing_missing_gif_fails(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# x\n\n![demo](docs/missing.gif)\n", encoding="utf-8")
    demo = next(f for f in scan(tmp_path, use_plugins=False).findings if f.rule_id == "demo")
    assert demo.status == "fail"


def test_pinned_requirements_pass(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.32.0\nflask==3.0.0\n", encoding="utf-8")
    result = scan(tmp_path, use_plugins=False)
    assert status_map(result)["pinned_deps"] == "pass"
    assert status_map(result)["lockfile"] == "warn"


def test_unpinned_requirements_warn(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests\nflask\n", encoding="utf-8")
    pinned = next(
        f for f in scan(tmp_path, use_plugins=False).findings if f.rule_id == "pinned_deps"
    )
    assert pinned.status == "warn"
    assert "2 unpinned" in pinned.detail


def test_comment_only_requirements_skip(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("# nothing here\n", encoding="utf-8")
    pinned = next(
        f for f in scan(tmp_path, use_plugins=False).findings if f.rule_id == "pinned_deps"
    )
    assert pinned.status == "skip"


def test_empty_repo_skips_dependency_rules(tmp_path: Path) -> None:
    result = scan(tmp_path, use_plugins=False)
    table = status_map(result)
    assert table["lockfile"] == "skip"
    assert table["pinned_deps"] == "skip"
    assert table["dev_env"] == "skip"


def test_gitlab_ci_counts_as_ci(tmp_path: Path) -> None:
    (tmp_path / ".gitlab-ci.yml").write_text("test: {}\n", encoding="utf-8")
    assert status_map(scan(tmp_path, use_plugins=False))["ci"] == "pass"


def test_devcontainer_directory_passes(tmp_path: Path) -> None:
    (tmp_path / ".devcontainer").mkdir()
    assert status_map(scan(tmp_path, use_plugins=False))["devcontainer"] == "pass"


def test_security_md_inside_dot_github_passes(tmp_path: Path) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    (github / "SECURITY.md").write_text("# security\n", encoding="utf-8")
    assert status_map(scan(tmp_path, use_plugins=False))["security"] == "pass"


def test_changelog_name_variants_pass(tmp_path: Path) -> None:
    for name in ("CHANGELOG.md", "CHANGELOG", "HISTORY.md"):
        repo = tmp_path / name.replace(".", "_")
        repo.mkdir()
        (repo / name).write_text("# changes\n", encoding="utf-8")
        assert status_map(scan(repo, use_plugins=False))["changelog"] == "pass"


def test_missing_changelog_warns(tmp_path: Path) -> None:
    finding = next(
        f for f in scan(tmp_path, use_plugins=False).findings if f.rule_id == "changelog"
    )
    assert finding.status == "warn"


def test_copying_license_passes(tmp_path: Path) -> None:
    (tmp_path / "COPYING.md").write_text("license text\n", encoding="utf-8")
    assert status_map(scan(tmp_path, use_plugins=False))["license"] == "pass"


def test_readme_rst_with_install_line(tmp_path: Path) -> None:
    (tmp_path / "README.rst").write_text("x\n\n``pip install demo``\n", encoding="utf-8")
    table = status_map(scan(tmp_path, use_plugins=False))
    assert table["readme"] == "pass"
    assert table["install"] == "pass"


def test_readme_without_install_line_warns(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# x\n\nNo instructions yet.\n", encoding="utf-8")
    install = next(f for f in scan(tmp_path, use_plugins=False).findings if f.rule_id == "install")
    assert install.status == "warn"


def test_python_project_without_venv_fails_dev_env(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n", encoding="utf-8")
    assert status_map(scan(tmp_path, use_plugins=False))["dev_env"] == "fail"


def test_python_project_with_venv_passes_dev_env(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\nversion='0'\n", encoding="utf-8")
    (tmp_path / ".venv").mkdir()
    assert status_map(scan(tmp_path, use_plugins=False))["dev_env"] == "pass"


def test_scan_reports_resolved_root(tmp_path: Path) -> None:
    result = scan(tmp_path)
    assert result.root == tmp_path.resolve()


def test_broken_plugin_check_is_isolated(monkeypatch, capsys) -> None:  # type: ignore[no-untyped-def]
    class Exploding:
        name = "exploding"

        def check(self, root: Path):  # type: ignore[no-untyped-def]
            raise RuntimeError("plugin bug")

    monkeypatch.setattr("forgefix.plugins.load_plugins", lambda: [Exploding()])
    result = scan(MINIMAL)
    assert result.plugins == []
    assert result.score.total == 100
    assert "plugin 'exploding' failed: RuntimeError" in capsys.readouterr().out


def test_scan_findings_match_rule_suggestions() -> None:
    result = scan(BROKEN, use_plugins=False)
    for finding in result.findings:
        assert finding.suggestion  # every builtin finding carries a fix hint
