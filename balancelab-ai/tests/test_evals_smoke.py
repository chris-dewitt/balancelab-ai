"""Ensure the deterministic evaluation smoke suite passes on the golden set."""

from __future__ import annotations

from evals.runner import DEFAULT_CASES, run_cases


def test_all_golden_and_adversarial_cases_pass() -> None:
    results = run_cases(DEFAULT_CASES)
    assert results, "expected at least one eval case"
    failures = [r for r in results if not r.passed]
    assert not failures, f"eval regressions: {[(r.case_id, r.detail) for r in failures]}"
