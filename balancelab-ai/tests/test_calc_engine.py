"""Tests for the deterministic calculation engine and lineage."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from balancelab.calc.engine import compute_snapshot
from balancelab.calc.formulas import FORMULA_VERSION
from balancelab.config import Settings
from balancelab.domain.models import Account, AccountCategory, DataOrigin, Portfolio, Provenance
from balancelab.errors import ReconciliationError
from balancelab.synthetic.generator import generate_synthetic_portfolio


def _portfolio(assets: str, liabilities: str, equity: str) -> Portfolio:
    return Portfolio(
        name="T",
        as_of_date=date(2025, 12, 31),
        currency="USD",
        provenance=Provenance(origin=DataOrigin.SYNTHETIC, generator="t", seed=0),
        accounts=(
            Account(
                name="A", category=AccountCategory.ASSET, currency="USD", balance=Decimal(assets)
            ),
            Account(
                name="L",
                category=AccountCategory.LIABILITY,
                currency="USD",
                balance=Decimal(liabilities),
            ),
            Account(
                name="E", category=AccountCategory.EQUITY, currency="USD", balance=Decimal(equity)
            ),
        ),
    )


def test_totals_are_correct() -> None:
    snapshot = compute_snapshot(_portfolio("100.00", "40.00", "60.00"))
    assert snapshot.total_assets == Decimal("100.00")
    assert snapshot.total_liabilities == Decimal("40.00")
    assert snapshot.total_equity == Decimal("60.00")
    assert snapshot.balances is True


def test_lineage_covers_every_number() -> None:
    snapshot = compute_snapshot(_portfolio("100.00", "40.00", "60.00"))
    labels = {node.label for node in snapshot.lineage}
    assert "total_asset" in labels
    assert "total_liability" in labels
    assert "total_equity" in labels
    assert "balance_residual" in labels
    # 3 leaves + 3 totals + 1 residual = 7 nodes.
    assert len(snapshot.lineage) == 7
    # Every node stamps the formula version.
    assert all(node.formula_version == FORMULA_VERSION for node in snapshot.lineage)


def test_total_nodes_reference_their_leaf_inputs() -> None:
    snapshot = compute_snapshot(_portfolio("100.00", "40.00", "60.00"))
    node_ids = {node.id for node in snapshot.lineage}
    total_asset = next(n for n in snapshot.lineage if n.label == "total_asset")
    assert total_asset.inputs  # non-empty
    assert all(input_id in node_ids for input_id in total_asset.inputs)


def test_reconciliation_failure_raises() -> None:
    with pytest.raises(ReconciliationError) as exc:
        compute_snapshot(_portfolio("100.00", "40.00", "5.00"))
    assert exc.value.details["residual"] == "55.00"


def test_tolerance_allows_small_drift() -> None:
    # Residual of 0.01 within default tolerance of 0.01 should pass.
    snapshot = compute_snapshot(
        _portfolio("100.01", "40.00", "60.00"),
        settings=Settings(reconciliation_abs_tolerance=0.01),
    )
    assert snapshot.balances is True


def test_generated_portfolio_reconciles() -> None:
    snapshot = compute_snapshot(generate_synthetic_portfolio(seed=99))
    assert snapshot.balances is True
