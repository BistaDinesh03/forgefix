"""Report rendering and writing tests."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from forgefix.core.report import render_markdown, score_label, write_report
from forgefix.core.rules import Finding
from forgefix.core.scanner import ScanResult, scan
from forgefix.core.score import score_findings

FIXTURES = Path(__file__).parent / "fixtures"
BROKEN = FIXTURES / "broken_repo"
NOW = datetime(2026, 10, 11, 12, 0, tzinfo=UTC)


def test_render_broken_fixture_report() -> None:
    md = render_markdown(scan(BROKEN), now=NOW)
    assert md.startswith("# ForgeFix health report")
    assert "2026-10-11 12:00 UTC" in md
    assert "Health score: **46/100** (critical)" in md
    assert "| Status | Check | Category | Detail |" in md
    assert "README present" in md
    assert "## Category breakdown" in md
    assert "## Top fixes" in md
    assert "## Plugins" in md
    assert "`example`" in md
    assert "no source code was copied" in md


def test_render_escapes_pipes_in_cells() -> None:
    finding = Finding(
        rule_id="x",
        category="docs",
        title="T",
        status="fail",
        detail="a | b",
        suggestion="s",
        weight=10,
        warn_weight=5,
    )
    result = ScanResult(
        root=Path("."), findings=[finding], score=score_findings([finding]), plugins=[]
    )
    assert "a \\| b" in render_markdown(result, now=NOW)


def test_render_empty_result() -> None:
    result = ScanResult(root=Path("."), findings=[], score=score_findings([]), plugins=[])
    md = render_markdown(result, now=NOW)
    assert "Nothing to fix" in md
    assert "| - | 0 |" in md


def test_write_report_creates_parents(tmp_path: Path) -> None:
    target = tmp_path / "deep" / "nested" / "report.md"
    written = write_report(target, "# hi\n")
    assert written.read_text(encoding="utf-8") == "# hi\n"


@pytest.mark.parametrize(
    ("score", "label"),
    [(100, "healthy"), (80, "healthy"), (79, "needs work"), (50, "needs work"), (49, "critical")],
)
def test_score_label_bands(score: int, label: str) -> None:
    assert score_label(score) == label
