"""Tests for stack detection, bring-up planning, and plan execution."""

import json
import shutil
import sys
from pathlib import Path

from forgefix.core.up import (
    CI_TEMPLATES,
    README_TEMPLATE,
    Outcome,
    Stack,
    Step,
    default_launcher,
    default_runner,
    detect_serve_command,
    detect_stack,
    execute_plan,
    plan_is_clean,
    plan_up,
)

FIXTURES = Path(__file__).parent / "fixtures"
BROKEN = FIXTURES / "broken_repo"


def fake_runner_factory(codes: list[int], outputs: list[str]):  # type: ignore[no-untyped-def]
    """Build a runner returning the given (code, output) pairs in order."""
    calls: list[tuple[str, ...]] = []

    def runner(argv: tuple[str, ...], cwd: Path) -> tuple[int, str]:
        calls.append(argv)
        index = len(calls) - 1
        return codes[index], outputs[index]

    runner.calls = calls  # type: ignore[attr-defined]
    return runner


def test_detect_stack_python() -> None:
    stack = detect_stack(BROKEN)
    assert stack.name == "python"
    assert stack.evidence == "pyproject.toml"


def test_detect_stack_node(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    assert detect_stack(tmp_path).name == "node"


def test_detect_stack_go(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example.com/x\n", encoding="utf-8")
    assert detect_stack(tmp_path).name == "go"


def test_detect_stack_none(tmp_path: Path) -> None:
    stack = detect_stack(tmp_path)
    assert stack.name == "none"
    assert "no dependency manifest" in stack.evidence


def test_plan_up_python_order(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(BROKEN, repo)
    steps = plan_up(repo, serve=False)
    assert [step.kind for step in steps[:4]] == ["repair"] * 4
    labels = [step.label for step in steps]
    assert "create README.md skeleton" in labels
    assert any("virtual environment" in label for label in labels)
    assert any("requirements.lock" in label for label in labels)
    assert any("test suite" in label for label in labels)
    assert all(step.kind != "serve" for step in steps)


def test_plan_up_respects_existing_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(BROKEN, repo)
    (repo / "README.md").write_text("# already here\n", encoding="utf-8")
    (repo / "SECURITY.md").write_text("# security\n", encoding="utf-8")
    labels = [step.label for step in plan_up(repo, serve=False)]
    assert "create README.md skeleton" not in labels
    assert "create SECURITY.md" not in labels
    assert "create .editorconfig" in labels


def test_plan_up_includes_serve_when_configured(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text(
        '[tool.forgefix]\nserve = ["python", "--version"]\n', encoding="utf-8"
    )
    kinds = [step.kind for step in plan_up(repo, serve=True)]
    assert kinds[-1] == "serve"
    assert all(step.kind != "serve" for step in plan_up(repo, serve=False))


def test_plan_up_none_stack_plans_nothing(tmp_path: Path) -> None:
    steps = plan_up(tmp_path, serve=False)
    assert any(step.kind == "run" and not step.argv for step in steps)


def test_execute_repairs_create_then_skip(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    steps = [
        Step(kind="repair", label="create README", target=target, content="# hi\n"),
        Step(kind="repair", label="create README again", target=target, content="# hi\n"),
    ]
    outcomes = execute_plan(tmp_path, steps)
    assert [outcome.status for outcome in outcomes] == ["done", "skipped"]
    assert target.read_text(encoding="utf-8") == "# hi\n"
    assert "already exists" in outcomes[1].detail


def test_execute_repair_without_target_fails(tmp_path: Path) -> None:
    outcomes = execute_plan(tmp_path, [Step(kind="repair", label="broken repair")])
    assert outcomes[0].status == "failed"
    assert "no target" in outcomes[0].detail


def test_execute_fails_fast_on_nonzero_exit(tmp_path: Path) -> None:
    runner = fake_runner_factory([0, 1, 0], ["fine", "boom output", "never"])
    steps = [
        Step(kind="run", label="first", argv=(sys.executable, "-c", "pass")),
        Step(kind="run", label="second", argv=(sys.executable, "-c", "pass")),
        Step(kind="run", label="third", argv=(sys.executable, "-c", "pass")),
    ]
    outcomes = execute_plan(tmp_path, steps, runner=runner)  # type: ignore[arg-type]
    assert [outcome.status for outcome in outcomes] == ["done", "failed"]
    assert "boom output" in outcomes[1].detail
    assert len(runner.calls) == 2  # type: ignore[attr-defined]


def test_execute_freeze_writes_full_output(tmp_path: Path) -> None:
    runner = fake_runner_factory([0], ["pkg-a==1.0\npkg-b==2.0\n"])
    target = tmp_path / "requirements.lock"
    step = Step(
        kind="freeze", label="freeze", argv=("python", "-m", "pip", "freeze"), target=target
    )
    outcomes = execute_plan(tmp_path, [step], runner=runner)  # type: ignore[arg-type]
    assert outcomes[0].status == "done"
    assert target.read_text(encoding="utf-8") == "pkg-a==1.0\npkg-b==2.0\n"


def test_execute_skips_unknown_executable(tmp_path: Path) -> None:
    step = Step(kind="run", label="missing tool", argv=("no-such-binary-xyz", "--version"))
    outcomes = execute_plan(tmp_path, [step])
    assert outcomes[0].status == "skipped"
    assert "not found on PATH" in outcomes[0].detail


def test_execute_skips_empty_argv(tmp_path: Path) -> None:
    outcomes = execute_plan(tmp_path, [Step(kind="run", label="noop")])
    assert outcomes[0].status == "skipped"


def test_execute_serve_uses_launcher(tmp_path: Path) -> None:
    def launcher(argv: tuple[str, ...], cwd: Path) -> int:
        return 4242

    step = Step(kind="serve", label="serve", argv=("python", "--version"))
    outcomes = execute_plan(tmp_path, [step], launcher=launcher)
    assert outcomes[0].status == "done"
    assert "4242" in outcomes[0].detail


def test_execute_serve_failure_breaks(tmp_path: Path) -> None:
    def launcher(argv: tuple[str, ...], cwd: Path) -> int:
        raise OSError("address in use")

    step = Step(kind="serve", label="serve", argv=("python", "--version"))
    outcomes = execute_plan(tmp_path, [step], launcher=launcher)
    assert outcomes[0].status == "failed"


def test_default_runner_success_and_failure() -> None:
    code, output = default_runner((sys.executable, "-c", "print('hello-forgefix')"), Path.cwd())
    assert code == 0
    assert "hello-forgefix" in output
    code, _ = default_runner((sys.executable, "-c", "import sys; sys.exit(3)"), Path.cwd())
    assert code == 3


def test_default_runner_survives_bad_executable() -> None:
    code, output = default_runner(("no-such-binary-forgefix",), Path.cwd())
    assert code == 1
    assert output


def test_default_launcher_returns_pid() -> None:
    pid = default_launcher((sys.executable, "-c", "pass"), Path.cwd())
    assert pid > 0


def test_detect_serve_node(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr("forgefix.core.up._resolve_exe", lambda name: f"/usr/bin/{name}")
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"dev": "vite"}}), encoding="utf-8"
    )
    stack = detect_stack(tmp_path)
    assert detect_serve_command(tmp_path, stack) == ("/usr/bin/npm", "run", "dev")


def test_detect_serve_node_invalid_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{nope", encoding="utf-8")
    assert detect_serve_command(tmp_path, detect_stack(tmp_path)) is None


def test_detect_serve_node_without_dev_script(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(json.dumps({"scripts": {}}), encoding="utf-8")
    assert detect_serve_command(tmp_path, detect_stack(tmp_path)) is None


def test_detect_serve_python_with_config(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr("forgefix.core.up._resolve_exe", lambda name: None)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.forgefix]\nserve = ["python", "--version"]\n', encoding="utf-8"
    )
    assert detect_serve_command(tmp_path, detect_stack(tmp_path)) == ("python", "--version")


def test_detect_serve_python_invalid_toml(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[[[broken", encoding="utf-8")
    assert detect_serve_command(tmp_path, detect_stack(tmp_path)) is None


def test_detect_serve_python_without_pyproject(tmp_path: Path) -> None:
    stack = Stack("python", "requirements.txt")
    assert detect_serve_command(tmp_path, stack) is None


def test_detect_serve_go(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr("forgefix.core.up._resolve_exe", lambda name: f"/usr/bin/{name}")
    (tmp_path / "go.mod").write_text("module x\n", encoding="utf-8")
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
    assert detect_serve_command(tmp_path, detect_stack(tmp_path)) == ("/usr/bin/go", "run", ".")
    (tmp_path / "main.go").unlink()
    assert detect_serve_command(tmp_path, detect_stack(tmp_path)) is None


def test_plan_is_clean_logic() -> None:
    assert plan_is_clean([Outcome("a", "done"), Outcome("b", "skipped")])
    assert not plan_is_clean([Outcome("a", "done"), Outcome("b", "failed")])


def test_templates_are_original_and_specific() -> None:
    readme = README_TEMPLATE.format(name="demo", install="pip install -e .", test="pytest -q")
    assert "# demo" in readme
    assert "pip install -e ." in readme
    assert "TODO" in readme
    assert set(CI_TEMPLATES) == {"python", "node", "go", "none"}
    assert "actions/checkout@v4" in CI_TEMPLATES["python"]
