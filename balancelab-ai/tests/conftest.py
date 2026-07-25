"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from balancelab.api.app import create_app
from balancelab.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Deterministic test settings with the synthetic-only policy in force."""

    return Settings(environment="test", log_level="warning", synthetic_data_only=True)


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """A TestClient bound to an app built from the test settings."""

    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
