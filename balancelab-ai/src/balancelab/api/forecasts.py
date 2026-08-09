"""Forecast routes.

``POST /v1/forecasts`` runs a stored scenario against its base portfolio and
persists the result. The remaining routes retrieve a run and expose its
calculation lineage (flat and as a graph), a resolvable per-node explanation,
its reconciliation, and a downloadable export bundle.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from balancelab.api.dependencies import UowDep
from balancelab.api.lineage_http import attach_download_headers, resolve_or_404
from balancelab.api.schemas import ForecastCreateRequest
from balancelab.calc.forecast import compute_forecast
from balancelab.domain.export import ForecastExport
from balancelab.domain.forecast import ForecastRun
from balancelab.domain.lineage import LineageGraph, build_lineage_graph
from balancelab.domain.models import CalculationNode
from balancelab.domain.reconciliation import Reconciliation
from balancelab.errors import NotFoundError
from balancelab.export import build_forecast_export
from balancelab.reconcile import reconcile_forecast
from balancelab.storage import UnitOfWork

router = APIRouter(prefix="/v1/forecasts", tags=["forecasts"])


def _load_run(run_id: str, uow: UnitOfWork) -> ForecastRun:
    run = uow.forecasts.get(run_id)
    if run is None:
        raise NotFoundError("forecast run not found", details={"run_id": run_id})
    return run


@router.post("", response_model=ForecastRun, status_code=status.HTTP_201_CREATED)
def create_forecast(request: ForecastCreateRequest, uow: UowDep) -> ForecastRun:
    scenario = uow.scenarios.get(request.scenario_id)
    if scenario is None:
        raise NotFoundError("scenario not found", details={"scenario_id": request.scenario_id})
    portfolio = uow.portfolios.get(scenario.base_portfolio_id)
    if portfolio is None:
        raise NotFoundError(
            "base portfolio not found",
            details={"base_portfolio_id": scenario.base_portfolio_id},
        )
    run = compute_forecast(portfolio, scenario)
    return uow.forecasts.add(run)


@router.get("/{run_id}", response_model=ForecastRun)
def get_forecast(run_id: str, uow: UowDep) -> ForecastRun:
    return _load_run(run_id, uow)


@router.get("/{run_id}/lineage", response_model=list[CalculationNode])
def get_forecast_lineage(run_id: str, uow: UowDep) -> list[CalculationNode]:
    return list(_load_run(run_id, uow).lineage)


@router.get("/{run_id}/lineage/graph", response_model=LineageGraph)
def get_forecast_lineage_graph(run_id: str, uow: UowDep) -> LineageGraph:
    return build_lineage_graph(_load_run(run_id, uow).lineage)


# Declared after ``/lineage/graph`` so the literal path wins over ``{node_id}``.
@router.get("/{run_id}/lineage/{node_id}", response_model=LineageGraph)
def resolve_forecast_lineage_node(run_id: str, node_id: str, uow: UowDep) -> LineageGraph:
    return resolve_or_404(_load_run(run_id, uow).lineage, node_id)


@router.get("/{run_id}/reconciliation", response_model=Reconciliation)
def get_forecast_reconciliation(run_id: str, uow: UowDep) -> Reconciliation:
    return reconcile_forecast(_load_run(run_id, uow))


@router.get("/{run_id}/export", response_model=ForecastExport)
def export_forecast(run_id: str, uow: UowDep, response: Response) -> ForecastExport:
    run = _load_run(run_id, uow)
    scenario = uow.scenarios.get(run.scenario_id)
    if scenario is None:
        raise NotFoundError(
            "scenario for forecast not found", details={"scenario_id": run.scenario_id}
        )
    portfolio = uow.portfolios.get(run.base_portfolio_id)
    if portfolio is None:
        raise NotFoundError(
            "portfolio for forecast not found",
            details={"base_portfolio_id": run.base_portfolio_id},
        )
    attach_download_headers(response, f"forecast-{run.id}.json")
    return build_forecast_export(portfolio, scenario, run)
