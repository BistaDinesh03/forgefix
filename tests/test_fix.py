"""Tests for create-if-missing file generation in core/fix.py."""

from pathlib import Path

from forgefix.core.fix import (
    plan_fixes,
    render_contributing,
    render_dockerfile,
    render_env_example,
    scan_env_keys,
    stack_commands,
)


def test_scan_env_keys_python_and_node(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "import os\n"
        'a = os.getenv("DATABASE_URL")\n'
        'b = os.environ.get("API_KEY")\n'
        'c = os.environ["SECRET_TOKEN"]\n',
        encoding="utf-8",
    )
    (tmp_path / "ui.ts").write_text(
        'const a = process.env.NEXT_PUBLIC_URL;\nconst b = process.env["PORT"];\n',
        encoding="utf-8",
    )
    assert scan_env_keys(tmp_path) == [
        "API_KEY",
        "DATABASE_URL",
        "NEXT_PUBLIC_URL",
        "PORT",
        "SECRET_TOKEN",
    ]


def test_scan_env_keys_skips_vendored_and_secret_files(tmp_path: Path) -> None:
    vendored = tmp_path / "node_modules" / "pkg"
    vendored.mkdir(parents=True)
    (vendored / "index.js").write_text("process.env.IGNORED", encoding="utf-8")
    (tmp_path / ".env").write_text("SHOULD_NOT_APPEAR=1\n", encoding="utf-8")
    (tmp_path / "app.js").write_text("process.env.KEEP", encoding="utf-8")
    assert scan_env_keys(tmp_path) == ["KEEP"]


def test_scan_env_keys_deduplicates(tmp_path: Path) -> None:
    (tmp_path / "one.py").write_text('os.getenv("SHARED")', encoding="utf-8")
    (tmp_path / "two.py").write_text('os.environ["SHARED"]', encoding="utf-8")
    assert scan_env_keys(tmp_path) == ["SHARED"]


def test_render_env_example_comments_keys() -> None:
    text = render_env_example(["A_KEY", "B_KEY"])
    assert "# A_KEY=" in text
    assert "# B_KEY=" in text
    assert not any(line.startswith("A_KEY=") for line in text.splitlines())


def test_render_env_example_without_keys() -> None:
    text = render_env_example([])
    assert "No environment variables were detected" in text
    assert text.endswith("\n")


def test_plan_fixes_generates_all_missing(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text('import os\nTOKEN = os.getenv("TOKEN")\n', encoding="utf-8")
    fixes = plan_fixes(tmp_path, "python")
    assert {fix.kind for fix in fixes} == {"security", "contributing", "env", "dockerfile"}
    env_fix = next(fix for fix in fixes if fix.kind == "env")
    assert "# TOKEN=" in env_fix.content
    security = next(fix for fix in fixes if fix.kind == "security")
    assert "OWNER/REPO" in security.content
    assert "security@example.com" in security.content
    contributing = next(fix for fix in fixes if fix.kind == "contributing")
    assert "pip install -e ." in contributing.content
    assert "pytest -q" in contributing.content
    assert all(fix.target.parent == tmp_path for fix in fixes)


def test_plan_fixes_respects_existing_files(tmp_path: Path) -> None:
    for name in ("SECURITY.md", "CONTRIBUTING.md", ".env.example", "compose.yml"):
        (tmp_path / name).write_text("x", encoding="utf-8")
    # Docker-compose counts as a container definition for the devcontainer rule.
    (tmp_path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    assert plan_fixes(tmp_path, "python") == []


def test_plan_fixes_respects_nested_security_policy(tmp_path: Path) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    (github / "SECURITY.md").write_text("# security\n", encoding="utf-8")
    kinds = {fix.kind for fix in plan_fixes(tmp_path, "python")}
    assert "security" not in kinds


def test_render_dockerfile_python_with_requirements(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("flask\n", encoding="utf-8")
    text = render_dockerfile(tmp_path, "python")
    assert "FROM python:3.12-slim" in text
    assert "pip install --no-cache-dir -r requirements.txt" in text
    assert "USER app" in text
    assert "CMD" in text


def test_render_dockerfile_python_without_requirements(tmp_path: Path) -> None:
    text = render_dockerfile(tmp_path, "python")
    assert "pip install --no-cache-dir ." in text
    assert "COPY --chown=app:app . ." in text


def test_render_dockerfile_node_go_and_unknown(tmp_path: Path) -> None:
    node = render_dockerfile(tmp_path, "node")
    assert "FROM node:20-slim" in node
    assert "USER node" in node
    go = render_dockerfile(tmp_path, "go")
    assert "golang:1.23-alpine" in go
    assert "USER nonroot:nonroot" in go
    unknown = render_dockerfile(tmp_path, "none")
    assert "FROM alpine:3.20" in unknown
    assert "USER app" in unknown


def test_render_dockerfile_go_copies_go_sum_when_present(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example.com/demo\n", encoding="utf-8")
    (tmp_path / "go.sum").write_text("", encoding="utf-8")
    text = render_dockerfile(tmp_path, "go")
    assert "COPY go.mod go.sum ./" in text


def test_render_contributing_uses_stack_commands() -> None:
    text = render_contributing("demo", "node")
    assert "# Contributing to demo" in text
    assert "npm install" in text
    assert "npm test" in text
    assert "CHANGELOG.md" in text


def test_stack_commands_unknown_stack() -> None:
    install, test = stack_commands("rust")
    assert "TODO" in install
    assert "TODO" in test
