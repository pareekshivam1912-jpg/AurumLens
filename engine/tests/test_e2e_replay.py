"""End-to-end replay test for AurumLens (Phase A10 / Phase 7 Exit Gate).

Exit Gate Specification (PRD §15, ANTIGRAVITY_BUILD_PLAN §11):
- A replayed historical alert flows through:
  signal -> explanation (EN/HI) -> paper position -> exit -> stored P&L -> exported evidence pack (CSV/HTML).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
import tempfile
import pytest

from aurumlens.explain.explainer import SignalExplainer
from aurumlens.explain.numeric_guard import verify_numeric_guard
from aurumlens.export.evidence import export_evidence_to_csv, export_evidence_to_html
from aurumlens.paper.simulator import (
    DuplicateExecutionError,
    PaperExecutionAdapter,
    PositionStatus,
)


def test_end_to_end_replayed_alert_lifecycle():
    """Verify complete end-to-end flow of an ALERT through the entire pipeline."""
    # 1. Replayed historical alert evidence record (day t = 2026-10-01)
    evidence = {
        "signal_id": "sig-replay-20261001-01",
        "pair_name": "GOLDTEN_GOLDGUINEA",
        "trade_date": "2026-10-01",
        "leg_a_contract_id": "GOLDTEN-20261031",
        "leg_b_contract_id": "GOLDGUINEA-20261031",
        "leg_a_expiry": "2026-10-31",
        "leg_b_expiry": "2026-10-31",
        "expiry_gap_days": 0,
        "quoted_price_a": 120500.0,
        "quoted_price_b": 96400.0,
        "price_source": "settlement",
        "quality_a": "OK",
        "quality_b": "OK",
        "normalized_price_a": 120500.0,
        "normalized_price_b": 120500.0,
        "target_basis_g": 10.0,
        "carry_rate": 0.065,
        "carry_source": "FALLBACK",
        "log_spread_raw": 0.000146,
        "log_spread_adj": 0.000146,
        "roll_mean": 0.000000,
        "roll_std": 0.000060,
        "zscore": 2.43,
        "rich_leg": "GOLDTEN",
        "expected_convergence_inr": 530.0,
        "total_costs_inr": 170.0,
        "slippage_inr": 50.0,
        "safety_buffer_inr": 0.0,
        "net_expected_edge_inr": 310.0,
        "volume_a": 120.0,
        "volume_b": 95.0,
        "oi_a": 450.0,
        "oi_b": 380.0,
        "lots_a": 4,
        "lots_b": 5,
        "pair_fine_grams": 40.0,
        "residual_fine_g": 0.0,
        "status": "ALERT",
        "reason_codes": [],
        "config_version": "v2.1.0",
        "dataset_version": "ds_20261001_v1",
        "gate_results": [
            {"gate_name": "SPEC_OK", "passed": True, "value": 1.0, "threshold": 1.0, "margin": 0.0, "reason_code": "OK"},
            {"gate_name": "DATA_QUALITY", "passed": True, "value": 1.0, "threshold": 1.0, "margin": 0.0, "reason_code": "OK"},
            {"gate_name": "EXPIRY_PAIR_VALID", "passed": True, "value": 0.0, "threshold": 35.0, "margin": 35.0, "reason_code": "OK"},
            {"gate_name": "HISTORY_SUFFICIENT", "passed": True, "value": 30.0, "threshold": 30.0, "margin": 0.0, "reason_code": "OK"},
            {"gate_name": "Z_SCORE_THRESHOLD", "passed": True, "value": 2.43, "threshold": 2.0, "margin": 0.43, "reason_code": "OK"},
            {"gate_name": "LIQUIDITY_VOLUME_A", "passed": True, "value": 120.0, "threshold": 10.0, "margin": 110.0, "reason_code": "OK"},
            {"gate_name": "LIQUIDITY_VOLUME_B", "passed": True, "value": 95.0, "threshold": 10.0, "margin": 85.0, "reason_code": "OK"},
            {"gate_name": "LIQUIDITY_OI_A", "passed": True, "value": 450.0, "threshold": 50.0, "margin": 400.0, "reason_code": "OK"},
            {"gate_name": "LIQUIDITY_OI_B", "passed": True, "value": 380.0, "threshold": 50.0, "margin": 330.0, "reason_code": "OK"},
            {"gate_name": "EXPIRY_SAFETY", "passed": True, "value": 30.0, "threshold": 5.0, "margin": 25.0, "reason_code": "OK"},
            {"gate_name": "COST_HURDLE", "passed": True, "value": 310.0, "threshold": 0.0, "margin": 310.0, "reason_code": "OK"},
            {"gate_name": "DUPLICATE_CHECK", "passed": True, "value": 0.0, "threshold": 0.0, "margin": 0.0, "reason_code": "OK"},
        ],
    }

    # 2. Generate and verify bilingual explanations
    explainer = SignalExplainer()

    # English explanation
    exp_en = explainer.explain(evidence, language="en")
    assert exp_en.status == "ALERT"
    assert exp_en.passed_numeric_guard is True
    assert "GOLDTEN" in exp_en.text
    assert verify_numeric_guard(exp_en.text, evidence) is True

    # Hindi explanation
    exp_hi = explainer.explain(evidence, language="hi")
    assert exp_hi.status == "ALERT"
    assert exp_hi.passed_numeric_guard is True
    assert "GOLDTEN" in exp_hi.text
    assert verify_numeric_guard(exp_hi.text, evidence) is True

    # 3. Paper Execution at t+1 (2026-10-02)
    adapter = PaperExecutionAdapter()
    evidence["rich_leg"] = "A"

    # Enter position
    position = adapter.stage_order(evidence)

    assert position.status == PositionStatus.OPEN
    assert position.position_id.startswith("pos_")
    assert position.leg_a.lots == 4
    assert position.leg_b.lots == 5

    # Zero-duplicate rule assertion: attempting to re-execute same signal_id MUST fail
    with pytest.raises(DuplicateExecutionError):
        adapter.stage_order(evidence)

    # 4. Exit position at t+5 on reversion
    closed = adapter.close_position(
        position_id=position.position_id,
        current_price_a=120200.0,  # GOLDTEN converged down
        current_price_b=96450.0,   # GOLDGUINEA held firm
        exit_reason="REVERSION",
        costs_inr=170.0,
    )

    assert closed.status == PositionStatus.CLOSED
    assert closed.exit_reason == "REVERSION"
    assert closed.net_pnl is not None
    assert closed.gross_pnl is not None
    assert closed.total_costs == 170.0

    # 5. Export Evidence Pack (CSV and HTML)
    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = Path(tmp_dir) / "evidence.csv"
        html_path = Path(tmp_dir) / "evidence.html"

        csv_str = export_evidence_to_csv(evidence)
        html_str = export_evidence_to_html(evidence)

        csv_path.write_text(csv_str, encoding="utf-8")
        html_path.write_text(html_str, encoding="utf-8")

        assert csv_path.exists()
        assert html_path.exists()

        csv_content = csv_path.read_text(encoding="utf-8")
        html_content = html_path.read_text(encoding="utf-8")

        # Verify critical integrity elements
        assert "sig-replay-20261001-01" in csv_content
        assert "GOLDTEN_GOLDGUINEA" in csv_content
        assert "v2.1.0" in csv_content

        assert "AurumLens Evidence Audit Pack" in html_content
        assert "GOLDTEN_GOLDGUINEA" in html_content
        assert "2.43" in html_content
        assert "Analytics only — not investment advice" in html_content
