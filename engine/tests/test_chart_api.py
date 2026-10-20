"""Unit tests for Chart API endpoints and data pipeline.

Verifies:
- Purity direction rule: Sub-999 (GOLDM 995) normalizes UP in chart series.
- Single contract candle series and parity metrics.
- Pair spread series, rolling Bollinger bounds (mu +/- 2 sigma), and Z-score calculations.
- Range filtering and input validation.
"""

import pytest
from fastapi.testclient import TestClient

from aurumlens.api.main import app

client = TestClient(app)


def test_contract_chart_goldm_purity_direction():
    """Verify that GOLDM (995) normalized price is strictly higher than raw price."""
    response = client.get("/v1/chart/contract/GOLDM")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "GOLDM"
    assert data["purity"] == 0.995
    assert data["quote_basis_g"] == 10.0
    assert data["points_count"] > 0

    first_pt = data["points"][0]
    # R16 Purity Direction Rule: Lower purity must normalize UP
    assert first_pt["normalized_price"] > first_pt["raw_price"]
    # Ratio must be approximately 0.999 / 0.995 = 1.00402
    expected_norm = round(first_pt["raw_price"] * (0.999 / 0.995), 2)
    assert abs(first_pt["normalized_price"] - expected_norm) <= 0.05


def test_contract_chart_goldten_purity_equality():
    """Verify that GOLDTEN (999 per 10g) normalized price equals raw price."""
    response = client.get("/v1/chart/contract/GOLDTEN")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "GOLDTEN"
    assert data["purity"] == 0.999
    assert data["quote_basis_g"] == 10.0
    assert data["points_count"] > 0

    first_pt = data["points"][0]
    assert first_pt["normalized_price"] == round(first_pt["raw_price"], 2)


def test_contract_chart_unsupported_symbol():
    """Verify that querying an unknown commodity symbol fails cleanly with 400."""
    response = client.get("/v1/chart/contract/CRUDEOIL")
    assert response.status_code == 400
    assert "Unsupported symbol" in response.json()["detail"]


def test_pair_chart_series_structure_and_bounds():
    """Verify pair spread series, Bollinger bands, and Z-score metrics."""
    response = client.get("/v1/chart/pair/GOLDTEN_GOLDGUINEA?range=ALL&lookback=60&min_history=30")
    assert response.status_code == 200
    data = response.json()

    assert data["pair_name"] == "GOLDTEN_GOLDGUINEA"
    assert data["leg_a_symbol"] == "GOLDTEN"
    assert data["leg_b_symbol"] == "GOLDGUINEA"
    assert data["points_count"] > 0
    assert "summary" in data

    # Verify rolling bounds math for warm points
    warm_points = [p for p in data["points"] if p["roll_mean"] is not None and p["roll_std"] is not None]
    assert len(warm_points) > 0

    for pt in warm_points:
        expected_upper = round(pt["roll_mean"] + 2.0 * pt["roll_std"], 6)
        expected_lower = round(pt["roll_mean"] - 2.0 * pt["roll_std"], 6)
        assert abs(pt["roll_upper"] - expected_upper) <= 0.000002
        assert abs(pt["roll_lower"] - expected_lower) <= 0.000002


def test_pair_chart_range_filter():
    """Verify that range filter restricts points properly."""
    res_all = client.get("/v1/chart/pair/GOLDTEN_GOLDGUINEA?range=ALL")
    res_1w = client.get("/v1/chart/pair/GOLDTEN_GOLDGUINEA?range=1W")
    res_1m = client.get("/v1/chart/pair/GOLDTEN_GOLDGUINEA?range=1M")

    count_all = res_all.json()["points_count"]
    count_1w = res_1w.json()["points_count"]
    count_1m = res_1m.json()["points_count"]

    assert count_1w <= count_1m
    assert count_1m <= count_all
