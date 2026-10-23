"""Stack detection and one-command bring-up (plan, dry-run, apply).

``plan_up`` only *describes* what would happen; nothing touches the repository
until ``execute_plan`` runs. Repairs are create-if-missing: existing files are
never modified or overwritten, and a LICENSE is never invented for anyone.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # noqa: S404 - list-argv, shell=False, bounded timeouts only # nosec B404
import sys
import tomllib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from forgefix.core.rules import (
    PYTHON_MANIFEST_NAMES,
    README_NAMES,
    SECURITY_NAMES,
)

RUN_TIMEOUT_SECONDS = 600

# Steps report (argv, cwd) -> (returncode, tail of combined output).
Runner = Callable[[tuple[str, ...], Path], tuple[int, str]]
# Serve steps report (argv, cwd) -> pid.
Launcher = Callable[[tuple[str, ...], Path], int]


@dataclass(frozen=True)
class Stack:
    """Detected project stack plus the evidence that decided it."""

    name: str
    evidence: str


@dataclass(frozen=True)
class Step:
    """One unit of work in a bring-up plan."""

    kind: str  # "repair" | "run" | "freeze" | "serve"
    label: str
    argv: tuple[str, ...] = ()
    content: str = ""
    target: Path | None = None


@dataclass(frozen=True)
class Outcome:
    """What actually happened to a step during ``execute_plan``."""

    label: str
    status: str  # "done" | "skipped" | "failed"
    detail: str = ""


README_TEMPLATE = """# {name}

> TODO: one-line pitch for this project.

## Getting started

```bash
{install}
```

## Development

```bash
{test}
```
"""

SECURITY_TEMPLATE = """# Security policy

## Reporting a vulnerability

Please open a private security advisory on the repository (or email the
maintainers) instead of a public issue. We acknowledge reports within 48 hours
and aim to ship a fix or mitigation within 7 days for high-severity issues.
"""

EDITORCONFIG_TEMPLATE = """root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 4

[*.{yml,yaml,json,md}]
indent_size = 2
"""

CI_TEMPLATES = {
    "python": """name: CI
on:
  push:
    branches: [main]
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e . pytest
      - run: pytest -q
""",
    "node": """name: CI
on:
  push:
    branches: [main]
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci || npm install
      - run: npm test
""",
    "go": """name: CI
on:
  push:
    branches: [main]
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: "stable"
      - run: go test ./...
""",
    "none": """name: CI
on:
  push:
    branches: [main]
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Add your build and test commands here"
""",
}


def detect_stack(root: Path) -> Stack:
    """Detect the project stack from dependency manifests (first match wins)."""
    for name in PYTHON_MANIFEST_NAMES:
        if (root / name).exists():
            return Stack("python", name)
    if (root / "package.json").exists():
        return Stack("node", "package.json")
    if (root / "go.mod").exists():
        return Stack("go", "go.mod")
    return Stack("none", "no dependency manifest found")


def _readme_install_command(stack: Stack) -> str:
    if stack.name == "python":
        return "pip install -e ."
    if stack.name == "node":
        return "npm install"
    if stack.name == "go":
        return "go mod download"
    return "# TODO: add the one-command install for this project"


def _readme_test_command(stack: Stack) -> str:
    if stack.name == "python":
        return "pytest -q"
    if stack.name == "node":
        return "npm test"
    if stack.name == "go":
        return "go test ./..."
    return "# TODO: add the test command for this project"


def _venv_python(root: Path) -> Path:
    if os.name == "nt":  # pragma: no cover - exercised only on Windows CI
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


def _resolve_exe(name: str) -> str | None:
    """Resolve an executable to a full path, or None when it is unavailable."""
    if Path(name).is_absolute():
        return name if Path(name).exists() else None
    return shutil.which(name)


def _tail(text: str, lines: int = 12) -> str:
    parts = [line for line in text.splitlines() if line.strip()]
    return "\n".join(parts[-lines:])


def default_runner(argv: tuple[str, ...], cwd: Path) -> tuple[int, str]:
    """Run argv in cwd with no shell, capture output, bounded timeout."""
    try:
        completed = subprocess.run(  # noqa: S603 # nosec B603 - sanitized list argv, shell=False
            list(argv),
            cwd=cwd,
            shell=False,  # noqa: S602 - explicitly never a shell
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, f"{type(exc).__name__}: {exc}"
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, output


def default_launcher(argv: tuple[str, ...], cwd: Path) -> int:
    """Start a detached dev server and return its pid."""
    process = subprocess.Popen(  # noqa: S603 # nosec B603 - sanitized list argv, shell=False
        list(argv),
        cwd=cwd,
        shell=False,  # noqa: S602 - explicitly never a shell
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )
    return process.pid


def detect_serve_command(root: Path, stack: Stack) -> tuple[str, ...] | None:
    """Find a dev-server command when it is unambiguous, else None."""
    if stack.name == "node":
        package = root / "package.json"
        try:
            data = json.loads(package.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            return None
        scripts = data.get("scripts") if isinstance(data, dict) else None
        if isinstance(scripts, dict) and isinstance(scripts.get("dev"), str):
            npm = _resolve_exe("npm")
            if npm:
                return (npm, "run", "dev")
        return None
    if stack.name == "python":
        pyproject = root / "pyproject.toml"
        if not pyproject.is_file():
            return None
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8", errors="replace"))
        except (OSError, tomllib.TOMLDecodeError):
            return None
        serve = data.get("tool", {}).get("forgefix", {}).get("serve")
        if isinstance(serve, list) and all(isinstance(item, str) for item in serve):
            resolved = tuple(_resolve_exe(item) or item for item in serve)
            if resolved:
                return resolved
        return None
    if stack.name == "go" and (root / "main.go").is_file():
        go = _resolve_exe("go")
        if go:
            return (go, "run", ".")
    return None


def _repair_steps(root: Path, stack: Stack) -> list[Step]:
    """Create-if-missing setup files: README, SECURITY.md, .editorconfig, CI."""
    steps: list[Step] = []
    name = root.name or "project"
    if _find_first(root, README_NAMES) is None:
        steps.append(
            Step(
                kind="repair",
                label="create README.md skeleton",
                target=root / "README.md",
                content=README_TEMPLATE.format(
                    name=name,
                    install=_readme_install_command(stack),
                    test=_readme_test_command(stack),
                ),
            )
        )
    if _find_first(root, SECURITY_NAMES) is None:
        steps.append(
            Step(
                kind="repair",
                label="create SECURITY.md",
                target=root / "SECURITY.md",
                content=SECURITY_TEMPLATE,
            )
        )
    if not (root / ".editorconfig").exists():
        steps.append(
            Step(
                kind="repair",
                label="create .editorconfig",
                target=root / ".editorconfig",
                content=EDITORCONFIG_TEMPLATE,
            )
        )
    workflows = root / ".github" / "workflows"
    if not workflows.is_dir() and not any(
        (root / name).exists() for name in (".gitlab-ci.yml", ".circleci", "Jenkinsfile")
    ):
        steps.append(
            Step(
                kind="repair",
                label="create .github/workflows/ci.yml",
                target=workflows / "ci.yml",
                content=CI_TEMPLATES[stack.name],
            )
        )
    return steps


def _find_first(root: Path, names: Sequence[str]) -> Path | None:
    for name in names:
        candidate = root / name
        if candidate.exists():
            return candidate
    return None


def plan_up(root: Path, *, serve: bool = True) -> list[Step]:
    """Build the ordered bring-up plan: repairs -> env -> deps -> lock -> tests -> serve."""
    stack = detect_stack(root)
    steps = _repair_steps(root, stack)

    if stack.name == "python":
        venv_python = _venv_python(root)
        steps.append(
            Step(
                kind="run",
                label="create virtual environment (.venv)",
                argv=(sys.executable, "-m", "venv", ".venv"),
            )
        )
        install: list[str] = [str(venv_python), "-m", "pip", "install", "-e", "."]
        if (root / "tests").is_dir() or list(root.glob("test_*.py")):
            install.append("pytest")
        steps.append(Step(kind="run", label="install dependencies", argv=tuple(install)))
        steps.append(
            Step(
                kind="freeze",
                label="write requirements.lock (pip freeze)",
                argv=(str(venv_python), "-m", "pip", "freeze", "--all"),
                target=root / "requirements.lock",
            )
        )
        if (root / "tests").is_dir() or list(root.glob("test_*.py")):
            steps.append(
                Step(
                    kind="run",
                    label="run test suite",
                    argv=(str(venv_python), "-m", "pytest", "-q"),
                )
            )
    elif stack.name == "node":
        npm = _resolve_exe("npm")
        if npm:
            lock = root / "package-lock.json"
            install_cmd = "ci" if lock.is_file() else "install"
            steps.append(
                Step(
                    kind="run",
                    label=f"install dependencies (npm {install_cmd})",
                    argv=(npm, install_cmd),
                )
            )
            steps.append(Step(kind="run", label="run test suite", argv=(npm, "test")))
        else:
            steps.append(
                Step(
                    kind="run",
                    label="install dependencies (npm not found)",
                    argv=("npm", "install"),
                )
            )
    elif stack.name == "go":
        go = _resolve_exe("go")
        if go:
            steps.append(Step(kind="run", label="download modules", argv=(go, "mod", "download")))
            steps.append(Step(kind="run", label="run test suite", argv=(go, "test", "./...")))
        else:
            steps.append(
                Step(
                    kind="run",
                    label="download modules (go not found)",
                    argv=("go", "mod", "download"),
                )
            )
    else:
        steps.append(
            Step(
                kind="run",
                label="no stack detected - nothing to install",
                argv=(),
            )
        )

    if serve:
        serve_argv = detect_serve_command(root, stack)
        if serve_argv:
            steps.append(
                Step(kind="serve", label=f"start dev server: {serve_argv[0]}", argv=serve_argv)
            )
    return steps


def _is_docker_step(argv: Sequence[str]) -> bool:
    if not argv:
        return False
    name = Path(argv[0]).name.lower()
    return name in {"docker", "docker.exe", "podman", "podman.exe"}


def execute_plan(
    root: Path,
    steps: Sequence[Step],
    *,
    runner: Runner | None = None,
    launcher: Launcher | None = None,
) -> list[Outcome]:
    """Apply a plan. Repairs never overwrite; run steps fail fast."""
    run = runner or default_runner
    launch = launcher or default_launcher
    outcomes: list[Outcome] = []

    for step in steps:
        if step.kind == "repair":
            if step.target is None:
                outcomes.append(Outcome(step.label, "failed", "repair has no target"))
                break
            if step.target.exists():
                outcomes.append(
                    Outcome(step.label, "skipped", f"{step.target.name} already exists")
                )
                continue
            step.target.parent.mkdir(parents=True, exist_ok=True)
            step.target.write_text(step.content, encoding="utf-8", newline="\n")
            outcomes.append(Outcome(step.label, "done", f"created {step.target.name}"))
            continue

        if not step.argv:
            outcomes.append(Outcome(step.label, "skipped", "nothing to do"))
            continue

        executable = _resolve_exe(step.argv[0])
        if executable is None:
            outcomes.append(Outcome(step.label, "skipped", f"{step.argv[0]} not found on PATH"))
            continue
        argv = (executable, *step.argv[1:])

        if _is_docker_step(argv):
            executable_name = Path(executable).name.lower()
            daemon_exe = "docker" if executable_name.startswith("docker") else executable
            info_code, _info_out = run((daemon_exe, "info"), root)
            if info_code != 0:
                outcomes.append(
                    Outcome(
                        step.label,
                        "failed",
                        "Docker is not running - start Docker and retry",
                    )
                )
                break

        if step.kind == "serve":
            try:
                pid = launch(argv, root)
            except OSError as exc:
                outcomes.append(Outcome(step.label, "failed", str(exc)))
                break
            outcomes.append(Outcome(step.label, "done", f"started with pid {pid}"))
            continue

        code, output = run(argv, root)
        if code != 0:
            outcomes.append(Outcome(step.label, "failed", _tail(output) or f"exit code {code}"))
            break

        if step.kind == "freeze" and step.target is not None:
            step.target.write_text(output.rstrip() + "\n", encoding="utf-8", newline="\n")
            outcomes.append(Outcome(step.label, "done", f"wrote {step.target.name}"))
        else:
            outcomes.append(Outcome(step.label, "done", _tail(output)))
    return outcomes


def plan_is_clean(outcomes: Sequence[Outcome]) -> bool:
    """True when every outcome succeeded (done or skipped)."""
    return all(outcome.status != "failed" for outcome in outcomes)
