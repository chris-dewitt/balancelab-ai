"""Deterministic evaluation smoke runner for the balance-sheet core.

Loads the versioned case sets, runs each case through the real synthetic
generator and calculation/forecast engines, and checks results against pinned
expectations. Prints per-case outcomes and an aggregate, and exits non-zero on
any regression so CI can gate merges. No network, no models: fully deterministic.

Usage::

    python -m evals.runner [path/to/cases.json ...]
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from balancelab.calc.engine import compute_snapshot
from balancelab.calc.forecast import compute_forecast
from balancelab.domain.models import AccountCategory
from balancelab.domain.scenario import Assumption, Scenario
from balancelab.errors import ReconciliationError
from balancelab.synthetic.generator import generate_synthetic_portfolio

_CASES_DIR = Path(__file__).parent / "cases"
DEFAULT_CASES = _CASES_DIR / "golden_reconciliation.json"
DEFAULT_CASE_FILES = (
    _CASES_DIR / "golden_reconciliation.json",
    _CASES_DIR / "golden_forecast.json",
)


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


def _run_forecast(case: dict[str, Any]) -> CaseResult:
    expect = case["expect"]
    portfolio = generate_synthetic_portfolio(seed=case["seed"])
    scenario = Scenario(
        name=case["id"],
        base_portfolio_id=portfolio.id,
        horizon_periods=case["horizon"],
        assumptions=(
            Assumption(target=AccountCategory.ASSET, value=Decimal(case["asset_growth"])),
            Assumption(target=AccountCategory.LIABILITY, value=Decimal(case["liability_growth"])),
        ),
    )
    run = compute_forecast(portfolio, scenario)
    mismatches: list[str] = []
    fields = {
        "total_assets": AccountCategory.ASSET,
        "total_liabilities": AccountCategory.LIABILITY,
        "total_equity": AccountCategory.EQUITY,
    }
    for field, category in fields.items():
        actual = [str(v.value) for v in run.totals(category)]
        if actual != expect[field]:
            mismatches.append(f"{field}: {actual} != {expect[field]}")
    return CaseResult(case["id"], not mismatches, "; ".join(mismatches) or "ok")


def run_cases(path: Path) -> list[CaseResult]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results: list[CaseResult] = []
    for case in payload["cases"]:
        kind = case["kind"]
        if kind == "golden":
            results.append(_run_golden(case))
        elif kind == "adversarial":
            results.append(_run_adversarial(case))
        elif kind == "forecast":
            results.append(_run_forecast(case))
        else:  # pragma: no cover - guards against malformed case files
            results.append(CaseResult(case["id"], False, f"unknown case kind: {kind}"))
    return results


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    paths = [Path(a) for a in args] if args else list(DEFAULT_CASE_FILES)
    results: list[CaseResult] = []
    for path in paths:
        results.extend(run_cases(path))
    passed = sum(1 for r in results if r.passed)
    for result in results:
        marker = "PASS" if result.passed else "FAIL"
        print(f"[{marker}] {result.case_id}: {result.detail}")
    print(f"\n{passed}/{len(results)} cases passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
