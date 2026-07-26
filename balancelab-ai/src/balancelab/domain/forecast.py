"""Forecast result schemas.

A :class:`ForecastRun` is the deterministic output of applying a scenario to a
base portfolio: per-period projected values plus the full calculation lineage.
Like snapshots, every figure resolves to a formula, inputs, unit, and formula
version, and the balance-sheet identity holds in every period.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from balancelab.domain.base import DomainModel, utc_now
from balancelab.domain.ids import FORECAST_RUN, new_id
from balancelab.domain.models import AccountCategory, CalculationNode


class ForecastValue(DomainModel):
    """A single projected value at a given period.

    ``account_id`` is set for account-level rows and ``None`` for category totals.
    ``period`` 0 is the base (observed) period; 1..horizon are projections.
    """

    period: int = Field(ge=0)
    account_id: str | None
    label: str
    category: AccountCategory | None
    value: Decimal
    unit: str


class ForecastRun(DomainModel):
    """The result of running a scenario forecast."""

    id: str = Field(default_factory=lambda: new_id(FORECAST_RUN))
    scenario_id: str
    base_portfolio_id: str
    currency: str
    horizon_periods: int = Field(ge=1)
    formula_version: str
    values: tuple[ForecastValue, ...]
    lineage: tuple[CalculationNode, ...]
    created_at: datetime = Field(default_factory=utc_now)

    def totals(self, category: AccountCategory) -> tuple[ForecastValue, ...]:
        """Return the per-period category totals for ``category``, ordered by period."""

        rows = [v for v in self.values if v.account_id is None and v.category == category]
        return tuple(sorted(rows, key=lambda v: v.period))
