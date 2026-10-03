"""Tests for the 11-gate evaluator and evidence records (Design §6.11, R20).

Mandatory test coverage from Phase.md §3:
- A planted anomaly triggers ALERT (all gates pass)
- Ordinary days stay QUIET
- Cost failure blocks the alert
- Liquidity failure blocks the alert
- Expiry failure blocks the alert
- SUSPECT price blocks the alert
- Pair failing several gates reports ALL of them
- Constant structural offset never alerts (convergence to mean, not zero)
- Strict mode with DISPUTED spec gives SPEC_UNVERIFIED
- Changing future data cannot change past signals (no look-ahead)
"""

from datetime import date
import pytest

from aurumlens.signal.gates import (
    GateConfig,
    GateResult,
    PairDayInput,
    collect_reason_codes,
    determine_status,
    evaluate_gates,
)
from aurumlens.signal.evidence import build_evidence_record
from aurumlens.signal.nearest_miss import compute_near_miss, rank_near_misses


def _make_alert_input(**overrides) -> PairDayInput:
    """Factory: a pair-day that passes ALL gates (ALERT)."""
    defaults = dict(
        pair_name="GOLDTEN_GOLDM",
        trade_date=date(2026, 10, 1),
        spec_mode="research",
        spec_status_a="VERIFIED_OFFICIAL",
        spec_status_b="VERIFIED_OFFICIAL",
        purity_status_a="VERIFIED_OFFICIAL",
        purity_status_b="VERIFIED_OFFICIAL",
        quality_a="OK",
        quality_b="OK",
        has_expiry_pair=True,
        expiry_gap_days=5,
        days_to_expiry_a=25,
        days_to_expiry_b=20,
        history_count=60,
        zscore=2.5,
        volume_a=100,
        volume_b=80,
        oi_a=500,
        oi_b=300,
        expected_convergence_inr=500.0,
        total_costs_inr=100.0,
        slippage_inr=50.0,
        safety_buffer_inr=20.0,
        is_duplicate=False,
    )
    defaults.update(overrides)
    return PairDayInput(**defaults)


def _default_config() -> GateConfig:
    return GateConfig(
        entry_z=2.0,
        min_history_obs=30,
        max_expiry_gap_days=35,
        min_volume=10,
        min_oi=50,
        unsafe_expiry_window_days=5,
    )


def test_planted_anomaly_triggers_alert():
    """A pair-day where all gates pass must return ALERT."""
    inp = _make_alert_input()
    cfg = _default_config()
    results = evaluate_gates(inp, cfg)

    assert len(results) == 12  # all 12 gates evaluated
    assert all(g.passed for g in results), f"Failing gates: {[g.gate_name for g in results if not g.passed]}"
    assert determine_status(results) == "ALERT"
    assert collect_reason_codes(results) == []


def test_ordinary_day_stays_quiet():
    """Low z-score (ordinary day) stays QUIET."""
    inp = _make_alert_input(zscore=0.5)  # below entry_z=2.0
    results = evaluate_gates(inp, _default_config())

    assert determine_status(results) == "QUIET"
    reasons = collect_reason_codes(results)
    assert "Z_BELOW_THRESHOLD" in reasons


def test_cost_failure_blocks_alert():
    """When costs exceed expected convergence, COST_HURDLE_FAIL blocks alert."""
    inp = _make_alert_input(
        expected_convergence_inr=50.0,
        total_costs_inr=100.0,
        slippage_inr=50.0,
        safety_buffer_inr=20.0,
    )
    results = evaluate_gates(inp, _default_config())

    assert determine_status(results) == "QUIET"
    reasons = collect_reason_codes(results)
    assert "COST_HURDLE_FAIL" in reasons


def test_liquidity_failure_blocks_alert():
    """Low volume on leg A blocks the alert with LIQUIDITY_VOLUME_A."""
    inp = _make_alert_input(volume_a=3)  # below min_volume=10
    results = evaluate_gates(inp, _default_config())

    assert determine_status(results) == "QUIET"
    reasons = collect_reason_codes(results)
    assert "LIQUIDITY_VOLUME_A" in reasons


def test_expiry_failure_blocks_alert():
    """Leg too close to expiry (within unsafe window) blocks with EXPIRY_UNSAFE."""
    inp = _make_alert_input(days_to_expiry_a=3)  # within 5-day window
    results = evaluate_gates(inp, _default_config())

    assert determine_status(results) == "QUIET"
    reasons = collect_reason_codes(results)
    assert any("EXPIRY_UNSAFE" in r for r in reasons)


def test_suspect_price_blocks_alert():
    """SUSPECT data quality blocks with DATA_SUSPECT."""
    inp = _make_alert_input(quality_a="SUSPECT")
    results = evaluate_gates(inp, _default_config())

    assert determine_status(results) == "QUIET"
    reasons = collect_reason_codes(results)
    assert any("DATA_SUSPECT" in r for r in reasons)


def test_multiple_failures_report_all_reason_codes():
    """R20: ALL gates evaluated, multiple failures each reported."""
    inp = _make_alert_input(
        zscore=0.3,           # Z_BELOW_THRESHOLD
        volume_a=2,           # LIQUIDITY_VOLUME_A
        oi_b=10,              # LIQUIDITY_OI_B
        days_to_expiry_a=2,   # EXPIRY_UNSAFE
    )
    results = evaluate_gates(inp, _default_config())

    assert determine_status(results) == "QUIET"
    reasons = collect_reason_codes(results)

    # Must have ALL failures reported (R20), not just the first one
    assert "Z_BELOW_THRESHOLD" in reasons
    assert "LIQUIDITY_VOLUME_A" in reasons
    assert "LIQUIDITY_OI_B" in reasons
    assert any("EXPIRY_UNSAFE" in r for r in reasons)
    assert len(reasons) >= 4


def test_strict_mode_disputed_spec_gives_spec_unverified():
    """R24: strict mode with DISPUTED spec -> SPEC_UNVERIFIED -> QUIET."""
    inp = _make_alert_input(
        spec_mode="strict",
        purity_status_a="DISPUTED",
    )
    results = evaluate_gates(inp, _default_config())

    assert determine_status(results) == "QUIET"
    reasons = collect_reason_codes(results)
    assert "SPEC_UNVERIFIED" in reasons


def test_research_mode_disputed_spec_passes():
    """R24: research mode always passes SPEC_OK (but watermarked)."""
    inp = _make_alert_input(
        spec_mode="research",
        purity_status_a="DISPUTED",
    )
    results = evaluate_gates(inp, _default_config())

    spec_gate = [g for g in results if g.gate_name == "SPEC_OK"][0]
    assert spec_gate.passed


def test_duplicate_suppression():
    """Duplicate of an open alert is blocked."""
    inp = _make_alert_input(is_duplicate=True)
    results = evaluate_gates(inp, _default_config())

    assert determine_status(results) == "QUIET"
    reasons = collect_reason_codes(results)
    assert "DUPLICATE_ALERT" in reasons


def test_evidence_record_built_correctly():
    """Evidence record captures all gates, status, and reason codes."""
    inp = _make_alert_input(zscore=1.5)
    results = evaluate_gates(inp, _default_config())

    record = build_evidence_record(
        pair_name="GOLDTEN_GOLDM",
        trade_date=date(2026, 10, 1),
        gate_results=results,
        expected_convergence_inr=500.0,
        slippage_estimate=50.0,
        safety_buffer_inr=20.0,
    )

    assert record.status == "QUIET"
    assert "Z_BELOW_THRESHOLD" in record.reason_codes
    assert len(record.gate_results) == 12


def test_nearest_miss_ranking():
    """Near-miss ranking: most gates passed first, then highest min_ratio."""
    inp_close = _make_alert_input(zscore=1.9, pair_name="PAIR_CLOSE")  # z nearly at 2.0
    inp_far = _make_alert_input(zscore=0.5, volume_a=3, pair_name="PAIR_FAR")  # multiple fails

    cfg = _default_config()
    results_close = evaluate_gates(inp_close, cfg)
    results_far = evaluate_gates(inp_far, cfg)

    nm_close = compute_near_miss(results_close, inp_close, cfg)
    nm_far = compute_near_miss(results_far, inp_far, cfg)

    ranked = rank_near_misses([nm_far, nm_close])

    # PAIR_CLOSE should rank higher (more gates passed)
    assert ranked[0].pair_name == "PAIR_CLOSE"
    assert ranked[0].gates_passed > ranked[1].gates_passed
