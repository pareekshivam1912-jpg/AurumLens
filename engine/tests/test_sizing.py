"""Tests for lot-ratio sizing and residual fine gold grams (R22, Design §6.7).

Hand fixture:
    GOLDTEN (10 g, 999) vs GOLDGUINEA (8 g, 999) gives a ratio of 4 : 5
    (40 g vs 40 g, residual 0).
"""

import pytest

from aurumlens.analytics.sizing import (
    calculate_lot_ratio,
    fine_grams_per_lot,
)


def test_hand_fixture_goldten_vs_goldguinea_4_to_5():
    """Design §6.7 Fixture: GOLDTEN (10g, 999) vs GOLDGUINEA (8g, 999) -> 4 : 5 ratio, residual 0."""
    g_goldten = fine_grams_per_lot(trading_unit_g=10.0, purity=0.999)
    g_goldguinea = fine_grams_per_lot(trading_unit_g=8.0, purity=0.999)

    assert g_goldten == 10.0
    assert g_goldguinea == 8.0

    res = calculate_lot_ratio(
        g_a=g_goldten,
        g_b=g_goldguinea,
        max_lots_per_leg=50,
        max_notional_inr=2_500_000.0,
    )

    # Ratio: 4 lots of 10g = 40g, 5 lots of 8g = 40g
    assert res.lots_a == 4
    assert res.lots_b == 5
    assert res.residual_fine_g == 0.0
    assert res.fine_grams_a == 40.0
    assert res.fine_grams_b == 40.0

    # Test tuple unpacking
    lots_a, lots_b, residual = res
    assert (lots_a, lots_b, residual) == (4, 5, 0.0)


def test_fine_grams_with_sub999_purity():
    """Fine grams formula: g_i = trading_unit_g * purity / 0.999."""
    # GOLDM: 100g at 0.995 purity
    # g = 100 * 0.995 / 0.999 = 99.599599599...
    g_goldm = fine_grams_per_lot(trading_unit_g=100.0, purity=0.995)
    expected = 100.0 * (0.995 / 0.999)
    assert abs(g_goldm - expected) < 1e-9


def test_residual_fine_grams_sign():
    """residual_fine_g = n_A * g_A - n_B * g_B.

    Positive sign indicates leg A has more gold (net long A / short B is long gold).
    Negative sign indicates leg B has more gold.
    """
    # 10g vs 3g with max_lots=3
    # Best integer match: 1 lot of 10g vs 3 lots of 3g (9g) -> residual = +1.0g
    res_pos = calculate_lot_ratio(g_a=10.0, g_b=3.0, max_lots_per_leg=3)
    assert res_pos.lots_a == 1
    assert res_pos.lots_b == 3
    assert res_pos.residual_fine_g == 1.0  # Leg A is longer

    # Opposite: 3g vs 10g -> residual = -1.0g
    res_neg = calculate_lot_ratio(g_a=3.0, g_b=10.0, max_lots_per_leg=3)
    assert res_neg.lots_a == 3
    assert res_neg.lots_b == 1
    assert res_neg.residual_fine_g == -1.0  # Leg B is longer


def test_notional_cap_enforced():
    """Lots cannot exceed max_notional_inr."""
    # Price per gram = 7,500 INR
    # Leg A: 100g lot = 750,000 INR
    # Max notional = 1,000,000 INR -> at most 1 lot of A
    res = calculate_lot_ratio(
        g_a=100.0,
        g_b=10.0,
        price_a=75000.0,  # 75,000 per 10g = 750,000 per 100g lot
        price_b=75000.0,  # 75,000 per 10g lot
        quote_basis_a=10.0,
        quote_basis_b=10.0,
        max_notional_inr=1_000_000.0,
        max_lots_per_leg=50,
    )
    assert res.lots_a <= 1
    if res.notional_a is not None and res.notional_b is not None:
        assert res.notional_a <= 1_000_000.0
        assert res.notional_b <= 1_000_000.0
