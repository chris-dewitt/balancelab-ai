"""End-to-end API tests for lineage graph, reconciliation, and export routes."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _snapshot(client: TestClient, seed: int = 7) -> dict:
    portfolio = client.post("/v1/portfolios/synthetic", json={"seed": seed}).json()
    return client.post("/v1/snapshots", json={"portfolio": portfolio}).json()


def _forecast(client: TestClient, seed: int = 7) -> dict:
    portfolio = client.post("/v1/portfolios/synthetic", json={"seed": seed}).json()
    scenario = client.post(
        "/v1/scenarios",
        json={
            "name": "s",
            "base_portfolio_id": portfolio["id"],
            "horizon_periods": 3,
            "assumptions": [
                {"target": "asset", "value": "0.05"},
                {"target": "liability", "value": "0.02"},
            ],
        },
    ).json()
    return client.post("/v1/forecasts", json={"scenario_id": scenario["id"]}).json()


# ---- Snapshot lineage / reconciliation / export --------------------------------


def test_snapshot_lineage_graph(client: TestClient) -> None:
    snapshot = _snapshot(client)
    graph = client.get(f"/v1/snapshots/{snapshot['id']}/lineage/graph")
    assert graph.status_code == 200
    body = graph.json()
    assert body["nodes"] and body["edges"]
    assert len(body["root_ids"]) == 1


def test_snapshot_lineage_node_resolution(client: TestClient) -> None:
    snapshot = _snapshot(client)
    graph = client.get(f"/v1/snapshots/{snapshot['id']}/lineage/graph").json()
    root_id = graph["root_ids"][0]
    resolved = client.get(f"/v1/snapshots/{snapshot['id']}/lineage/{root_id}")
    assert resolved.status_code == 200
    # Resolving the reconciliation root pulls in the whole graph.
    assert len(resolved.json()["nodes"]) == len(graph["nodes"])

    missing = client.get(f"/v1/snapshots/{snapshot['id']}/lineage/calc_missing")
    assert missing.status_code == 404
    assert missing.json()["code"] == "not_found"


def test_snapshot_reconciliation_endpoint(client: TestClient) -> None:
    snapshot = _snapshot(client)
    recon = client.get(f"/v1/snapshots/{snapshot['id']}/reconciliation")
    assert recon.status_code == 200
    assert recon.json()["passed"] is True


def test_snapshot_export_downloads(client: TestClient) -> None:
    snapshot = _snapshot(client)
    export = client.get(f"/v1/snapshots/{snapshot['id']}/export")
    assert export.status_code == 200
    assert "attachment" in export.headers["content-disposition"]
    body = export.json()
    assert body["schema_version"]
    assert body["snapshot"]["id"] == snapshot["id"]
    assert body["reconciliation"]["passed"] is True


def test_snapshot_subresources_404_when_absent(client: TestClient) -> None:
    for suffix in ("lineage/graph", "reconciliation", "export"):
        response = client.get(f"/v1/snapshots/snap_missing/{suffix}")
        assert response.status_code == 404


# ---- Forecast lineage / reconciliation / export --------------------------------


def test_forecast_lineage_graph_and_export(client: TestClient) -> None:
    run = _forecast(client)
    graph = client.get(f"/v1/forecasts/{run['id']}/lineage/graph")
    assert graph.status_code == 200
    assert graph.json()["nodes"]

    recon = client.get(f"/v1/forecasts/{run['id']}/reconciliation")
    assert recon.status_code == 200
    assert recon.json()["passed"] is True
    assert len(recon.json()["checks"]) == run["horizon_periods"] + 1

    export = client.get(f"/v1/forecasts/{run['id']}/export")
    assert export.status_code == 200
    assert "attachment" in export.headers["content-disposition"]
    assert export.json()["forecast"]["id"] == run["id"]


def test_forecast_subresources_404_when_absent(client: TestClient) -> None:
    for suffix in ("lineage/graph", "reconciliation", "export"):
        response = client.get(f"/v1/forecasts/frun_missing/{suffix}")
        assert response.status_code == 404
