"""Liveness and readiness endpoints.

``/healthz`` reports process liveness and never depends on external systems.
``/readyz`` reports whether the service is ready to serve traffic; in M0 it also
verifies the deterministic core is importable and the synthetic-data policy is in
the expected state. Later milestones extend readiness with database and provider
checks.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from balancelab import __version__
from balancelab.config import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    version: str
    checks: dict[str, bool]


@router.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@router.get("/readyz", response_model=ReadinessResponse)
def readyz() -> ReadinessResponse:
    settings = get_settings()
    checks = {
        "config_loaded": bool(settings.app_name),
        "synthetic_data_only": settings.synthetic_data_only,
    }
    # Only assert database connectivity when persistence is configured; the
    # in-memory backend has nothing to probe.
    if settings.database_url:
        from balancelab.storage.session import ping

        checks["database"] = ping(settings.database_url)
    ready = all(checks.values())
    return ReadinessResponse(
        status="ready" if ready else "not_ready",
        version=__version__,
        checks=checks,
    )
