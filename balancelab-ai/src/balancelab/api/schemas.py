"""Request schemas for the v1 API surface.

Response bodies reuse the domain models directly (``Portfolio``, ``Snapshot``),
which keeps a single typed contract between the domain and the wire.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from balancelab.domain.models import Portfolio


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
