"""Tests for health and readiness endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_readyz(client: TestClient) -> None:
    response = client.get("/readyz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["config_loaded"] is True
    assert body["checks"]["synthetic_data_only"] is True


def test_correlation_header_is_echoed(client: TestClient) -> None:
    response = client.get("/healthz", headers={"X-Correlation-ID": "test-cid-123"})
    assert response.headers["X-Correlation-ID"] == "test-cid-123"


def test_correlation_header_generated_when_absent(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.headers.get("X-Correlation-ID")
