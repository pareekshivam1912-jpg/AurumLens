"""Spread and statistical score calculation module.

Implements spread and anomaly scoring per Design §6.6:
- s_t = ln(norm_A) - ln(norm_B) + carry_adj
- Fixture: GOLDTEN 120,500 vs GOLDM 120,482.41 -> raw log spread = 0.00014597
- z_t = (s_t - mu_{t-1}) / sigma_{t-1} over s_{t-L}...s_{t-1}. Require count >= min_history_obs
- MAD variant: (s_t - median) / (1.4826 * MAD)
- rich_leg = A if s_t > mu_{t-1} else B

Strict No Look-Ahead:
    All rolling statistics (mean, std, median, MAD) use history strictly
    through trade date t-1. The observation at date t is never included in
    its own baseline.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
from typing import Optional, Sequence

MAD_NORMAL_SCALE: float = 1.4826
DEFAULT_LOOKBACK_WINDOW: int = 60
DEFAULT_MIN_HISTORY_OBS: int = 30


@dataclass(frozen=True)
class SpreadResult:
    """Spread calculation and statistical anomaly score results.

    Attributes:
        log_spread_raw: Raw log price difference ln(norm_A) - ln(norm_B).
        carry_adj: Implied carry adjustment term.
        log_spread_adj: Carry-adjusted spread s_t = log_spread_raw + carry_adj.
        zscore: Rolling z-score through t-1, or None if insufficient history.
        mad_score: Robust MAD score through t-1, or None if insufficient history.
        rich_leg: Identifier of the richer/overvalued contract leg ('A' or 'B').
        roll_mean: Rolling mean mu_{t-1} of adjusted spread through t-1.
        roll_std: Rolling standard deviation sigma_{t-1} through t-1.
    """

    log_spread_raw: float
    carry_adj: float
    log_spread_adj: float
    zscore: Optional[float] = None
    mad_score: Optional[float] = None
    rich_leg: Optional[str] = None
    roll_mean: Optional[float] = None
    roll_std: Optional[float] = None


def compute_log_spread(norm_a: float, norm_b: float) -> float:
    """Compute raw log spread between normalized prices of leg A and leg B.

    Per Design §6.6:
        log_spread_raw = ln(norm_A) - ln(norm_B)

    Note:
        Both inputs must be normalized prices (in Rs per 10 g of 999 fine gold).
        Never compare raw unnormalized contract prices!

    Fixture:
        GOLDTEN 120,500.00 vs GOLDM 120,482.41 (from 120,000 * 0.999/0.995 = 120,482.41206...)
        yields raw log spread = 0.00014597.

    Args:
        norm_a: Normalized price of leg A (must be > 0).
        norm_b: Normalized price of leg B (must be > 0).

    Returns:
        Raw log spread as float.

    Raises:
        ValueError: If norm_a <= 0 or norm_b <= 0.
    """
    if norm_a <= 0.0 or norm_b <= 0.0:
        raise ValueError(
            f"Normalized prices must be strictly positive, got norm_a={norm_a}, norm_b={norm_b}"
        )
    return math.log(norm_a) - math.log(norm_b)


def compute_zscore(
    spread: float,
    mean: float,
    std: float,
) -> Optional[float]:
    """Compute rolling z-score: z_t = (s_t - mu_{t-1}) / sigma_{t-1}.

    Args:
        spread: Current adjusted spread s_t.
        mean: Historical rolling mean mu_{t-1} through t-1.
        std: Historical rolling standard deviation sigma_{t-1} through t-1.

    Returns:
        z-score as float, or None if std is non-positive or non-finite.
    """
    if std is None or std <= 0.0 or math.isnan(std) or math.isinf(std):
        return None
    if mean is None or math.isnan(mean) or math.isinf(mean):
        return None
    return (spread - mean) / std


def compute_mad(values: Sequence[float]) -> float:
    """Compute Median Absolute Deviation (MAD) of a sequence.

    Formula:
        MAD = median(|X - median(X)|)

    Args:
        values: Sequence of numeric values (must be non-empty).

    Returns:
        Median absolute deviation as float.

    Raises:
        ValueError: If values sequence is empty.
    """
    if not values:
        raise ValueError("Cannot compute MAD of an empty sequence")
    med = statistics.median(values)
    abs_devs = [abs(x - med) for x in values]
    return float(statistics.median(abs_devs))


def compute_mad_score(
    spread: float,
    median_val: float,
    mad_val: float,
    scale_factor: float = MAD_NORMAL_SCALE,
) -> Optional[float]:
    """Compute robust anomaly score using Median Absolute Deviation.

    Formula per Design §6.6:
        mad_score = (s_t - median) / (1.4826 * MAD)

    The 1.4826 factor scales the MAD of a normally distributed sample to
    match the standard deviation: 1 / Phi^{-1}(3/4) ~ 1.4826022...

    Args:
        spread: Current adjusted spread s_t.
        median_val: Historical rolling median through t-1.
        mad_val: Historical median absolute deviation through t-1.
        scale_factor: Normal consistency scaling constant (default: 1.4826).

    Returns:
        MAD score as float, or None if denominator is non-positive or non-finite.
    """
    if mad_val is None or mad_val <= 0.0 or math.isnan(mad_val) or math.isinf(mad_val):
        return None
    if median_val is None or math.isnan(median_val) or math.isinf(median_val):
        return None
    denom = scale_factor * mad_val
    if denom <= 0.0:
        return None
    return (spread - median_val) / denom


def compute_spread(
    norm_a: float,
    norm_b: float,
    carry_adj: float = 0.0,
    history: Optional[Sequence[float]] = None,
    lookback_window: int = DEFAULT_LOOKBACK_WINDOW,
    min_history_obs: int = DEFAULT_MIN_HISTORY_OBS,
    symbol_a: str = "A",
    symbol_b: str = "B",
    ddof: int = 1,
) -> SpreadResult:
    """Compute cross-contract log spread and rolling anomaly scores.

    Per Design §6.6:
    - s_t = ln(norm_A) - ln(norm_B) + carry_adj
    - z_t = (s_t - mu_{t-1}) / sigma_{t-1}
    - mad_score = (s_t - median) / (1.4826 * MAD)
    - rich_leg = A if s_t > mu_{t-1} else B

    Strict No Look-Ahead:
        The `history` sequence must contain observations strictly prior to t
        (s_{t-L} ... s_{t-1}). The observation at date t is not included.

    Args:
        norm_a: Normalized price of leg A in Rs/10g 999 (must be > 0).
        norm_b: Normalized price of leg B in Rs/10g 999 (must be > 0).
        carry_adj: Implied carry adjustment (default: 0.0).
        history: Sequence of historical adjusted spreads through t-1.
        lookback_window: Window size L for rolling statistics (default: 60).
        min_history_obs: Minimum observations required to compute scores (default: 30).
        symbol_a: Identifier for leg A (default: 'A').
        symbol_b: Identifier for leg B (default: 'B').
        ddof: Degrees of freedom for sample standard deviation (default: 1).

    Returns:
        SpreadResult dataclass.
    """
    log_spread_raw = compute_log_spread(norm_a, norm_b)
    log_spread_adj = log_spread_raw + carry_adj

    roll_mean: Optional[float] = None
    roll_std: Optional[float] = None
    zscore: Optional[float] = None
    mad_score: Optional[float] = None
    rich_leg: Optional[str] = None

    if history is not None:
        clean_hist = [
            float(x) for x in history
            if x is not None and not math.isnan(x) and not math.isinf(x)
        ]
        if lookback_window > 0:
            window = clean_hist[-lookback_window:]
        else:
            window = clean_hist

        if len(window) >= min_history_obs:
            roll_mean = float(statistics.fmean(window))
            if ddof == 0:
                roll_std = float(statistics.pstdev(window))
            else:
                roll_std = float(statistics.stdev(window))

            zscore = compute_zscore(log_spread_adj, roll_mean, roll_std)

            med = float(statistics.median(window))
            mad = compute_mad(window)
            mad_score = compute_mad_score(log_spread_adj, med, mad)

            rich_leg = symbol_a if log_spread_adj > roll_mean else symbol_b

    return SpreadResult(
        log_spread_raw=log_spread_raw,
        carry_adj=carry_adj,
        log_spread_adj=log_spread_adj,
        zscore=zscore,
        mad_score=mad_score,
        rich_leg=rich_leg,
        roll_mean=roll_mean,
        roll_std=roll_std,
    )


# Function alias
compute_spread_result = compute_spread
