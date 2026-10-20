"""Unit tests for Unified AurumLens AI Chatbot API.

Verifies:
- 5-domain intent routing (Guide, Diagnostics, Portfolio, Order Staging, Risk Stress).
- Strict NumericGuard verification (zero hallucinated numbers).
- Two-phase staged execution action card generation.
- Bilingual English and Hindi response formats.
- Quick prompt suggestion chips.
"""

import pytest
from fastapi.testclient import TestClient

from aurumlens.api.main import app

client = TestClient(app)


def test_chat_trading_guide_purity():
    """Verify chatbot answers purity normalization question with Rule R16."""
    res = client.post("/v1/chat", json={"message": "How does GOLDM 995 purity normalization work?", "language": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "trading_guide"
    assert "Rule R16" in data["message"]
    assert "0.999" in data["message"] or "999" in data["message"]
    assert data["passed_numeric_guard"] is True


def test_chat_signal_diagnostics_nearest_miss():
    """Verify chatbot explains nearest-miss gate failure with verified figures."""
    res = client.post("/v1/chat", json={"message": "Why was the GOLDTEN-GOLDGUINEA signal blocked on Oct 1st?", "language": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "signal_diagnostics"
    assert data["tool_called"] == "get_signal_evidence"
    assert "1.67" in data["message"]
    assert "2.0" in data["message"]
    assert "11" in data["message"]
    assert data["passed_numeric_guard"] is True


def test_chat_portfolio_summary():
    """Verify chatbot retrieves active paper portfolio and margin status."""
    res = client.post("/v1/chat", json={"message": "Check my paper portfolio & margin balance", "language": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "paper_portfolio"
    assert data["tool_called"] == "get_portfolio_summary"
    assert "194200" in data["message"] or "Margin" in data["message"]
    assert data["passed_numeric_guard"] is True


def test_chat_stage_order_proposal_card():
    """Verify chatbot stages an order and returns an actionable proposal card without auto-executing."""
    res = client.post("/v1/chat", json={"message": "Stage a paper trade on GOLDTEN-GOLDGUINEA", "language": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "stage_order"
    assert data["tool_called"] == "stage_paper_order"
    assert data["action_card"] is not None
    assert data["action_card"]["type"] == "stage_proposal"
    assert "prop_" in data["action_card"]["proposal_id"]
    assert data["action_card"]["margin"] > 0
    assert data["passed_numeric_guard"] is True


def test_chat_what_if_risk_stress():
    """Verify chatbot simulates a 5% gold drop and reports stressed equity."""
    res = client.post("/v1/chat", json={"message": "What happens if gold drops 5% and spread moves 50 bps?", "language": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "risk_stress"
    assert data["tool_called"] == "simulate_risk_stress"
    assert "Stress Simulation" in data["message"]
    assert data["passed_numeric_guard"] is True


def test_chat_hindi_response():
    """Verify bilingual Hindi response generation passing numeric guard."""
    res = client.post("/v1/chat", json={"message": "तनाव विश्लेषण (Stress Test) दिखाओ", "language": "hi"})
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "hi"
    assert "तनाव" in data["message"] or "इक्विटी" in data["message"]
    assert data["passed_numeric_guard"] is True


def test_chat_suggestions():
    """Verify suggestions endpoint returns quick starter chips."""
    res = client.get("/v1/chat/suggestions")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 4
    assert any(s["id"] == "diag" for s in data)
