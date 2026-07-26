"""v1 API routes.

The deterministic path is now persisted:

* ``POST /v1/portfolios/synthetic`` generates a reproducible synthetic portfolio
  and stores it.
* ``POST /v1/snapshots`` computes a fully-traced snapshot (enforcing the
  synthetic-data boundary), stores the portfolio and snapshot, and returns the
  snapshot.
* ``GET /v1/portfolios/{id}`` and ``GET /v1/snapshots/{id}`` retrieve stored
  records, returning a structured 404 when absent.

Authoritative arithmetic happens only in :mod:`balancelab.calc`; these handlers
orchestrate typed inputs, persistence, and outputs.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from balancelab.api.dependencies import UowDep
from balancelab.api.schemas import SnapshotRequest, SyntheticPortfolioRequest
from balancelab.calc.engine import compute_snapshot
from balancelab.domain.models import Portfolio, Snapshot
from balancelab.errors import NotFoundError
from balancelab.synthetic.generator import ensure_synthetic, generate_synthetic_portfolio

router = APIRouter(prefix="/v1", tags=["balancelab"])


@router.post(
    "/portfolios/synthetic",
    response_model=Portfolio,
    status_code=status.HTTP_201_CREATED,
)
def create_synthetic_portfolio(
    request: SyntheticPortfolioRequest,
    uow: UowDep,
) -> Portfolio:
    portfolio = generate_synthetic_portfolio(
        seed=request.seed,
        name=request.name,
        currency=request.currency,
        as_of_date=request.as_of_date,
        n_asset_accounts=request.n_asset_accounts,
        n_liability_accounts=request.n_liability_accounts,
    )
    return uow.portfolios.add(portfolio)


@router.get("/portfolios/{portfolio_id}", response_model=Portfolio)
def get_portfolio(portfolio_id: str, uow: UowDep) -> Portfolio:
    portfolio = uow.portfolios.get(portfolio_id)
    if portfolio is None:
        raise NotFoundError("portfolio not found", details={"portfolio_id": portfolio_id})
    return portfolio


@router.post(
    "/snapshots",
    response_model=Snapshot,
    status_code=status.HTTP_201_CREATED,
)
def create_snapshot(
    request: SnapshotRequest,
    uow: UowDep,
) -> Snapshot:
    portfolio = ensure_synthetic(request.portfolio)
    snapshot = compute_snapshot(portfolio)
    # Persist the input portfolio (idempotent) so the snapshot's portfolio_id
    # always resolves, then the snapshot itself.
    uow.portfolios.add(portfolio)
    return uow.snapshots.add(snapshot)


@router.get("/snapshots/{snapshot_id}", response_model=Snapshot)
def get_snapshot(snapshot_id: str, uow: UowDep) -> Snapshot:
    snapshot = uow.snapshots.get(snapshot_id)
    if snapshot is None:
        raise NotFoundError("snapshot not found", details={"snapshot_id": snapshot_id})
    return snapshot
