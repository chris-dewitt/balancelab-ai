"""Reconciliation service.

Derives :class:`~balancelab.domain.reconciliation.Reconciliation` records from
stored snapshots and forecasts. Pure and deterministic: the same input always
yields the same checks (ids/timestamps aside).
"""

from __future__ import annotations

from decimal import Decimal

from balancelab.calc import formulas
from balancelab.config import Settings, get_settings
from balancelab.domain.forecast import ForecastRun
from balancelab.domain.models import AccountCategory, Snapshot
from balancelab.domain.reconciliation import (
    Reconciliation,
    ReconciliationCheck,
    ReconciliationSubject,
)


def _tolerance(settings: Settings | None) -> Decimal:
    cfg = settings or get_settings()
    return Decimal(str(cfg.reconciliation_abs_tolerance))


def _check(
    period: int | None,
    assets: Decimal,
    liabilities: Decimal,
    equity: Decimal,
    tolerance: Decimal,
) -> ReconciliationCheck:
    residual = formulas.balance_residual(assets, liabilities, equity)
    return ReconciliationCheck(
        period=period,
        total_assets=assets,
        total_liabilities=liabilities,
        total_equity=equity,
        residual=residual,
        tolerance=tolerance,
        passed=formulas.is_balanced(residual, tolerance),
    )


def reconcile_snapshot(snapshot: Snapshot, settings: Settings | None = None) -> Reconciliation:
    """Reconcile a snapshot's identity (single check)."""

    tolerance = _tolerance(settings)
    check = _check(
        None,
        snapshot.total_assets,
        snapshot.total_liabilities,
        snapshot.total_equity,
        tolerance,
    )
    return Reconciliation(
        subject_type=ReconciliationSubject.SNAPSHOT,
        subject_id=snapshot.id,
        currency=snapshot.currency,
        checks=(check,),
        passed=check.passed,
    )


def reconcile_forecast(run: ForecastRun, settings: Settings | None = None) -> Reconciliation:
    """Reconcile a forecast's identity for every period."""

    tolerance = _tolerance(settings)
    by_period: dict[int, dict[AccountCategory, Decimal]] = {}
    for value in run.values:
        if value.account_id is None and value.category is not None:
            by_period.setdefault(value.period, {})[value.category] = value.value

    checks = tuple(
        _check(
            period,
            totals.get(AccountCategory.ASSET, Decimal(0)),
            totals.get(AccountCategory.LIABILITY, Decimal(0)),
            totals.get(AccountCategory.EQUITY, Decimal(0)),
            tolerance,
        )
        for period, totals in sorted(by_period.items())
    )
    return Reconciliation(
        subject_type=ReconciliationSubject.FORECAST,
        subject_id=run.id,
        currency=run.currency,
        checks=checks,
        passed=all(c.passed for c in checks),
    )
