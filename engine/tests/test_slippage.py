"""Tests for Corwin-Schultz (2012) slippage estimator (Design §6.10).

Mandatory coverage:
- CS fixture: H=(120,900; 121,200), L=(119,800; 120,300) -> S ≈ 0.000424
- Fallback when S ≤ 0 or missing data
- Simulated fill: adverse direction
"""

import math
import pytest

from aurumlens.signal.slippage import (
    corwin_schultz_single,
    corwin_schultz_rolling,
    estimate_slippage,
    simulated_fill,
)


def test_corwin_schultz_hand_fixture():
    """Design §6.10 Fixture: H=(120,900; 121,200), L=(119,800; 120,300) -> S ≈ 0.000424."""
    s = corwin_schultz_single(
        h_t=121200.0,
        l_t=120300.0,
        h_prev=120900.0,
        l_prev=119800.0,
    )
    # S should be approximately 0.000424 (within tolerance)
    assert abs(s - 0.000424) < 0.001, f"Expected ~0.000424, got {s}"
    assert s > 0, "CS spread must be positive for this fixture"


def test_corwin_schultz_fallback_on_negative():
    """When CS data produces S ≤ 0 or is insufficient, fallback is used."""
    # Only 1 data point — insufficient for 2-day pairing
    result = estimate_slippage(
        highs=[100.0],
        lows=[100.0],
        symbol="GOLDM",
        fallback_bps={"GOLDM": 5.0},
    )
    assert result.is_fallback
    assert result.spread_estimate == 5.0 / 10000.0


def test_corwin_schultz_fallback_on_missing_data():
    """When insufficient data, fallback is used."""
    result = estimate_slippage(
        highs=[120500.0],  # Only 1 point, need at least 2
        lows=[119800.0],
        symbol="GOLDTEN",
        fallback_bps={"GOLDTEN": 8.0},
    )
    assert result.is_fallback
    assert result.spread_estimate == 8.0 / 10000.0


def test_fixed_bps_model():
    """When slippage_model='fixed_bps', always use fallback."""
    result = estimate_slippage(
        highs=[121000, 121200, 121100],
        lows=[119800, 120300, 120100],
        symbol="GOLDM",
        fallback_bps={"GOLDM": 5.0},
        slippage_model="fixed_bps",
    )
    assert result.is_fallback
    assert result.slippage_model == "fixed_bps"
    assert result.spread_estimate == 5.0 / 10000.0


def test_simulated_fill_adverse_direction():
    """Buy fills at higher price, sell fills at lower price (adverse)."""
    price = 120000.0
    spread = 0.001  # 10 bps

    buy_fill = simulated_fill(price, spread, "buy")
    sell_fill = simulated_fill(price, spread, "sell")

    # Buy: 120000 * (1 + 0.0005) = 120060
    assert buy_fill == 120000.0 * 1.0005
    assert buy_fill > price

    # Sell: 120000 * (1 - 0.0005) = 119940
    assert sell_fill == 120000.0 * 0.9995
    assert sell_fill < price
