"""Tests for implied carry rate and carry adjustment (R18, Design §6.5).

Scale check from Design §6.5:
- At r = 6% (0.06), a 5-day gap gives 0.00082 (8.2 bp).
- At r = 6% (0.06), a 26-day gap gives 0.00427 (42.7 bp).
"""

from datetime import date
import math
import pytest

from aurumlens.analytics.carry import (
    SOURCE_CURVE,
    SOURCE_FALLBACK,
    compute_carry,
    compute_carry_adjustment,
    compute_curve_carry_rate,
)


def test_scale_check_5_day_gap():
    """Design §6.5 Scale Check: r=6%, 5-day gap gives 0.00082 (8.2 bp)."""
    # carry_adj = r * (T_B - T_A) / 365
    adj = compute_carry_adjustment(
        carry_rate=0.06,
        expiry_a=date(2026, 10, 31),
        expiry_b=date(2026, 11, 5),  # 5 calendar days
    )
    # 0.06 * 5 / 365 = 0.0008219178...
    assert round(adj, 5) == 0.00082


def test_scale_check_26_day_gap():
    """Design §6.5 Scale Check: r=6%, 26-day gap gives 0.00427 (42.7 bp)."""
    adj = compute_carry_adjustment(
        carry_rate=0.06,
        expiry_a=date(2026, 10, 5),
        expiry_b=date(2026, 10, 31),  # 26 calendar days
    )
    # 0.06 * 26 / 365 = 0.00427397...
    assert round(adj, 5) == 0.00427


def test_curve_carry_rate_formula():
    """Test curve carry rate computation: r = ln(P_far / P_near) / (tau)."""
    # Near price = 75,000, Far price = 75,375 (0.5% premium over 30 days)
    # tau = 30 / 365 = 0.0821918
    # r = ln(75375 / 75000) / 0.0821918 = 0.0049875 / 0.0821918 = 0.06068 (6.07%)
    r_curve = compute_curve_carry_rate(
        p_near=75000.0,
        p_far=75375.0,
        expiry_near=date(2026, 10, 1),
        expiry_far=date(2026, 10, 31),
    )
    expected = math.log(75375.0 / 75000.0) / (30.0 / 365.0)
    assert abs(r_curve - expected) < 1e-9
    assert round(r_curve, 4) == 0.0607


def test_compute_carry_curve_vs_fallback():
    """Verify carry source is tagged CURVE when curve rate is provided, FALLBACK otherwise."""
    # When curve is provided
    res_curve = compute_carry(
        expiry_a=date(2026, 10, 31),
        expiry_b=date(2026, 11, 5),
        curve_rate=0.06,
        fallback_rate=0.065,
    )
    assert res_curve.carry_source == SOURCE_CURVE
    assert res_curve.carry_rate == 0.06
    assert round(res_curve.carry_adj, 5) == 0.00082

    # When curve is None -> fallback
    res_fallback = compute_carry(
        expiry_a=date(2026, 10, 31),
        expiry_b=date(2026, 11, 5),
        curve_rate=None,
        fallback_rate=0.065,
    )
    assert res_fallback.carry_source == SOURCE_FALLBACK
    assert res_fallback.carry_rate == 0.065
    expected_fallback_adj = 0.065 * 5 / 365
    assert abs(res_fallback.carry_adj - expected_fallback_adj) < 1e-9


def test_carry_adjustment_direction():
    """If leg B expires AFTER leg A, carry_adj > 0. If leg B expires BEFORE leg A, carry_adj < 0."""
    adj_pos = compute_carry_adjustment(0.06, date(2026, 10, 1), date(2026, 10, 10))
    assert adj_pos > 0.0

    adj_neg = compute_carry_adjustment(0.06, date(2026, 10, 10), date(2026, 10, 1))
    assert adj_neg < 0.0
