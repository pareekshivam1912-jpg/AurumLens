"""Carry calculation and implied term-structure adjustment module.

Implements carry calculation per Design §6.5 (R18):
- Curve carry: If symbol S has two OK-quality expiries on date t with sufficient volume:
    r_curve = ln(P_far / P_near) / ((T_far - T_near) / 365)
- Fallback: r = carry_fallback_rate from config (e.g. 0.065 / 6.5%).
    Mark carry_source = 'FALLBACK'.
- Adjustment: carry_adj = r * (T_B - T_A) / 365.

Scale check:
    At r = 6% (0.06), a 5-day gap gives 0.06 * 5 / 365 = 0.00082 (8.2 bp).
    At r = 6% (0.06), a 26-day gap gives 0.06 * 26 / 365 = 0.00427 (42.7 bp).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import math
from typing import Optional, Union

DAYS_IN_YEAR: float = 365.0
SOURCE_CURVE: str = "CURVE"
SOURCE_FALLBACK: str = "FALLBACK"
DEFAULT_FALLBACK_RATE: float = 0.065


@dataclass(frozen=True)
class CarryResult:
    """Carry calculation result.

    Attributes:
        carry_rate: Annualized continuous carry rate r (e.g. 0.065 for 6.5%).
        carry_adj: Carry adjustment carry_adj = r * (T_B - T_A) / 365.
        carry_source: Source of the carry rate ('CURVE' or 'FALLBACK').
    """

    carry_rate: float
    carry_adj: float
    carry_source: str


def _to_date(d: Union[date, str, datetime]) -> date:
    """Coerce string or datetime into a date object."""
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, str):
        return date.fromisoformat(d)
    return d


def compute_curve_carry_rate(
    p_near: float,
    p_far: float,
    expiry_near: Union[date, str, datetime],
    expiry_far: Union[date, str, datetime],
) -> float:
    """Compute annualized implied carry rate from same-symbol term structure.

    Per Design §6.5 (R18):
        r_curve = ln(P_far / P_near) / ((T_far - T_near) / 365)

    Args:
        p_near: Price of the near-dated contract (must be > 0).
        p_far: Price of the far-dated contract (must be > 0).
        expiry_near: Expiry date of the near contract.
        expiry_far: Expiry date of the far contract (must be strictly after expiry_near).

    Returns:
        Annualized continuous carry rate r_curve.

    Raises:
        ValueError: If prices <= 0 or expiry_far <= expiry_near.
    """
    if p_near <= 0.0 or p_far <= 0.0:
        raise ValueError(
            f"Prices must be strictly positive, got p_near={p_near}, p_far={p_far}"
        )

    d_near = _to_date(expiry_near)
    d_far = _to_date(expiry_far)
    day_diff = (d_far - d_near).days

    if day_diff <= 0:
        raise ValueError(
            f"expiry_far ({d_far}) must be strictly after expiry_near ({d_near}), "
            f"got non-positive day difference: {day_diff}"
        )

    tau = day_diff / DAYS_IN_YEAR
    return math.log(p_far / p_near) / tau


def compute_carry_adjustment(
    carry_rate: float,
    expiry_a: Union[date, str, datetime],
    expiry_b: Union[date, str, datetime],
) -> float:
    """Compute carry adjustment for cross-contract spread.

    Per Design §6.5:
        carry_adj = r * (T_B - T_A) / 365

    Scale check:
        At r = 0.06, a 5-day gap gives:
            0.06 * 5 / 365 = 0.0008219... (~0.00082 or 8.2 bp).

    Args:
        carry_rate: Annualized carry rate r.
        expiry_a: Expiry date of leg A.
        expiry_b: Expiry date of leg B.

    Returns:
        Carry adjustment carry_adj.
    """
    d_a = _to_date(expiry_a)
    d_b = _to_date(expiry_b)
    day_diff = (d_b - d_a).days
    return carry_rate * (day_diff / DAYS_IN_YEAR)


# Alias
compute_carry_adj = compute_carry_adjustment


def compute_carry_adj_from_days(
    carry_rate: float,
    days_b_minus_a: int,
) -> float:
    """Compute carry adjustment directly from calendar day difference (T_B - T_A)."""
    return carry_rate * (days_b_minus_a / DAYS_IN_YEAR)


def compute_carry(
    expiry_a: Union[date, str, datetime],
    expiry_b: Union[date, str, datetime],
    curve_rate: Optional[float] = None,
    fallback_rate: float = DEFAULT_FALLBACK_RATE,
) -> CarryResult:
    """Calculate CarryResult using curve carry if available, else fallback rate.

    Per Design §6.5 (R18):
    1. If curve_rate is available and finite, use it and mark carry_source = 'CURVE'.
    2. Otherwise, use fallback_rate from config and mark carry_source = 'FALLBACK'.
    3. Calculate carry_adj = r * (T_B - T_A) / 365.

    Args:
        expiry_a: Expiry date of leg A.
        expiry_b: Expiry date of leg B.
        curve_rate: Implied curve carry rate if available.
        fallback_rate: Configured fallback carry rate (default: 0.065).

    Returns:
        CarryResult with carry_rate, carry_adj, and carry_source ('CURVE' or 'FALLBACK').
    """
    if curve_rate is not None and not math.isnan(curve_rate) and not math.isinf(curve_rate):
        rate = float(curve_rate)
        source = SOURCE_CURVE
    else:
        rate = float(fallback_rate)
        source = SOURCE_FALLBACK

    adj = compute_carry_adjustment(rate, expiry_a, expiry_b)
    return CarryResult(
        carry_rate=rate,
        carry_adj=adj,
        carry_source=source,
    )
