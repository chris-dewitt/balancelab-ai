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

from fastapi import APIRouter, Response, status

from balancelab.api.dependencies import UowDep
from balancelab.api.lineage_http import attach_download_headers, resolve_or_404
from balancelab.api.schemas import SnapshotRequest, SyntheticPortfolioRequest
from balancelab.calc.engine import compute_snapshot
from balancelab.domain.export import SnapshotExport
from balancelab.domain.lineage import LineageGraph, build_lineage_graph
from balancelab.domain.models import CalculationNode, Portfolio, Snapshot
from balancelab.domain.reconciliation import Reconciliation
from balancelab.errors import NotFoundError
from balancelab.export import build_snapshot_export
from balancelab.reconcile import reconcile_snapshot
from balancelab.storage import UnitOfWork
from balancelab.synthetic.generator import ensure_synthetic, generate_synthetic_portfolio

router = APIRouter(prefix="/v1", tags=["balancelab"])


def _load_snapshot(snapshot_id: str, uow: UnitOfWork) -> Snapshot:
    snapshot = uow.snapshots.get(snapshot_id)
    if snapshot is None:
        raise NotFoundError("snapshot not found", details={"snapshot_id": snapshot_id})
    return snapshot


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
    return _load_snapshot(snapshot_id, uow)


@router.get("/snapshots/{snapshot_id}/lineage", response_model=list[CalculationNode])
def get_snapshot_lineage(snapshot_id: str, uow: UowDep) -> list[CalculationNode]:
    return list(_load_snapshot(snapshot_id, uow).lineage)


@router.get("/snapshots/{snapshot_id}/lineage/graph", response_model=LineageGraph)
def get_snapshot_lineage_graph(snapshot_id: str, uow: UowDep) -> LineageGraph:
    return build_lineage_graph(_load_snapshot(snapshot_id, uow).lineage)


# Declared after ``/lineage/graph`` so the literal path wins over ``{node_id}``.
@router.get("/snapshots/{snapshot_id}/lineage/{node_id}", response_model=LineageGraph)
def resolve_snapshot_lineage_node(snapshot_id: str, node_id: str, uow: UowDep) -> LineageGraph:
    return resolve_or_404(_load_snapshot(snapshot_id, uow).lineage, node_id)


@router.get("/snapshots/{snapshot_id}/reconciliation", response_model=Reconciliation)
def get_snapshot_reconciliation(snapshot_id: str, uow: UowDep) -> Reconciliation:
    return reconcile_snapshot(_load_snapshot(snapshot_id, uow))


@router.get("/snapshots/{snapshot_id}/export", response_model=SnapshotExport)
def export_snapshot(snapshot_id: str, uow: UowDep, response: Response) -> SnapshotExport:
    snapshot = _load_snapshot(snapshot_id, uow)
    portfolio = uow.portfolios.get(snapshot.portfolio_id)
    if portfolio is None:
        raise NotFoundError(
            "portfolio for snapshot not found",
            details={"portfolio_id": snapshot.portfolio_id},
        )
    attach_download_headers(response, f"snapshot-{snapshot.id}.json")
    return build_snapshot_export(portfolio, snapshot)
