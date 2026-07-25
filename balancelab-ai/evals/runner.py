"""Deterministic evaluation smoke runner for the M0 balance-sheet core.

Loads the versioned case set, runs each case through the real synthetic
generator and calculation engine, and checks results against pinned
expectations. Prints per-case outcomes and an aggregate, and exits non-zero on
any regression so CI can gate merges. No network, no models: fully deterministic.

Usage::

    python -m evals.runner [path/to/cases.json]
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from balancelab.calc.engine import compute_snapshot
from balancelab.errors import ReconciliationError
from balancelab.synthetic.generator import generate_synthetic_portfolio

DEFAULT_CASES = Path(__file__).parent / "cases" / "golden_reconciliation.json"


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    passed: bool
    detail: str


def _run_golden(case: dict[str, Any]) -> CaseResult:
    expect = case["expect"]
    snapshot = compute_snapshot(generate_synthetic_portfolio(seed=case["seed"]))
    mismatches: list[str] = []
    if snapshot.balances is not expect["balances"]:
        mismatches.append(f"balances={snapshot.balances}")
    for field in ("total_assets", "total_liabilities", "total_equity"):
        actual = getattr(snapshot, field)
        if actual != Decimal(expect[field]):
            mismatches.append(f"{field}: {actual} != {expect[field]}")
    if len(snapshot.lineage) != expect["lineage_nodes"]:
        mismatches.append(f"lineage_nodes={len(snapshot.lineage)} != {expect['lineage_nodes']}")
    return CaseResult(case["id"], not mismatches, "; ".join(mismatches) or "ok")


def _run_adversarial(case: dict[str, Any]) -> CaseResult:
    portfolio = generate_synthetic_portfolio(seed=case["seed"])
    # Rebuild with a corrupted first asset balance to break the identity.
    accounts = list(portfolio.accounts)
    corrupted = accounts[0].model_copy(update={"balance": Decimal(case["corrupt_first_asset_to"])})
    accounts[0] = corrupted
    portfolio = portfolio.model_copy(update={"accounts": tuple(accounts)})
    try:
        compute_snapshot(portfolio)
    except ReconciliationError:
        return CaseResult(case["id"], True, "reconciliation correctly rejected")
    return CaseResult(case["id"], False, "expected ReconciliationError, none raised")


def run_cases(path: Path) -> list[CaseResult]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results: list[CaseResult] = []
    for case in payload["cases"]:
        kind = case["kind"]
        if kind == "golden":
            results.append(_run_golden(case))
        elif kind == "adversarial":
            results.append(_run_adversarial(case))
        else:  # pragma: no cover - guards against malformed case files
            results.append(CaseResult(case["id"], False, f"unknown case kind: {kind}"))
    return results


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    path = Path(args[0]) if args else DEFAULT_CASES
    results = run_cases(path)
    passed = sum(1 for r in results if r.passed)
    for result in results:
        marker = "PASS" if result.passed else "FAIL"
        print(f"[{marker}] {result.case_id}: {result.detail}")
    print(f"\n{passed}/{len(results)} cases passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
