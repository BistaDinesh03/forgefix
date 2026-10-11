"""Unit tests for deterministic health scoring."""

from forgefix.core.rules import Finding
from forgefix.core.score import score_findings


def make(
    status: str,
    *,
    rule_id: str = "rule",
    category: str = "docs",
    weight: int = 10,
    warn_weight: int = 4,
    title: str = "Check",
    suggestion: str = "Fix it",
) -> Finding:
    return Finding(
        rule_id=rule_id,
        category=category,
        title=title,
        status=status,  # type: ignore[arg-type]
        detail="detail",
        suggestion=suggestion,
        weight=weight,
        warn_weight=warn_weight,
    )


def test_all_pass_scores_100() -> None:
    result = score_findings([make("pass"), make("skip")])
    assert result.total == 100
    assert result.passed == 1
    assert result.skipped == 1
    assert result.deductions == 0
    assert result.top_fixes == []


def test_mixed_statuses_score_deterministically() -> None:
    findings = [
        make("fail", weight=12),
        make("warn", warn_weight=3),
        make("pass"),
        make("skip"),
    ]
    result = score_findings(findings)
    assert result.total == 100 - 12 - 3
    assert (result.failed, result.warned, result.passed, result.skipped) == (1, 1, 1, 1)
    assert result.breakdown == {"docs": 15}


def test_breakdown_groups_by_category() -> None:
    findings = [
        make("fail", category="deps", weight=5),
        make("warn", category="docs", warn_weight=2),
        make("fail", category="docs", weight=10),
    ]
    result = score_findings(findings)
    assert result.breakdown == {"deps": 5, "docs": 12}


def test_score_clamps_to_zero() -> None:
    findings = [make("fail", weight=60), make("fail", weight=60)]
    result = score_findings(findings)
    assert result.total == 0
    assert result.deductions == 120


def test_top_fixes_sorted_by_deduction_and_capped_at_five() -> None:
    findings = [
        make("fail", weight=5, title="c0"),
        make("fail", weight=20, title="c1"),
        make("fail", weight=10, title="c2"),
        make("fail", weight=1, title="c3"),
        make("fail", weight=8, title="c4"),
        make("fail", weight=3, title="c5"),
        make("fail", weight=15, title="c6"),
    ]
    result = score_findings(findings)
    assert len(result.top_fixes) == 5
    assert [deduction for _, _, deduction in result.top_fixes] == [20, 15, 10, 8, 5]
    assert result.top_fixes[0][0] == "c1"
    assert result.top_fixes[0][1] == "Fix it"


def test_deduction_property_per_status() -> None:
    assert make("fail", weight=12).deduction == 12
    assert make("warn", warn_weight=7).deduction == 7
    assert make("pass").deduction == 0
    assert make("skip").deduction == 0


def test_empty_findings_are_clean() -> None:
    result = score_findings([])
    assert result.total == 100
    assert result.breakdown == {}
