"""Scenario CRUD routes.

Scenarios are created against an existing base portfolio, retrieved and listed,
and deleted. Following the domain's immutability rule, there is no in-place
update: a correction is a new scenario. Creation validates that the referenced
base portfolio exists and that the assumptions are well-formed.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status
from pydantic import ValidationError as PydanticValidationError

from balancelab.api.dependencies import UowDep
from balancelab.api.errors import sanitize_validation_errors
from balancelab.api.schemas import ScenarioCreateRequest
from balancelab.domain.scenario import Assumption, Scenario
from balancelab.errors import NotFoundError, ValidationError

router = APIRouter(prefix="/v1/scenarios", tags=["scenarios"])


def _build_scenario(request: ScenarioCreateRequest) -> Scenario:
    """Construct a domain Scenario, translating domain validation to 422s."""

    try:
        assumptions = tuple(
            Assumption(
                target=a.target,
                kind=a.kind,
                value=a.value,
                description=a.description,
            )
            for a in request.assumptions
        )
        return Scenario(
            name=request.name,
            description=request.description,
            base_portfolio_id=request.base_portfolio_id,
            horizon_periods=request.horizon_periods,
            assumptions=assumptions,
        )
    except PydanticValidationError as exc:
        raise ValidationError(
            "invalid scenario",
            details={"errors": sanitize_validation_errors(exc.errors())},
        ) from exc


@router.post("", response_model=Scenario, status_code=status.HTTP_201_CREATED)
def create_scenario(request: ScenarioCreateRequest, uow: UowDep) -> Scenario:
    if uow.portfolios.get(request.base_portfolio_id) is None:
        raise NotFoundError(
            "base portfolio not found",
            details={"base_portfolio_id": request.base_portfolio_id},
        )
    scenario = _build_scenario(request)
    return uow.scenarios.add(scenario)


@router.get("", response_model=list[Scenario])
def list_scenarios(
    uow: UowDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Scenario]:
    return list(uow.scenarios.list(limit=limit, offset=offset))


@router.get("/{scenario_id}", response_model=Scenario)
def get_scenario(scenario_id: str, uow: UowDep) -> Scenario:
    scenario = uow.scenarios.get(scenario_id)
    if scenario is None:
        raise NotFoundError("scenario not found", details={"scenario_id": scenario_id})
    return scenario


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(scenario_id: str, uow: UowDep) -> None:
    if not uow.scenarios.delete(scenario_id):
        raise NotFoundError("scenario not found", details={"scenario_id": scenario_id})
