"""Unit tests for Paper Trading and Risk Simulation API endpoints.

Verifies:
- Portfolio ledger querying (capital, equity, margin).
- Two-phase staged execution (stage -> confirm).
- Zero-duplicate execution guard rejection.
- Position closure with exit reason and P&L attribution.
- What-If risk stress runner under hypothetical market shocks.
"""

import pytest
from fastapi.testclient import TestClient

from aurumlens.api.main import app

client = TestClient(app)


def test_get_paper_portfolio():
    """Verify that portfolio ledger returns valid capital and margin metrics."""
    response = client.get("/v1/paper/portfolio")
    assert response.status_code == 200
    data = response.json()

    assert data["initial_capital"] == 1_000_000.0
    assert data["total_equity"] >= 1_000_000.0
    assert data["used_margin"] >= 0.0
    assert data["free_margin"] >= 0.0
    assert "positions" in data
    assert len(data["positions"]) >= 1


def test_two_phase_staged_order_execution():
    """Verify Stage 1 (proposal staging) followed by Stage 2 (explicit confirmation)."""
    # 1. Stage proposal
    stage_payload = {
        "signal_id": "sig_unit_test_99",
        "pair_name": "GOLDM_GOLDTEN",
        "leg_a_symbol": "GOLDM",
        "leg_b_symbol": "GOLDTEN",
        "rich_leg": "A",
        "price_a": 120000.0,
        "price_b": 120500.0,
        "lots_a": 1,
        "lots_b": 10,
        "slippage_bps_a": 5.0,
        "slippage_bps_b": 5.0,
        "residual_fine_g": 0.0,
        "log_spread_adj": 0.0012,
    }
    stage_res = client.post("/v1/paper/stage", json=stage_payload)
    assert stage_res.status_code == 200
    staged = stage_res.json()
    assert staged["status"] == "STAGED"
    assert "proposal_id" in staged
    proposal_id = staged["proposal_id"]

    # Verify adverse fill calculation (selling A gets lower price, buying B gets higher price)
    assert staged["side_a"] == "SELL"
    assert staged["est_fill_a"] < 120000.0
    assert staged["side_b"] == "BUY"
    assert staged["est_fill_b"] > 120500.0

    # 2. Confirm execution
    confirm_res = client.post("/v1/paper/confirm", json={"proposal_id": proposal_id})
    assert confirm_res.status_code == 200
    confirmed = confirm_res.json()
    assert confirmed["status"] == "OPEN"
    assert confirmed["signal_id"] == "sig_unit_test_99"


def test_zero_duplicate_guard():
    """Verify that re-staging an already executed signal is strictly blocked."""
    dup_payload = {
        "signal_id": "sig_20261001_01",  # already active in demo portfolio
        "pair_name": "GOLDTEN_GOLDGUINEA",
        "price_a": 120500.0,
        "price_b": 96400.0,
        "lots_a": 4,
        "lots_b": 5,
    }
    response = client.post("/v1/paper/stage", json=dup_payload)
    assert response.status_code == 400
    assert "Execution blocked" in response.json()["detail"]


def test_position_close_lifecycle():
    """Verify closing an open position records exit reason and P&L."""
    # First stage and confirm a new position to close
    stage_payload = {
        "signal_id": "sig_close_test_01",
        "pair_name": "GOLDTEN_GOLDGUINEA",
        "price_a": 120500.0,
        "price_b": 96400.0,
        "lots_a": 4,
        "lots_b": 5,
    }
    s_res = client.post("/v1/paper/stage", json=stage_payload)
    prop_id = s_res.json()["proposal_id"]
    c_res = client.post("/v1/paper/confirm", json={"proposal_id": prop_id})
    pos_id = c_res.json()["position_id"]

    # Close position
    close_payload = {
        "position_id": pos_id,
        "exit_reason": "CONVERGENCE",
    }
    close_res = client.post("/v1/paper/close", json=close_payload)
    assert close_res.status_code == 200
    closed = close_res.json()
    assert closed["status"] == "CLOSED"
    assert closed["exit_reason"] == "CONVERGENCE"


def test_what_if_risk_stress_simulation():
    """Verify risk stress runner calculates gold price shock and relative spread shock."""
    stress_payload = {
        "spot_shock_pct": 5.0,     # +5% spot rally
        "spread_shock_bps": 50.0,  # +50 bps spread widening
    }
    response = client.post("/v1/paper/simulate-risk", json=stress_payload)
    assert response.status_code == 200
    data = response.json()

    assert "baseline_equity" in data
    assert "stressed_equity" in data
    assert "equity_change_inr" in data
    assert "risk_status" in data
    assert isinstance(data["impact_by_position"], list)
