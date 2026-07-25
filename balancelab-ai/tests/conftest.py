"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from balancelab.api.app import create_app
from balancelab.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Deterministic test settings.

    ``database_url`` is pinned to ``None`` so app-level tests always use the
    in-memory backend regardless of any ambient environment variable (CI sets a
    Postgres URL only for the storage-contract and migration checks).
    """

    return Settings(
        environment="test",
        log_level="warning",
        synthetic_data_only=True,
        database_url=None,
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """A TestClient bound to an app built from the test settings."""

    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
