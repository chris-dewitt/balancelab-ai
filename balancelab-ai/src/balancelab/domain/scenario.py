"""Scenario and assumption schemas.

A scenario describes a bounded, deterministic forecast: a base portfolio, a
horizon, and a set of typed assumptions. Assumptions are intentionally narrow in
this first slice — per-category growth rates — so the forecast engine stays fully
deterministic and every projected figure is explainable. Richer assumption kinds
(rate shocks, macro paths) are added in later milestones.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import Field, model_validator

from balancelab.domain.base import DomainModel, utc_now
from balancelab.domain.ids import ASSUMPTION, SCENARIO, new_id
from balancelab.domain.models import AccountCategory

# A conservative upper bound on forecast horizon to keep runs bounded.
MAX_HORIZON_PERIODS = 120


class AssumptionKind(StrEnum):
    """The kind of assumption. Only per-period growth rate is supported so far."""

    GROWTH_RATE = "growth_rate"


class Assumption(DomainModel):
    """A single typed assumption applied to a balance-sheet category.

    ``value`` is a per-period rate expressed as a decimal fraction (e.g.
    ``0.02`` for +2% per period). Equity is never targeted directly: it is a
    residual of assets and liabilities, so a growth assumption on equity would be
    ambiguous and is rejected.
    """

    id: str = Field(default_factory=lambda: new_id(ASSUMPTION))
    target: AccountCategory
    kind: AssumptionKind = AssumptionKind.GROWTH_RATE
    value: Decimal
    description: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _reject_equity_target(self) -> Assumption:
        if self.target == AccountCategory.EQUITY:
            raise ValueError("equity is a residual and cannot be a growth-assumption target")
        return self


class Scenario(DomainModel):
    """A named, versioned forecast scenario over a base portfolio."""

    id: str = Field(default_factory=lambda: new_id(SCENARIO))
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    base_portfolio_id: str
    horizon_periods: int = Field(ge=1, le=MAX_HORIZON_PERIODS)
    assumptions: tuple[Assumption, ...] = ()
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _unique_target_per_kind(self) -> Scenario:
        seen: set[tuple[AccountCategory, AssumptionKind]] = set()
        for assumption in self.assumptions:
            key = (assumption.target, assumption.kind)
            if key in seen:
                raise ValueError(
                    f"duplicate assumption for target={assumption.target} kind={assumption.kind}"
                )
            seen.add(key)
        return self

    def growth_rate(self, category: AccountCategory) -> Decimal:
        """Return the per-period growth rate for ``category`` (0 if unspecified)."""

        for assumption in self.assumptions:
            if assumption.kind == AssumptionKind.GROWTH_RATE and assumption.target == category:
                return assumption.value
        return Decimal(0)
