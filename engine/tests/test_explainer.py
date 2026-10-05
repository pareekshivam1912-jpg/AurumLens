"""Tests for explainer and numeric guard (Rule R25)."""

import pytest
from aurumlens.explain.numeric_guard import (
    NumericGuardViolationError,
    assert_numeric_guard,
    verify_numeric_guard,
)
from aurumlens.explain.explainer import SignalExplainer


@pytest.fixture
def sample_evidence():
    return {
        "signal_id": "sig_20261001_01",
        "trade_date": "2026-10-01",
        "pair_name": "GOLDTEN_GOLDGUINEA",
        "leg_a_symbol": "GOLDTEN",
        "leg_b_symbol": "GOLDGUINEA",
        "quoted_price_a": 120500.0,
        "quoted_price_b": 96400.0,
        "zscore": 2.42,
        "lookback_days": 60,
        "expected_convergence_inr": 580.0,
        "total_costs_inr": 170.0,
        "slippage_inr": 50.0,
        "net_expected_edge_inr": 310.0,
        "pair_fine_grams": 40.0,
        "lots_a": 4,
        "lots_b": 5,
        "residual_fine_g": 0.0,
        "status": "ALERT",
        "reason_codes": [],
        "gate_results": [{"passed": True}] * 12,
    }


def test_numeric_guard_passes_on_valid_data(sample_evidence):
    sample_evidence["edge_per_10g"] = 77.50
    text = "On 2026-10-01, GOLDTEN (₹1,20,500.0) has z = 2.42. Net edge is +₹310.0. Ratio is 4 to 5 with 0.0g residual."
    assert verify_numeric_guard(text, sample_evidence) is True


def test_numeric_guard_catches_hallucinated_number(sample_evidence):
    # Text mentions a fabricated number (99999.0) not present anywhere in evidence
    text = "On 2026-10-01, GOLDTEN price is ₹99,999.00 and z = 2.42."
    assert verify_numeric_guard(text, sample_evidence) is False
    with pytest.raises(NumericGuardViolationError):
        assert_numeric_guard(text, sample_evidence)


def test_english_explanation_generation(sample_evidence):
    explainer = SignalExplainer()
    res = explainer.explain(sample_evidence, language="en")
    assert res.language == "en"
    assert res.status == "ALERT"
    assert "GOLDTEN" in res.text
    assert "GOLDGUINEA" in res.text
    assert "2.42" in res.text
    assert "310.00" in res.text
    assert res.passed_numeric_guard is True


def test_hindi_explanation_generation(sample_evidence):
    explainer = SignalExplainer()
    res = explainer.explain(sample_evidence, language="hi")
    assert res.language == "hi"
    assert res.status == "ALERT"
    assert "मानकीकृत" in res.text or "मानक विचलन" in res.text
    assert "2.42" in res.text
    assert res.passed_numeric_guard is True


def test_nearest_miss_explanation():
    near_miss_evidence = {
        "signal_id": "sig_20261001_02",
        "trade_date": "2026-10-01",
        "pair_name": "GOLDTEN_GOLDM",
        "zscore": 1.67,
        "entry_z": 2.0,
        "status": "QUIET",
        "reason_codes": ["Z_BELOW_THRESHOLD"],
        "gate_results": [{"passed": True}] * 11 + [{"passed": False}],
    }
    explainer = SignalExplainer()
    res = explainer.explain(near_miss_evidence, language="en", is_nearest_miss=True)
    assert res.status == "QUIET"
    assert "1.67" in res.text
    assert "Z_BELOW_THRESHOLD" in res.text
    assert res.passed_numeric_guard is True
