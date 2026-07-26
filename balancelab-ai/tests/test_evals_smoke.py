"""Ensure the deterministic evaluation smoke suite passes on the golden sets."""

from __future__ import annotations

from evals.runner import DEFAULT_CASE_FILES, run_cases


def test_all_golden_cases_pass() -> None:
    results = [r for path in DEFAULT_CASE_FILES for r in run_cases(path)]
    assert results, "expected at least one eval case"
    failures = [r for r in results if not r.passed]
    assert not failures, f"eval regressions: {[(r.case_id, r.detail) for r in failures]}"
