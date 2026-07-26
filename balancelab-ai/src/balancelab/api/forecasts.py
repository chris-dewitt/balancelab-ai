"""Forecast routes.

``POST /v1/forecasts`` runs a stored scenario against its base portfolio and
persists the result. ``GET /v1/forecasts/{id}`` retrieves a run, and
``GET /v1/forecasts/{id}/lineage`` returns just its calculation lineage.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from balancelab.api.dependencies import UowDep
from balancelab.api.schemas import ForecastCreateRequest
from balancelab.calc.forecast import compute_forecast
from balancelab.domain.forecast import ForecastRun
from balancelab.domain.models import CalculationNode
from balancelab.errors import NotFoundError

router = APIRouter(prefix="/v1/forecasts", tags=["forecasts"])


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
    run = uow.forecasts.get(run_id)
    if run is None:
        raise NotFoundError("forecast run not found", details={"run_id": run_id})
    return run


@router.get("/{run_id}/lineage", response_model=list[CalculationNode])
def get_forecast_lineage(run_id: str, uow: UowDep) -> list[CalculationNode]:
    run = uow.forecasts.get(run_id)
    if run is None:
        raise NotFoundError("forecast run not found", details={"run_id": run_id})
    return list(run.lineage)
