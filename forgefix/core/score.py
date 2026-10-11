"""Deterministic health scoring for ForgeFix findings."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from forgefix.core.rules import Finding


@dataclass(frozen=True)
class ScoreResult:
    """Aggregate score plus the counts and breakdowns used by reports."""

    total: int
    passed: int
    warned: int
    failed: int
    skipped: int
    deductions: int
    breakdown: dict[str, int]
    top_fixes: list[tuple[str, str, int]]


def score_findings(findings: Sequence[Finding]) -> ScoreResult:
    """Score findings: start at 100, subtract deterministic per-finding weights."""
    total_deduction = 0
    passed = warned = failed = skipped = 0
    breakdown: dict[str, int] = {}
    fixes: list[tuple[int, str, str]] = []

    for finding in findings:
        deduction = finding.deduction
        total_deduction += deduction
        breakdown[finding.category] = breakdown.get(finding.category, 0) + deduction
        if deduction > 0:
            fixes.append((deduction, finding.title, finding.suggestion))
        if finding.status == "pass":
            passed += 1
        elif finding.status == "warn":
            warned += 1
        elif finding.status == "fail":
            failed += 1
        else:
            skipped += 1

    fixes.sort(key=lambda item: item[0], reverse=True)
    top_fixes = [(title, suggestion, deduction) for deduction, title, suggestion in fixes[:5]]
    total = max(0, min(100, 100 - total_deduction))
    return ScoreResult(
        total=total,
        passed=passed,
        warned=warned,
        failed=failed,
        skipped=skipped,
        deductions=total_deduction,
        breakdown=dict(sorted(breakdown.items())),
        top_fixes=top_fixes,
    )
