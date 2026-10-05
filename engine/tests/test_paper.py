"""Tests for Paper Execution Simulator adapter and duplicate guard."""

import pytest
from aurumlens.paper.simulator import (
    DuplicateExecutionError,
    PaperExecutionAdapter,
    PositionStatus,
)


@pytest.fixture
def alert_evidence():
    return {
        "signal_id": "sig_20261001_01",
        "pair_name": "GOLDTEN_GOLDGUINEA",
        "leg_a_symbol": "GOLDTEN",
        "leg_b_symbol": "GOLDGUINEA",
        "rich_leg": "A",
        "quoted_price_a": 120500.0,
        "quoted_price_b": 96400.0,
        "lots_a": 4,
        "lots_b": 5,
        "residual_fine_g": 0.0,
        "slippage_bps_a": 6.0,
        "slippage_bps_b": 8.0,
    }


def test_stage_paper_order(alert_evidence):
    adapter = PaperExecutionAdapter()
    pos = adapter.stage_order(alert_evidence)

    assert pos.status == PositionStatus.OPEN
    assert pos.signal_id == "sig_20261001_01"
    assert pos.leg_a.side == "SELL"  # Rich leg is shorted
    assert pos.leg_b.side == "BUY"   # Cheap leg is longed
    # Fill price includes adverse slippage
    assert pos.leg_a.fill_price < alert_evidence["quoted_price_a"]  # Sell fills lower
    assert pos.leg_b.fill_price > alert_evidence["quoted_price_b"]  # Buy fills higher
    assert len(adapter.audit_log) == 1


def test_duplicate_execution_protection(alert_evidence):
    adapter = PaperExecutionAdapter()
    adapter.stage_order(alert_evidence)

    # Attempting to stage the exact same signal must raise DuplicateExecutionError
    with pytest.raises(DuplicateExecutionError):
        adapter.stage_order(alert_evidence)

    # Audit log records the blocked attempt
    assert len(adapter.audit_log) == 2
    assert adapter.audit_log[1]["action"] == "DUPLICATE_BLOCKED"


def test_close_paper_position(alert_evidence):
    adapter = PaperExecutionAdapter()
    pos = adapter.stage_order(alert_evidence)

    # Close trade with favorable price moves: A drops, B rises
    closed_pos = adapter.close_position(
        position_id=pos.position_id,
        current_price_a=120400.0,  # A fell from ~120,463 -> profit on short
        current_price_b=96450.0,   # B rose from ~96,438 -> profit on long
        exit_reason="REVERSION",
        costs_inr=150.0,
    )

    assert closed_pos.status == PositionStatus.CLOSED
    assert closed_pos.exit_reason == "REVERSION"
    assert closed_pos.gross_pnl > 0
    assert closed_pos.net_pnl == pytest.approx(closed_pos.gross_pnl - 150.0)
    assert adapter.available_capital == pytest.approx(adapter.initial_capital + closed_pos.net_pnl)
