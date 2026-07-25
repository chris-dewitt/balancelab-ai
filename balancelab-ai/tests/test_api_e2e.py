"""End-to-end API test for the signature M0 path.

Exercises the full representative flow through the HTTP surface:
generate a synthetic portfolio, compute its snapshot, and verify the balance
identity holds and every total is backed by lineage. Also covers the malformed
input and reconciliation-failure error paths, which must return structured
error bodies with a correlation ID.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_synthetic_to_snapshot_end_to_end(client: TestClient) -> None:
    # 1. Generate a reproducible synthetic portfolio.
    gen = client.post("/v1/portfolios/synthetic", json={"seed": 2025})
    assert gen.status_code == 201
    portfolio = gen.json()
    assert portfolio["provenance"]["origin"] == "synthetic"

    # 2. Compute a fully-traced snapshot for it.
    snap = client.post("/v1/snapshots", json={"portfolio": portfolio})
    assert snap.status_code == 201
    snapshot = snap.json()

    # 3. The balance-sheet identity holds and totals trace to lineage.
    assert snapshot["balances"] is True
    labels = {node["label"] for node in snapshot["lineage"]}
    assert {"total_asset", "total_liability", "total_equity", "balance_residual"} <= labels


def test_persisted_portfolio_and_snapshot_are_retrievable(client: TestClient) -> None:
    portfolio = client.post("/v1/portfolios/synthetic", json={"seed": 314}).json()
    fetched_portfolio = client.get(f"/v1/portfolios/{portfolio['id']}")
    assert fetched_portfolio.status_code == 200
    assert fetched_portfolio.json()["id"] == portfolio["id"]

    snapshot = client.post("/v1/snapshots", json={"portfolio": portfolio}).json()
    fetched_snapshot = client.get(f"/v1/snapshots/{snapshot['id']}")
    assert fetched_snapshot.status_code == 200
    assert fetched_snapshot.json()["id"] == snapshot["id"]
    # The snapshot's portfolio was persisted too, so it resolves.
    assert client.get(f"/v1/portfolios/{snapshot['portfolio_id']}").status_code == 200


def test_missing_records_return_structured_404(client: TestClient) -> None:
    for path in ("/v1/portfolios/port_missing", "/v1/snapshots/snap_missing"):
        response = client.get(path)
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "not_found"
        assert body["correlation_id"]


def test_generation_is_reproducible_over_the_wire(client: TestClient) -> None:
    a = client.post("/v1/portfolios/synthetic", json={"seed": 11}).json()
    b = client.post("/v1/portfolios/synthetic", json={"seed": 11}).json()
    assert [x["balance"] for x in a["accounts"]] == [x["balance"] for x in b["accounts"]]


def test_malformed_request_returns_structured_error(client: TestClient) -> None:
    response = client.post("/v1/portfolios/synthetic", json={"seed": -1})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["correlation_id"]


def test_unbalanced_portfolio_returns_reconciliation_error(client: TestClient) -> None:
    portfolio = client.post("/v1/portfolios/synthetic", json={"seed": 5}).json()
    # Corrupt one account's balance so the identity no longer holds.
    portfolio["accounts"][0]["balance"] = "0.01"
    response = client.post("/v1/snapshots", json={"portfolio": portfolio})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "reconciliation_failed"
    assert "residual" in body["details"]
    assert body["correlation_id"]
