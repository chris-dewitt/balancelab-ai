"""FastAPI application factory.

The factory wires configuration, logging, correlation-ID middleware, structured
exception handlers, and the v1 routes. Keeping construction in a factory (rather
than a module-level singleton) makes it straightforward to build isolated app
instances in tests.
"""

from __future__ import annotations

from fastapi import FastAPI

from balancelab import __version__
from balancelab.api.errors import register_exception_handlers
from balancelab.api.health import router as health_router
from balancelab.api.middleware import CorrelationIdMiddleware
from balancelab.api.routes import router as v1_router
from balancelab.config import Settings, get_settings
from balancelab.storage import create_unit_of_work_factory
from balancelab.telemetry import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure a FastAPI application instance."""

    cfg = settings or get_settings()
    configure_logging(cfg.log_level)

    app = FastAPI(
        title="BalanceLab AI",
        version=__version__,
        summary="Deterministic synthetic balance-sheet forecasting core.",
    )

    # Choose the storage backend once (Postgres when configured, else in-memory).
    app.state.settings = cfg
    app.state.uow_factory = create_unit_of_work_factory(cfg)

    app.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(v1_router)

    return app


# Module-level app for ``uvicorn balancelab.api.app:app``.
app = create_app()
