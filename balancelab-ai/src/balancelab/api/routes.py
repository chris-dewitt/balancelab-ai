"""v1 API routes for the M0 vertical slice.

Two endpoints exercise the full deterministic path end to end:

* ``POST /v1/portfolios/synthetic`` generates a reproducible synthetic portfolio.
* ``POST /v1/snapshots`` computes a fully-traced snapshot for a portfolio,
  enforcing the synthetic-data-only boundary first.

Authoritative arithmetic happens only in :mod:`balancelab.calc`; these handlers
orchestrate typed inputs and outputs and never compute figures themselves.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from balancelab.api.schemas import SnapshotRequest, SyntheticPortfolioRequest
from balancelab.calc.engine import compute_snapshot
from balancelab.domain.models import Portfolio, Snapshot
from balancelab.synthetic.generator import ensure_synthetic, generate_synthetic_portfolio

router = APIRouter(prefix="/v1", tags=["balancelab"])


@router.post(
    "/portfolios/synthetic",
    response_model=Portfolio,
    status_code=status.HTTP_201_CREATED,
)
def create_synthetic_portfolio(request: SyntheticPortfolioRequest) -> Portfolio:
    return generate_synthetic_portfolio(
        seed=request.seed,
        name=request.name,
        currency=request.currency,
        as_of_date=request.as_of_date,
        n_asset_accounts=request.n_asset_accounts,
        n_liability_accounts=request.n_liability_accounts,
    )


@router.post(
    "/snapshots",
    response_model=Snapshot,
    status_code=status.HTTP_201_CREATED,
)
def create_snapshot(request: SnapshotRequest) -> Snapshot:
    portfolio = ensure_synthetic(request.portfolio)
    return compute_snapshot(portfolio)
