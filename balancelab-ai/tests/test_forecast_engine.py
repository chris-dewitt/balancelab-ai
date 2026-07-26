"""Tests for the deterministic forecast engine."""

from __future__ import annotations

from decimal import Decimal

import pytest

from balancelab.calc.forecast import FORECAST_FORMULA_VERSION, compute_forecast
from balancelab.domain.models import AccountCategory
from balancelab.domain.scenario import Assumption, Scenario
from balancelab.errors import ValidationError
from balancelab.synthetic.generator import generate_synthetic_portfolio


def _scenario(
    portfolio_id: str, asset: str = "0.05", liability: str = "0.02", horizon: int = 3
) -> Scenario:
    return Scenario(
        name="s",
        base_portfolio_id=portfolio_id,
        horizon_periods=horizon,
        assumptions=(
            Assumption(target=AccountCategory.ASSET, value=Decimal(asset)),
            Assumption(target=AccountCategory.LIABILITY, value=Decimal(liability)),
        ),
    )


def test_forecast_is_deterministic() -> None:
    p = generate_synthetic_portfolio(seed=7)
    s = _scenario(p.id)
    a = compute_forecast(p, s)
    b = compute_forecast(p, s)
    assert [v.value for v in a.values] == [v.value for v in b.values]


def test_identity_holds_every_period() -> None:
    p = generate_synthetic_portfolio(seed=7)
    run = compute_forecast(p, _scenario(p.id, horizon=5))
    for period in range(6):
        assets = _total(run, AccountCategory.ASSET, period)
        liabilities = _total(run, AccountCategory.LIABILITY, period)
        equity = _total(run, AccountCategory.EQUITY, period)
        assert assets == liabilities + equity


def test_period_zero_matches_base() -> None:
    p = generate_synthetic_portfolio(seed=3)
    run = compute_forecast(p, _scenario(p.id))
    base_assets = sum(
        (a.balance for a in p.accounts_by_category(AccountCategory.ASSET)), Decimal(0)
    )
    assert _total(run, AccountCategory.ASSET, 0) == base_assets


def test_growth_is_applied() -> None:
    p = generate_synthetic_portfolio(seed=3)
    run = compute_forecast(p, _scenario(p.id, asset="0.10", liability="0.00"))
    a0 = _total(run, AccountCategory.ASSET, 0)
    a1 = _total(run, AccountCategory.ASSET, 1)
    # 10% growth, within rounding of the per-account quantization.
    assert a1 > a0
    assert abs(a1 - (a0 * Decimal("1.10"))) <= Decimal("0.05")


def test_lineage_is_versioned_and_nonempty() -> None:
    p = generate_synthetic_portfolio(seed=1)
    run = compute_forecast(p, _scenario(p.id))
    assert run.lineage
    assert all(n.formula_version == FORECAST_FORMULA_VERSION for n in run.lineage)


def test_mismatched_portfolio_raises() -> None:
    p = generate_synthetic_portfolio(seed=1)
    other = generate_synthetic_portfolio(seed=2)
    with pytest.raises(ValidationError):
        compute_forecast(other, _scenario(p.id))


def _total(run: object, category: AccountCategory, period: int) -> Decimal:
    from balancelab.domain.forecast import ForecastRun

    assert isinstance(run, ForecastRun)
    return next(
        v.value
        for v in run.values
        if v.account_id is None and v.category == category and v.period == period
    )
