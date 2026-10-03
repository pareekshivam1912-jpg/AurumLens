"""Tests for itemized cost model (Design §6.9).

Mandatory coverage:
- CTT applies SELL-only
- Stamp duty applies BUY-only
- GST base = brokerage + exchange + sebi (NOT CTT/stamp)
"""

import pytest

from aurumlens.signal.costs import (
    CostBreakdown,
    compute_leg_side_costs,
    compute_pair_costs,
)


def test_ctt_sell_only():
    """CTT must appear only on sell side, never on buy side."""
    buy_lines = compute_leg_side_costs(turnover_inr=100_000, side="buy", leg="A")
    sell_lines = compute_leg_side_costs(turnover_inr=100_000, side="sell", leg="A")

    buy_components = {l.component for l in buy_lines}
    sell_components = {l.component for l in sell_lines}

    assert "ctt" not in buy_components
    assert "ctt" in sell_components


def test_stamp_buy_only():
    """Stamp duty must appear only on buy side, never on sell side."""
    buy_lines = compute_leg_side_costs(turnover_inr=100_000, side="buy", leg="A")
    sell_lines = compute_leg_side_costs(turnover_inr=100_000, side="sell", leg="A")

    buy_components = {l.component for l in buy_lines}
    sell_components = {l.component for l in sell_lines}

    assert "stamp" in buy_components
    assert "stamp" not in sell_components


def test_gst_base_excludes_ctt_and_stamp():
    """GST is computed on (brokerage + exchange + sebi), NOT on CTT or stamp duty.

    Sell side: has CTT but no stamp. GST should NOT include CTT in its base.
    """
    lines = compute_leg_side_costs(turnover_inr=1_000_000, side="sell", leg="A")
    by_comp = {l.component: l.amount_inr for l in lines}

    # GST base = brokerage + exchange + sebi
    expected_gst_base = by_comp["brokerage"] + by_comp["exchange"] + by_comp["sebi"]
    expected_gst = 0.18 * expected_gst_base
    assert abs(by_comp["gst"] - round(expected_gst, 4)) < 0.01


def test_pair_costs_total_covers_all_sides():
    """Pair costs = 2 legs × 2 sides = 4 leg-side groups."""
    breakdown = compute_pair_costs(
        turnover_a=120_000, turnover_b=96_000, pair_fine_grams=40.0
    )

    # Should have lines for A-buy, A-sell, B-buy, B-sell
    leg_sides = {(l.leg, l.side) for l in breakdown.lines}
    assert ("A", "buy") in leg_sides
    assert ("A", "sell") in leg_sides
    assert ("B", "buy") in leg_sides
    assert ("B", "sell") in leg_sides

    assert breakdown.total_inr > 0
    assert breakdown.cost_per_10g > 0


def test_brokerage_flat_dominates_small_turnover():
    """For small turnover, flat brokerage (Rs 20) beats percentage (0.03% × V)."""
    # 0.03% of 50,000 = 15, which is less than flat 20
    # So min(20, 15) = 15
    lines = compute_leg_side_costs(turnover_inr=50_000, side="buy", leg="A")
    brokerage = [l for l in lines if l.component == "brokerage"][0]
    assert brokerage.amount_inr == 15.0

    # For very small turnover (10,000): 0.03% = 3, min(20, 3) = 3
    lines_small = compute_leg_side_costs(turnover_inr=10_000, side="buy", leg="A")
    brokerage_small = [l for l in lines_small if l.component == "brokerage"][0]
    assert brokerage_small.amount_inr == 3.0
