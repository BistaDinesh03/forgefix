"""ForgeFix command-line interface (Typer + Rich)."""

from __future__ import annotations

import ctypes
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forgefix import __version__
from forgefix.config import ForgeFixConfig, config_file, load_config, save_config
from forgefix.core.badge import badge_markdown, badge_url, detect_repo_slug, write_badge
from forgefix.core.report import render_markdown, score_label, write_report
from forgefix.core.scanner import ScanResult, scan
from forgefix.core.share import build_share_text, find_demo_gif
from forgefix.core.up import Outcome, detect_stack, execute_plan, plan_is_clean, plan_up

app = typer.Typer(
    name="forgefix",
    help="One command to set up, health-check, and repair any open-source project.",
    no_args_is_help=True,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console(width=100)


def _stdin_is_tty() -> bool:
    """Return whether stdin can answer a confirmation prompt."""
    try:
        return sys.stdin.isatty()
    except (AttributeError, ValueError):
        return False


def _print_share_panel(text: str) -> None:
    # Print the share panel, switching a legacy Windows console to UTF-8.
    #
    # The tweet intentionally contains an emoji. Rich's legacy Windows renderer
    # writes through the active console code page (often cp1252), which cannot
    # encode it. Switching the code page for the duration of the print keeps the
    # exact text on capable terminals and avoids a crash on older ones.
    restore_cp: int | None = None
    old_encoding = getattr(sys.stdout, "encoding", None)
    windll = getattr(ctypes, "windll", None)
    if sys.platform == "win32" and windll is not None:
        try:
            kernel32 = windll.kernel32
            restore_cp = int(kernel32.GetConsoleOutputCP())
            kernel32.SetConsoleOutputCP(65001)
        except (AttributeError, OSError, ValueError):
            restore_cp = None
        reconfigure = getattr(sys.stdout, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
    try:
        console.print(Panel(text, title="Share your score", border_style="green"))
        style = "red" if len(text) > 280 else "dim"
        console.print(f"[{style}]{len(text)} characters (tweet limit: 280)[/{style}]")
    finally:
        if restore_cp is not None and windll is not None:
            try:
                windll.kernel32.SetConsoleOutputCP(restore_cp)
            except (AttributeError, OSError):
                pass
        if old_encoding:
            reconfigure = getattr(sys.stdout, "reconfigure", None)
            if reconfigure is not None:
                try:
                    reconfigure(encoding=old_encoding, errors="replace")
                except (OSError, ValueError):
                    pass


# Rich style names per status. (bandit flags dict keys as passwords: false positive.)
STATUS_PALETTE = {"pass": "green", "warn": "yellow", "fail": "red", "skip": "dim"}  # nosec B105


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"forgefix {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
) -> None:
    """ForgeFix: setup, health-check, and repair for any repository."""


def _resolve_root(path: Path) -> Path:
    root = path.expanduser().resolve()
    if not root.is_dir():
        raise typer.BadParameter(f"not a directory: {path}", param_hint="--path")
    return root


def _scan(root: Path) -> ScanResult:
    config = load_config(root)
    return scan(root, disabled=config.disabled_rules)


def _print_doctor_table(result: ScanResult) -> None:
    table = Table(title=f"ForgeFix doctor: {result.root.name}")
    table.add_column("Check", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Detail")
    table.add_column("Fix", overflow="fold")
    for finding in result.findings:
        color = STATUS_PALETTE[finding.status]
        fix = finding.suggestion if finding.status in {"fail", "warn"} else "-"
        table.add_row(
            finding.title,
            f"[{color}]{finding.status.upper()}[/]",
            finding.detail,
            fix,
        )
    console.print(table)
    total = result.score.total
    color = "green" if total >= 80 else "yellow" if total >= 50 else "red"
    console.print(
        f"Health score: [bold {color}]{total}[/bold {color}]/100 "
        f"({score_label(total)}) - {result.score.passed} pass, {result.score.warned} warn, "
        f"{result.score.failed} fail, {result.score.skipped} skip"
    )
    if result.score.top_fixes:
        console.print("Top fixes:")
        for _title, suggestion, deduction in result.score.top_fixes:
            console.print(f"  [yellow]-{deduction}[/yellow] {suggestion}")


@app.command()
def init(
    path: Annotated[
        Path, typer.Option("--path", help="Directory that receives .forgefix.yml.")
    ] = Path("."),
) -> None:
    """Create a starter .forgefix.yml in the current (or given) directory."""
    root = path.expanduser().resolve()
    if root.exists() and not root.is_dir():
        raise typer.BadParameter(f"not a directory: {path}", param_hint="--path")
    root.mkdir(parents=True, exist_ok=True)
    if config_file(root).exists():
        typer.echo(f"[forgefix] kept existing {config_file(root).name}")
        return
    written = save_config(root, ForgeFixConfig())
    typer.echo(f"[forgefix] created {written}")


@app.command()
def doctor(
    path: Annotated[Path, typer.Option("--path", help="Repository to scan.")] = Path("."),
    json_output: Annotated[
        bool, typer.Option("--json", help="Print machine-readable JSON.")
    ] = False,
    min_score: Annotated[
        int | None,
        typer.Option("--min-score", help="Exit with code 2 when the score is below this value."),
    ] = None,
) -> None:
    """Scan a repository and print a pass/warn/fail table with fix suggestions."""
    root = _resolve_root(path)
    result = _scan(root)
    if json_output:
        payload = {
            "path": str(result.root),
            "score": asdict(result.score),
            "findings": [asdict(finding) for finding in result.findings],
            "plugins": result.plugins,
        }
        typer.echo(json.dumps(payload, indent=2))
    else:
        _print_doctor_table(result)

    config = load_config(root)
    threshold = min_score
    if threshold is None and config_file(root).is_file():
        threshold = config.min_score
    if threshold is not None and result.score.total < threshold:
        typer.echo(
            f"[forgefix] score {result.score.total} is below the required minimum {threshold}",
            err=True,
        )
        raise typer.Exit(code=2)


@app.command()
def report(
    path: Annotated[Path, typer.Option("--path", help="Repository to scan.")] = Path("."),
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", help="Markdown destination (default: reports/forgefix-report.md)."
        ),
    ] = None,
) -> None:
    """Write the markdown health report (score, breakdown, top fixes)."""
    root = _resolve_root(path)
    config = load_config(root)
    result = scan(root, disabled=config.disabled_rules)
    markdown = render_markdown(result)
    target = output if output is not None else Path(config.report_path)
    written = write_report(target, markdown)
    typer.echo(f"[forgefix] score {result.score.total}/100 -> {written}")


@app.command()
def badge(
    path: Annotated[Path, typer.Option("--path", help="Repository to scan.")] = Path("."),
    write: Annotated[
        bool,
        typer.Option("--write", help="Write .forgefix-badge.json for the current score."),
    ] = False,
    branch: Annotated[
        str,
        typer.Option("--branch", help="Branch that will host the badge JSON."),
    ] = "main",
    owner: Annotated[
        str | None,
        typer.Option("--owner", help="GitHub owner (default: detect from the origin remote)."),
    ] = None,
    repo: Annotated[
        str | None,
        typer.Option("--repo", help="GitHub repository (default: detect from the origin remote)."),
    ] = None,
) -> None:
    """Print a Shields.io endpoint URL for a live health badge."""
    root = _resolve_root(path)
    result = _scan(root)
    if (owner is None) != (repo is None):
        raise typer.BadParameter("pass both --owner and --repo, or neither")
    slug: tuple[str, str] | None
    if owner is not None and repo is not None:
        slug = (owner, repo)
    else:
        slug = detect_repo_slug(root)
    if slug is None:
        typer.echo(
            "[forgefix] could not detect a GitHub remote; pass --owner and --repo",
            err=True,
        )
        raise typer.Exit(code=2)
    url = badge_url(slug[0], slug[1], branch=branch)
    typer.echo(f"[forgefix] score: {result.score.total}/100")
    typer.echo(f"[forgefix] badge: {url}")
    typer.echo(f"[forgefix] markdown: {badge_markdown(slug[0], slug[1], branch=branch)}")
    if write:
        target = write_badge(root, result.score.total)
        typer.echo(f"[forgefix] wrote {target.name}")


@app.command()
def share(
    path: Annotated[Path, typer.Option("--path", help="Repository to scan.")] = Path("."),
    repo_url: Annotated[
        str | None,
        typer.Option("--repo-url", help="Override the repository URL."),
    ] = None,
) -> None:
    """Print a ready-to-post health-score update."""
    root = _resolve_root(path)
    result = _scan(root)
    slug = detect_repo_slug(root)
    url = repo_url or (f"https://github.com/{slug[0]}/{slug[1]}" if slug else None)
    gif = find_demo_gif(root)
    gif_url = (
        f"{url}/blob/main/{gif.relative_to(root).as_posix()}"
        if url is not None and gif is not None
        else None
    )
    text = build_share_text(result.score.total, url, gif_url)
    _print_share_panel(text)


@app.command()
def up(
    path: Annotated[Path, typer.Option("--path", help="Repository to bring up.")] = Path("."),
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Execute the plan (without it, print a dry-run)."),
    ] = False,
    no_serve: Annotated[
        bool,
        typer.Option("--no-serve", help="Never start a detected dev server."),
    ] = False,
    badge: Annotated[
        bool,
        typer.Option(
            "--badge",
            help="Write .forgefix-badge.json for the current score (works in dry-run too).",
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Create generated files without prompting."),
    ] = False,
) -> None:
    """One-command bring-up: detect stack, repair setup, install, test, serve."""
    root = _resolve_root(path)
    if badge and not apply:
        badge_score = _scan(root).score.total
        written = write_badge(root, badge_score)
        typer.echo(f"[forgefix] wrote {written.name} ({badge_score}/100)")
    stack = detect_stack(root)
    typer.echo(f"[forgefix] stack: {stack.name} ({stack.evidence})")
    steps = plan_up(root, serve=not no_serve)
    if not apply:
        for index, step in enumerate(steps, start=1):
            typer.echo(f"[dry-run] {index}. [{step.kind}] {step.label}")
        typer.echo(f"[dry-run] {len(steps)} step(s) planned - re-run with --apply to execute")
        return

    if not yes:
        repairs = [step for step in steps if step.kind == "repair"]
        if repairs and _stdin_is_tty():
            console.print("[bold]Files to create:[/bold]")
            for step in repairs:
                console.print(f"  - {step.target}")
            if not typer.confirm("Create these files?", default=True):
                steps = [step for step in steps if step.kind != "repair"]
                typer.echo("[forgefix] skipped generated files")
        elif repairs:
            typer.echo("[forgefix] non-interactive: creating missing files (pass --yes to silence)")

    outcomes = execute_plan(root, steps)
    _print_outcomes(outcomes)
    if badge:
        badge_score = _scan(root).score.total
        written = write_badge(root, badge_score)
        typer.echo(f"[forgefix] wrote {written.name} ({badge_score}/100)")
    if not plan_is_clean(outcomes):
        typer.echo("[forgefix] bring-up failed - see the failing step above", err=True)
        raise typer.Exit(code=1)
    typer.echo("[forgefix] bring-up complete")


def _print_outcomes(outcomes: list[Outcome]) -> None:
    marker = {"done": "[ok]", "skipped": "[skip]", "failed": "[fail]"}
    for outcome in outcomes:
        if outcome.status == "failed" and "\n" in outcome.detail:
            typer.echo(f"{marker[outcome.status]} {outcome.label}")
            for line in outcome.detail.splitlines():
                typer.echo(f"    {line}")
        else:
            suffix = f" - {outcome.detail}" if outcome.detail else ""
            typer.echo(f"{marker.get(outcome.status, '[??]')} {outcome.label}{suffix}")


@app.command()
def serve(
    host: Annotated[str, typer.Option("--host", help="Interface to bind.")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", help="TCP port to listen on.")] = 8000,
) -> None:
    """Run the FastAPI server exposing /health, /doctor, and /report."""
    import uvicorn

    typer.echo(f"[forgefix] serving on http://{host}:{port} - try /doctor?path=.")
    uvicorn.run("forgefix.server:app", host=host, port=port, log_level="warning")


@app.command()
def cloud() -> None:
    """Placeholder for the hosted dashboard (not enabled)."""
    typer.echo("Hosted version coming soon - see docs/monetization.md")
