"""Deterministic calculation engine with full lineage.

Given a validated :class:`~balancelab.domain.models.Portfolio`, the engine
produces a :class:`~balancelab.domain.models.Snapshot` whose totals are
authoritative and whose ``lineage`` records exactly how each total was derived.
Every reported number resolves to a formula, its inputs, a unit, and the formula
version — satisfying the spec requirement that no displayed figure is unexplained.

The engine performs no model calls and no I/O; it is a pure transform from
portfolio to snapshot, which keeps results reproducible and testable.
"""

from __future__ import annotations

from decimal import Decimal

from balancelab.calc import formulas
from balancelab.config import Settings, get_settings
from balancelab.domain.models import (
    Account,
    AccountCategory,
    CalculationNode,
    Portfolio,
    Snapshot,
)
from balancelab.errors import ReconciliationError

_SOURCE_FORMULA = "source"  # sentinel formula for leaf (source-account) nodes


def _leaf_node(account: Account) -> CalculationNode:
    """Build a lineage leaf node for a single source account."""

    return CalculationNode(
        label=f"{account.category.value}:{account.name}",
        formula=_SOURCE_FORMULA,
        formula_version=formulas.FORMULA_VERSION,
        inputs=(account.id,),
        value=account.balance,
        unit=account.currency,
    )


def _category_total_node(
    category: AccountCategory,
    leaves: tuple[CalculationNode, ...],
    currency: str,
) -> CalculationNode:
    """Build an aggregate node summing the given leaf nodes for a category."""

    return CalculationNode(
        label=f"total_{category.value}",
        formula="sum(account.balance for account in category)",
        formula_version=formulas.FORMULA_VERSION,
        inputs=tuple(leaf.id for leaf in leaves),
        value=formulas.total(leaf.value for leaf in leaves),
        unit=currency,
    )


def compute_snapshot(portfolio: Portfolio, settings: Settings | None = None) -> Snapshot:
    """Compute a deterministic, fully-traced snapshot of ``portfolio``.

    Raises :class:`~balancelab.errors.ReconciliationError` if the balance-sheet
    identity (assets == liabilities + equity) does not hold within the configured
    absolute tolerance. The residual and totals are attached to the error so the
    failure is diagnosable without re-running.
    """

    cfg = settings or get_settings()
    currency = portfolio.currency

    # 1. Leaf nodes per source account, grouped by category.
    leaves_by_category: dict[AccountCategory, tuple[CalculationNode, ...]] = {}
    all_leaves: list[CalculationNode] = []
    for category in AccountCategory:
        accounts = portfolio.accounts_by_category(category)
        leaves = tuple(_leaf_node(a) for a in accounts)
        leaves_by_category[category] = leaves
        all_leaves.extend(leaves)

    # 2. Category totals.
    assets_node = _category_total_node(
        AccountCategory.ASSET, leaves_by_category[AccountCategory.ASSET], currency
    )
    liabilities_node = _category_total_node(
        AccountCategory.LIABILITY, leaves_by_category[AccountCategory.LIABILITY], currency
    )
    equity_node = _category_total_node(
        AccountCategory.EQUITY, leaves_by_category[AccountCategory.EQUITY], currency
    )

    # 3. Reconciliation node: residual = assets - (liabilities + equity).
    residual = formulas.balance_residual(
        assets_node.value, liabilities_node.value, equity_node.value
    )
    tolerance = Decimal(str(cfg.reconciliation_abs_tolerance))
    balanced = formulas.is_balanced(residual, tolerance)

    reconciliation_node = CalculationNode(
        label="balance_residual",
        formula="total_asset - (total_liability + total_equity)",
        formula_version=formulas.FORMULA_VERSION,
        inputs=(assets_node.id, liabilities_node.id, equity_node.id),
        value=residual,
        unit=currency,
    )

    lineage = (
        *all_leaves,
        assets_node,
        liabilities_node,
        equity_node,
        reconciliation_node,
    )

    if not balanced:
        raise ReconciliationError(
            "balance-sheet identity failed: assets != liabilities + equity",
            details={
                "portfolio_id": portfolio.id,
                "total_assets": str(assets_node.value),
                "total_liabilities": str(liabilities_node.value),
                "total_equity": str(equity_node.value),
                "residual": str(residual),
                "abs_tolerance": str(tolerance),
            },
        )

    return Snapshot(
        portfolio_id=portfolio.id,
        as_of_date=portfolio.as_of_date,
        currency=currency,
        total_assets=assets_node.value,
        total_liabilities=liabilities_node.value,
        total_equity=equity_node.value,
        balances=balanced,
        lineage=lineage,
    )
