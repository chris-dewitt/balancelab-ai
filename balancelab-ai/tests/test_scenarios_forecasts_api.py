"""End-to-end API tests for validation, scenarios, and forecasts."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _seed_portfolio(client: TestClient, seed: int = 7) -> dict:
    return client.post("/v1/portfolios/synthetic", json={"seed": seed}).json()


def _create_scenario(client: TestClient, portfolio_id: str) -> dict:
    return client.post(
        "/v1/scenarios",
        json={
            "name": "rate up",
            "base_portfolio_id": portfolio_id,
            "horizon_periods": 3,
            "assumptions": [
                {"target": "asset", "value": "0.05"},
                {"target": "liability", "value": "0.02"},
            ],
        },
    ).json()


# ---- Upload validation endpoint ------------------------------------------------


def test_validate_json_upload_ok(client: TestClient) -> None:
    payload = {
        "name": "U",
        "currency": "USD",
        "as_of_date": "2025-12-31",
        "origin": "synthetic",
        "accounts": [
            {"name": "Cash", "category": "asset", "currency": "USD", "balance": "100.00"},
            {"name": "Debt", "category": "liability", "currency": "USD", "balance": "40.00"},
            {"name": "Eq", "category": "equity", "currency": "USD", "balance": "60.00"},
        ],
    }
    response = client.post("/v1/portfolios/validate", json=payload)
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_validate_csv_upload(client: TestClient) -> None:
    csv_body = (
        "name,category,currency,balance\n"
        "Cash,asset,USD,100.00\n"
        "Debt,liability,USD,40.00\n"
        "Equity,equity,USD,60.00\n"
    )
    response = client.post(
        "/v1/portfolios/validate?origin=synthetic&currency=USD&as_of_date=2025-12-31",
        content=csv_body,
        headers={"content-type": "text/csv"},
    )
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_validate_malformed_json_is_422(client: TestClient) -> None:
    response = client.post(
        "/v1/portfolios/validate",
        content="{not json",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_validate_unsupported_media_type_is_415(client: TestClient) -> None:
    response = client.post(
        "/v1/portfolios/validate", content="x", headers={"content-type": "text/plain"}
    )
    assert response.status_code == 415
    assert response.json()["code"] == "unsupported_media_type"


# ---- Scenario CRUD -------------------------------------------------------------


def test_scenario_crud_roundtrip(client: TestClient) -> None:
    portfolio = _seed_portfolio(client)
    created = _create_scenario(client, portfolio["id"])
    scenario_id = created["id"]

    assert client.get(f"/v1/scenarios/{scenario_id}").status_code == 200
    listing = client.get("/v1/scenarios").json()
    assert any(s["id"] == scenario_id for s in listing)

    assert client.delete(f"/v1/scenarios/{scenario_id}").status_code == 204
    assert client.get(f"/v1/scenarios/{scenario_id}").status_code == 404


def test_scenario_requires_existing_base_portfolio(client: TestClient) -> None:
    response = client.post(
        "/v1/scenarios",
        json={"name": "x", "base_portfolio_id": "port_missing", "horizon_periods": 2},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_scenario_rejects_equity_assumption(client: TestClient) -> None:
    portfolio = _seed_portfolio(client)
    response = client.post(
        "/v1/scenarios",
        json={
            "name": "x",
            "base_portfolio_id": portfolio["id"],
            "horizon_periods": 2,
            "assumptions": [{"target": "equity", "value": "0.1"}],
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_delete_missing_scenario_is_404(client: TestClient) -> None:
    assert client.delete("/v1/scenarios/scen_missing").status_code == 404


# ---- Forecasts -----------------------------------------------------------------


def test_forecast_end_to_end(client: TestClient) -> None:
    portfolio = _seed_portfolio(client)
    scenario = _create_scenario(client, portfolio["id"])

    created = client.post("/v1/forecasts", json={"scenario_id": scenario["id"]})
    assert created.status_code == 201
    run = created.json()
    assert run["horizon_periods"] == 3

    fetched = client.get(f"/v1/forecasts/{run['id']}")
    assert fetched.status_code == 200

    lineage = client.get(f"/v1/forecasts/{run['id']}/lineage")
    assert lineage.status_code == 200
    assert len(lineage.json()) == len(run["lineage"])


def test_forecast_missing_scenario_is_404(client: TestClient) -> None:
    response = client.post("/v1/forecasts", json={"scenario_id": "scen_missing"})
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_get_missing_forecast_is_404(client: TestClient) -> None:
    assert client.get("/v1/forecasts/frun_missing").status_code == 404
