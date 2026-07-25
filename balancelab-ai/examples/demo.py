#!/usr/bin/env python3
"""M0 demonstration: synthetic portfolio -> deterministic snapshot -> lineage.

Runs the full deterministic path with no server and no model calls, and prints a
human-readable trace showing that every reported total resolves to a formula,
its inputs, a unit, and a formula version.

Usage::

    python examples/demo.py [seed]
"""

from __future__ import annotations

import sys

from balancelab.calc.engine import compute_snapshot
from balancelab.synthetic.generator import ensure_synthetic, generate_synthetic_portfolio


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    seed = int(args[0]) if args else 2025

    portfolio = ensure_synthetic(generate_synthetic_portfolio(seed=seed))
    snapshot = compute_snapshot(portfolio)

    print(f"Portfolio: {portfolio.name}  (id={portfolio.id})")
    print(f"  origin={portfolio.provenance.origin}  seed={portfolio.provenance.seed}")
    print(f"  as_of={portfolio.as_of_date}  currency={portfolio.currency}")
    print("  accounts:")
    for account in portfolio.accounts:
        print(f"    - [{account.category}] {account.name}: {account.balance}")

    print("\nSnapshot (deterministic):")
    print(f"  total_assets       = {snapshot.total_assets} {snapshot.currency}")
    print(f"  total_liabilities  = {snapshot.total_liabilities} {snapshot.currency}")
    print(f"  total_equity       = {snapshot.total_equity} {snapshot.currency}")
    print(f"  balances (A=L+E)   = {snapshot.balances}")

    print("\nCalculation lineage:")
    for node in snapshot.lineage:
        inputs = ", ".join(node.inputs) if node.inputs else "-"
        print(
            f"  {node.label}: {node.value} {node.unit}"
            f"  [formula='{node.formula}' v={node.formula_version} inputs={inputs}]"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
