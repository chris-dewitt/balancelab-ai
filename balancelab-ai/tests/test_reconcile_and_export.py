"""Tests for the reconciliation service and export builders."""

from __future__ import annotations

from decimal import Decimal

from balancelab.calc.engine import compute_snapshot
from balancelab.calc.forecast import compute_forecast
from balancelab.config import Settings
from balancelab.domain.export import EXPORT_SCHEMA_VERSION
from balancelab.domain.models import AccountCategory
from balancelab.domain.reconciliation import ReconciliationSubject
from balancelab.domain.scenario import Assumption, Scenario
from balancelab.export import build_forecast_export, build_snapshot_export
from balancelab.reconcile import reconcile_forecast, reconcile_snapshot
from balancelab.synthetic.generator import generate_synthetic_portfolio


def _forecast(seed: int = 7, horizon: int = 3):
    portfolio = generate_synthetic_portfolio(seed=seed)
    scenario = Scenario(
        name="s",
        base_portfolio_id=portfolio.id,
        horizon_periods=horizon,
        assumptions=(
            Assumption(target=AccountCategory.ASSET, value=Decimal("0.05")),
            Assumption(target=AccountCategory.LIABILITY, value=Decimal("0.02")),
        ),
    )
    return portfolio, scenario, compute_forecast(portfolio, scenario)


def test_snapshot_reconciliation_passes() -> None:
    snapshot = compute_snapshot(generate_synthetic_portfolio(seed=3))
    recon = reconcile_snapshot(snapshot)
    assert recon.subject_type == ReconciliationSubject.SNAPSHOT
    assert recon.subject_id == snapshot.id
    assert recon.passed is True
    assert len(recon.checks) == 1
    assert recon.checks[0].period is None
    assert recon.checks[0].residual == Decimal("0.00")


def test_forecast_reconciliation_is_per_period() -> None:
    _, _, run = _forecast(horizon=4)
    recon = reconcile_forecast(run)
    assert recon.subject_type == ReconciliationSubject.FORECAST
    assert recon.passed is True
    # One check per period, 0..horizon.
    assert [c.period for c in recon.checks] == [0, 1, 2, 3, 4]
    assert all(c.passed for c in recon.checks)


def test_reconciliation_uses_configured_tolerance() -> None:
    snapshot = compute_snapshot(generate_synthetic_portfolio(seed=3))
    recon = reconcile_snapshot(snapshot, Settings(reconciliation_abs_tolerance=0.5))
    assert recon.checks[0].tolerance == Decimal("0.5")


def test_snapshot_export_is_self_contained() -> None:
    portfolio = generate_synthetic_portfolio(seed=9)
    snapshot = compute_snapshot(portfolio)
    export = build_snapshot_export(portfolio, snapshot)
    assert export.schema_version == EXPORT_SCHEMA_VERSION
    assert export.portfolio.id == portfolio.id
    assert export.snapshot.id == snapshot.id
    assert export.reconciliation.passed is True
    assert export.lineage.nodes  # non-empty graph
    assert len(export.lineage.nodes) == len(snapshot.lineage)


def test_forecast_export_is_self_contained() -> None:
    portfolio, scenario, run = _forecast()
    export = build_forecast_export(portfolio, scenario, run)
    assert export.scenario.id == scenario.id
    assert export.forecast.id == run.id
    assert export.reconciliation.passed is True
    assert len(export.lineage.nodes) == len(run.lineage)
