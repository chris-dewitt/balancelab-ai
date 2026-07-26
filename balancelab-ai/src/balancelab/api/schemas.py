"""Request schemas for the v1 API surface.

Response bodies reuse the domain models directly (``Portfolio``, ``Snapshot``),
which keeps a single typed contract between the domain and the wire.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from balancelab.domain.models import AccountCategory, Portfolio
from balancelab.domain.scenario import MAX_HORIZON_PERIODS, AssumptionKind


class SyntheticPortfolioRequest(BaseModel):
    """Parameters for generating a reproducible synthetic portfolio."""

    model_config = {"extra": "forbid"}

    seed: int = Field(ge=0, description="Deterministic seed; same seed -> same output.")
    name: str = Field(default="Synthetic Demo Bank", min_length=1, max_length=200)
    currency: str = Field(default="USD")
    as_of_date: date | None = None
    n_asset_accounts: int = Field(default=3, ge=1, le=5)
    n_liability_accounts: int = Field(default=2, ge=1, le=5)


class SnapshotRequest(BaseModel):
    """Compute a deterministic snapshot for a provided portfolio."""

    model_config = {"extra": "forbid"}

    portfolio: Portfolio


class AssumptionInput(BaseModel):
    """A scenario assumption in a create request."""

    model_config = {"extra": "forbid"}

    target: AccountCategory
    kind: AssumptionKind = AssumptionKind.GROWTH_RATE
    value: Decimal = Field(description="Per-period rate as a decimal fraction, e.g. 0.02.")
    description: str | None = Field(default=None, max_length=500)


class ScenarioCreateRequest(BaseModel):
    """Create a forecast scenario over an existing base portfolio."""

    model_config = {"extra": "forbid"}

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    base_portfolio_id: str
    horizon_periods: int = Field(ge=1, le=MAX_HORIZON_PERIODS)
    assumptions: tuple[AssumptionInput, ...] = ()


class ForecastCreateRequest(BaseModel):
    """Run a forecast for a stored scenario."""

    model_config = {"extra": "forbid"}

    scenario_id: str
