"""Tests for AurumLens FastAPI service."""

import pytest
from fastapi.testclient import TestClient
from aurumlens.api.main import ADMIN_TOKEN, app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "aurumlens-api"
    assert "GOLDM" in data["contracts_supported"]


def test_convert_tool_endpoint():
    response = client.get(
        "/v1/tools/convert",
        params={"source_symbol": "GOLDM", "price": 120000.0, "target_symbol": "GOLDTEN"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source_symbol"] == "GOLDM"
    assert data["target_symbol"] == "GOLDTEN"
    # Target price for GOLDTEN (999) from GOLDM (995) at 120,000 is ~120,482.41
    assert round(data["target_price"], 2) == 120482.41


def test_lot_ratio_tool_endpoint():
    response = client.get(
        "/v1/tools/lot-ratio",
        params={"symbol_a": "GOLDTEN", "symbol_b": "GOLDGUINEA", "max_lots": 20},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lots_a"] == 4
    assert data["lots_b"] == 5
    assert data["residual_fine_g"] == 0.0


def test_hedge_cost_tool_endpoint():
    response = client.get(
        "/v1/tools/hedge-cost",
        params={"target_grams": 500.0, "spot_price": 120482.41},
    )
    assert response.status_code == 200
    options = response.json()
    assert len(options) == 4
    # Rank 1 should be GOLDM (lowest cost per 10g)
    assert options[0]["symbol"] == "GOLDM"
    assert options[0]["rank"] == 1
    # Rank 4 should be GOLDPETAL (due to flat broker fee on 500 lots)
    assert options[-1]["symbol"] == "GOLDPETAL"
    assert options[-1]["cost_per_10g_inr"] > options[0]["cost_per_10g_inr"]


def test_explain_endpoint_bilingual():
    # English
    resp_en = client.get("/v1/signals/sig_test_01/explain", params={"lang": "en"})
    assert resp_en.status_code == 200
    data_en = resp_en.json()
    assert data_en["language"] == "en"
    assert "GOLDTEN" in data_en["explanation"]
    assert data_en["passed_numeric_guard"] is True

    # Hindi
    resp_hi = client.get("/v1/signals/sig_test_01/explain", params={"lang": "hi"})
    assert resp_hi.status_code == 200
    data_hi = resp_hi.json()
    assert data_hi["language"] == "hi"
    assert data_hi["passed_numeric_guard"] is True


def test_evidence_export_endpoints():
    # CSV
    resp_csv = client.get("/v1/signals/sig_test_01/evidence.csv")
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]
    assert "sig_test_01" in resp_csv.text

    # HTML
    resp_html = client.get("/v1/signals/sig_test_01/evidence.html")
    assert resp_html.status_code == 200
    assert "text/html" in resp_html.headers["content-type"]
    assert "<!DOCTYPE html>" in resp_html.text
    assert "sig_test_01" in resp_html.text


def test_admin_refresh_unauthorized():
    # No token
    resp = client.post("/v1/admin/refresh")
    assert resp.status_code == 401

    # Invalid token
    resp_invalid = client.post("/v1/admin/refresh", headers={"Authorization": "Bearer wrong-token"})
    assert resp_invalid.status_code == 403


def test_admin_refresh_authorized():
    resp = client.post(
        "/v1/admin/refresh",
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["action"] == "PIPELINE_SYNC"
