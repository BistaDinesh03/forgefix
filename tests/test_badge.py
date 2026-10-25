"""Tests for dynamic badge documents, URLs, and repository detection."""

import json
from pathlib import Path

from forgefix.core.badge import (
    BADGE_FILENAME,
    badge_color,
    badge_json,
    badge_markdown,
    badge_url,
    detect_repo_slug,
    parse_github_remote,
    write_badge,
)


def test_badge_url_shape() -> None:
    url = badge_url("acme", "demo")
    assert url == (
        "https://img.shields.io/endpoint?url="
        "https://raw.githubusercontent.com/acme/demo/main/.forgefix-badge.json"
    )


def test_badge_url_uses_branch_and_filename() -> None:
    url = badge_url("acme", "demo", branch="trunk", filename="health.json")
    assert "/trunk/health.json" in url


def test_badge_markdown_links_to_repository() -> None:
    markdown = badge_markdown("acme", "demo")
    assert markdown.startswith("[![ForgeFix health](https://img.shields.io/endpoint?url=")
    assert markdown.endswith("](https://github.com/acme/demo)")


def test_badge_payload_and_colors() -> None:
    payload = json.loads(badge_json(96))
    assert payload == {
        "schemaVersion": 1,
        "label": "ForgeFix",
        "message": "96/100",
        "color": "brightgreen",
    }
    assert badge_color(90) == "brightgreen"
    assert badge_color(80) == "green"
    assert badge_color(60) == "yellow"
    assert badge_color(40) == "orange"
    assert badge_color(39) == "red"
    assert json.loads(badge_json(120))["message"] == "100/100"
    assert json.loads(badge_json(-5))["message"] == "0/100"


def test_write_badge_creates_json(tmp_path: Path) -> None:
    target = write_badge(tmp_path, 91)
    assert target == tmp_path / BADGE_FILENAME
    text = target.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert json.loads(text)["message"] == "91/100"


def test_detect_repo_slug_from_environment(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("GITHUB_REPOSITORY", "acme/demo")
    assert detect_repo_slug(tmp_path) == ("acme", "demo")


def test_detect_repo_slug_from_git_config(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text(
        '[core]\n\tbare = false\n[remote "origin"]\n\turl = git@github.com:acme/demo.git\n',
        encoding="utf-8",
    )
    assert detect_repo_slug(tmp_path) == ("acme", "demo")


def test_detect_repo_slug_from_worktree_git_file(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    main = tmp_path / "main"
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    admin = main / ".git" / "worktrees" / "wt"
    admin.mkdir(parents=True)
    (admin / "commondir").write_text("../..", encoding="utf-8")
    (main / ".git" / "config").write_text(
        '[remote "origin"]\n\turl = https://github.com/acme/demo.git\n',
        encoding="utf-8",
    )
    (worktree / ".git").write_text(f"gitdir: {admin.as_posix()}\n", encoding="utf-8")
    assert detect_repo_slug(worktree) == ("acme", "demo")


def test_detect_repo_slug_without_remote(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    assert detect_repo_slug(tmp_path) is None


def test_parse_github_remote_variants() -> None:
    assert parse_github_remote("https://github.com/acme/demo.git") == ("acme", "demo")
    assert parse_github_remote("https://github.com/acme/demo") == ("acme", "demo")
    assert parse_github_remote("git@github.com:acme/demo.git") == ("acme", "demo")
    assert parse_github_remote("ssh://git@github.com/acme/demo.git") == ("acme", "demo")
    assert parse_github_remote("https://gitlab.com/acme/demo") is None
    assert parse_github_remote("not a url") is None
