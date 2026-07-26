"""Backend-agnostic storage contract tests.

The same tests run against every backend so they behave identically. The
in-memory backend always runs; the SQLAlchemy/Postgres backend runs only when
``BALANCELAB_TEST_DATABASE_URL`` is set (opt-in, isolated), which CI provides via
a disposable Postgres service.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from decimal import Decimal

import pytest

from balancelab.calc.engine import compute_snapshot
from balancelab.calc.forecast import compute_forecast
from balancelab.domain.forecast import ForecastRun
from balancelab.domain.models import AccountCategory, Portfolio, Snapshot
from balancelab.domain.scenario import Assumption, Scenario
from balancelab.storage import UnitOfWork, UnitOfWorkFactory
from balancelab.storage.memory import InMemoryDatabase, InMemoryUnitOfWork
from balancelab.synthetic.generator import generate_synthetic_portfolio

_PG_URL = os.environ.get("BALANCELAB_TEST_DATABASE_URL")


def _make_portfolio(seed: int = 1) -> Portfolio:
    return generate_synthetic_portfolio(seed=seed)


def _make_snapshot(portfolio: Portfolio) -> Snapshot:
    return compute_snapshot(portfolio)


def _make_scenario(portfolio: Portfolio) -> Scenario:
    return Scenario(
        name="s",
        base_portfolio_id=portfolio.id,
        horizon_periods=2,
        assumptions=(Assumption(target=AccountCategory.ASSET, value=Decimal("0.05")),),
    )


def _make_forecast(portfolio: Portfolio, scenario: Scenario) -> ForecastRun:
    return compute_forecast(portfolio, scenario)


@pytest.fixture(
    params=[
        "memory",
        pytest.param(
            "postgres",
            marks=pytest.mark.skipif(
                _PG_URL is None, reason="BALANCELAB_TEST_DATABASE_URL not set"
            ),
        ),
    ]
)
def uow_factory(request: pytest.FixtureRequest) -> Iterator[UnitOfWorkFactory]:
    if request.param == "memory":
        db = InMemoryDatabase()
        yield lambda: InMemoryUnitOfWork(db)
        return

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from balancelab.storage.orm import Base
    from balancelab.storage.sqlalchemy_repo import SqlAlchemyUnitOfWork

    assert _PG_URL is not None
    engine = create_engine(_PG_URL, future=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        yield lambda: SqlAlchemyUnitOfWork(session_factory())
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_portfolio_roundtrip(uow_factory: UnitOfWorkFactory) -> None:
    portfolio = _make_portfolio()
    with uow_factory() as uow:
        uow.portfolios.add(portfolio)
        uow.commit()
    with uow_factory() as uow:
        loaded = uow.portfolios.get(portfolio.id)
    assert loaded is not None
    assert loaded == portfolio


def test_snapshot_roundtrip(uow_factory: UnitOfWorkFactory) -> None:
    portfolio = _make_portfolio(2)
    snapshot = _make_snapshot(portfolio)
    with uow_factory() as uow:
        uow.snapshots.add(snapshot)
        uow.commit()
    with uow_factory() as uow:
        loaded = uow.snapshots.get(snapshot.id)
    assert loaded is not None
    assert loaded == snapshot


def test_get_missing_returns_none(uow_factory: UnitOfWorkFactory) -> None:
    with uow_factory() as uow:
        assert uow.portfolios.get("port_does_not_exist") is None
        assert uow.snapshots.get("snap_does_not_exist") is None


def test_add_is_idempotent_by_id(uow_factory: UnitOfWorkFactory) -> None:
    portfolio = _make_portfolio(3)
    with uow_factory() as uow:
        first = uow.portfolios.add(portfolio)
        second = uow.portfolios.add(portfolio)
        uow.commit()
    assert first.id == second.id == portfolio.id
    # Re-reading yields exactly one, equal record.
    with uow_factory() as uow:
        loaded = uow.portfolios.get(portfolio.id)
    assert loaded == portfolio


def test_scenario_roundtrip_list_and_delete(uow_factory: UnitOfWorkFactory) -> None:
    portfolio = _make_portfolio(4)
    scenario = _make_scenario(portfolio)
    with uow_factory() as uow:
        uow.scenarios.add(scenario)
        uow.commit()
    with uow_factory() as uow:
        assert uow.scenarios.get(scenario.id) == scenario
        assert scenario.id in {s.id for s in uow.scenarios.list()}
    with uow_factory() as uow:
        assert uow.scenarios.delete(scenario.id) is True
        uow.commit()
    with uow_factory() as uow:
        assert uow.scenarios.get(scenario.id) is None
        assert uow.scenarios.delete(scenario.id) is False


def test_forecast_roundtrip(uow_factory: UnitOfWorkFactory) -> None:
    portfolio = _make_portfolio(5)
    scenario = _make_scenario(portfolio)
    run = _make_forecast(portfolio, scenario)
    with uow_factory() as uow:
        uow.forecasts.add(run)
        uow.commit()
    with uow_factory() as uow:
        loaded = uow.forecasts.get(run.id)
    assert loaded == run


def test_factory_satisfies_protocol(uow_factory: UnitOfWorkFactory) -> None:
    with uow_factory() as uow:
        assert isinstance(uow, UnitOfWork)
