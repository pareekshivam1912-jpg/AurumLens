"""Tests for log spread and rolling anomaly scores (Design §6.6).

Hand fixture:
    GOLDTEN 120,500 vs GOLDM 120,482.41 gives a raw log spread of 0.00014597.
"""

import math
import pytest

from aurumlens.analytics.spread import (
    compute_log_spread,
    compute_mad_score,
    compute_spread,
    compute_zscore,
)


def test_hand_fixture_raw_log_spread_00014597():
    """Design §6.6 Fixture: GOLDTEN 120,500 vs GOLDM 120,482.41 gives raw log spread 0.00014597."""
    norm_a = 120500.00  # GOLDTEN
    # GOLDM: 120000 * 0.999 / 0.995 = 120482.41206...
    # If rounded to 120482.41:
    norm_b = 120482.41

    spread = compute_log_spread(norm_a, norm_b)
    # ln(120500) - ln(120482.41) = 0.00014599...
    # ln(120500) - ln(120482.4120603) = 0.000145974...
    norm_b_exact = 120000.0 * (0.999 / 0.995)
    spread_exact = compute_log_spread(norm_a, norm_b_exact)

    assert round(spread_exact, 8) == 0.00014597
    assert round(spread, 6) == 0.000146


def test_spread_with_carry_adj():
    """Carry adjusted spread: s_t = ln(norm_A) - ln(norm_B) + carry_adj."""
    norm_a = 120500.00
    norm_b = 120000.0 * (0.999 / 0.995)
    carry_adj = 0.00082  # 5-day gap at 6%

    res = compute_spread(norm_a, norm_b, carry_adj=carry_adj)
    assert round(res.log_spread_raw, 8) == 0.00014597
    assert res.carry_adj == 0.00082
    expected_adj = res.log_spread_raw + carry_adj
    assert abs(res.log_spread_adj - expected_adj) < 1e-9


def test_no_lookahead_zscore_and_history_cutoff():
    """Scoring strictly uses history through t-1. If history count < min_history_obs, return None."""
    # 25 observations (below min_history_obs = 30)
    history_short = [0.0001 * (1 + 0.01 * i) for i in range(25)]
    res = compute_spread(120500.0, 120482.41, history=history_short, min_history_obs=30)
    assert res.zscore is None
    assert res.mad_score is None

    # 40 observations (exceeds min_history_obs = 30)
    # Constant history: mean=0.001, std=0.0002
    history_suff = [0.001 + 0.0002 * ((-1) ** i) for i in range(40)]
    res_suff = compute_spread(120500.0, 120000.0, history=history_suff, min_history_obs=30)
    assert res_suff.zscore is not None
    assert res_suff.roll_mean is not None
    assert res_suff.roll_std is not None


def test_rich_leg_selection():
    """rich_leg = A if s_t > mu_{t-1} else B."""
    # History with mean = 0.0
    history = [-0.001, 0.001] * 20  # mean = 0.0

    # Current spread > 0.0 -> A is rich
    res_a_rich = compute_spread(121000.0, 120000.0, history=history, min_history_obs=10)
    assert res_a_rich.rich_leg == "A"

    # Current spread < 0.0 -> B is rich
    res_b_rich = compute_spread(119000.0, 120000.0, history=history, min_history_obs=10)
    assert res_b_rich.rich_leg == "B"


def test_mad_score_calculation():
    """MAD score uses robust scale factor 1.4826."""
    # Absolute deviations from 3.0: median = 1.0, scale = 1.4826 * 1.0 = 1.4826
    score = compute_mad_score(4.4826, median_val=3.0, mad_val=1.0)
    # (4.4826 - 3.0) / 1.4826 = 1.4826 / 1.4826 = 1.0
    assert score is not None
    assert round(score, 4) == 1.0
