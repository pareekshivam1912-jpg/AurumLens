"""Corwin-Schultz (2012) bid-ask spread estimator with fallback.

Implements Design §6.10. Uses daily highs/lows to estimate effective spread.

Formulas:
    β = [ln(H_t/L_t)]² + [ln(H_{t-1}/L_{t-1})]²
    γ = [ln(max(H_t, H_{t-1}) / min(L_t, L_{t-1}))]²
    α = (√(2β) − √β) / (3 − 2√2) − √(γ / (3 − 2√2))
    S = 2(e^α − 1) / (1 + e^α)

Fixture: H = (120,900; 121,200), L = (119,800; 120,300) gives S ≈ 0.000424.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

# Constant: 3 - 2√2 ≈ 0.17157
K: float = 3.0 - 2.0 * math.sqrt(2.0)


@dataclass(frozen=True)
class SlippageEstimate:
    """Estimated bid-ask spread and slippage model used."""
    spread_estimate: float   # S as a fraction (not bps)
    slippage_model: str      # 'corwin_schultz' or 'fixed_bps'
    is_fallback: bool


def corwin_schultz_single(
    h_t: float, l_t: float, h_prev: float, l_prev: float
) -> float:
    """Compute single 2-day Corwin-Schultz spread estimate.

    Parameters
    ----------
    h_t, l_t : float
        High and low on day t.
    h_prev, l_prev : float
        High and low on day t-1.

    Returns
    -------
    float
        Estimated spread S. May be negative (indicates no reliable spread).
    """
    if h_t <= 0 or l_t <= 0 or h_prev <= 0 or l_prev <= 0:
        raise ValueError("All high/low prices must be strictly positive")
    if h_t < l_t or h_prev < l_prev:
        raise ValueError("High must be >= Low for each day")

    # β = [ln(H_t/L_t)]² + [ln(H_{t-1}/L_{t-1})]²
    ln_hl_t = math.log(h_t / l_t)
    ln_hl_prev = math.log(h_prev / l_prev)
    beta = ln_hl_t ** 2 + ln_hl_prev ** 2

    # γ = [ln(max(H_t, H_{t-1}) / min(L_t, L_{t-1}))]²
    gamma = math.log(max(h_t, h_prev) / min(l_t, l_prev)) ** 2

    # α = (√(2β) − √β) / (3 − 2√2) − √(γ / (3 − 2√2))
    sqrt_2beta = math.sqrt(2.0 * beta)
    sqrt_beta = math.sqrt(beta)
    gamma_term = gamma / K
    # Guard against negative under square root
    alpha = (sqrt_2beta - sqrt_beta) / K - math.sqrt(max(0.0, gamma_term))

    # S = 2(e^α − 1) / (1 + e^α)
    exp_alpha = math.exp(alpha)
    s = 2.0 * (exp_alpha - 1.0) / (1.0 + exp_alpha)

    return s


def corwin_schultz_rolling(
    highs: Sequence[float],
    lows: Sequence[float],
    window: int = 5,
) -> Optional[float]:
    """Rolling average CS spread over the last `window` 2-day pairs.

    Uses data through t-1 only (the last element is t-1).
    Needs at least window+1 observations to form `window` 2-day pairs.

    Returns
    -------
    Optional[float]
        Average spread, or None if insufficient data.
    """
    if len(highs) < 2 or len(lows) < 2:
        return None
    if len(highs) != len(lows):
        raise ValueError("highs and lows must have the same length")

    n = len(highs)
    # Compute 2-day estimates for the last `window` pairs
    start = max(1, n - window)
    estimates: list[float] = []

    for i in range(start, n):
        try:
            s = corwin_schultz_single(highs[i], lows[i], highs[i - 1], lows[i - 1])
            estimates.append(s)
        except (ValueError, ArithmeticError):
            continue

    if not estimates:
        return None

    return sum(estimates) / len(estimates)


def estimate_slippage(
    highs: Sequence[float],
    lows: Sequence[float],
    symbol: str,
    fallback_bps: dict[str, float],
    cs_window: int = 5,
    slippage_model: str = "corwin_schultz",
) -> SlippageEstimate:
    """Estimate bid-ask spread using CS model with fallback.

    Parameters
    ----------
    highs, lows : Sequence[float]
        High and low prices through t-1.
    symbol : str
        Contract symbol for fallback lookup.
    fallback_bps : dict[str, float]
        Fallback spread in basis points per symbol.
    cs_window : int
        Rolling window for CS averaging.
    slippage_model : str
        'corwin_schultz' or 'fixed_bps'.

    Returns
    -------
    SlippageEstimate
    """
    if slippage_model == "fixed_bps":
        bps = fallback_bps.get(symbol, 10.0)
        return SlippageEstimate(
            spread_estimate=bps / 10000.0,
            slippage_model="fixed_bps",
            is_fallback=True,
        )

    # Try Corwin-Schultz
    cs_spread = corwin_schultz_rolling(highs, lows, window=cs_window)

    if cs_spread is not None and cs_spread > 0:
        return SlippageEstimate(
            spread_estimate=cs_spread,
            slippage_model="corwin_schultz",
            is_fallback=False,
        )

    # Fallback
    bps = fallback_bps.get(symbol, 10.0)
    return SlippageEstimate(
        spread_estimate=bps / 10000.0,
        slippage_model="corwin_schultz",
        is_fallback=True,
    )


def simulated_fill(price: float, spread: float, side: str) -> float:
    """Compute adverse simulated fill price.

    Buy fills at price × (1 + S/2), sell fills at price × (1 − S/2).

    Parameters
    ----------
    price : float
        Mid-market price.
    spread : float
        Estimated bid-ask spread as a fraction.
    side : str
        'buy' or 'sell'.

    Returns
    -------
    float
        Simulated fill price, adverse to the trade.
    """
    if side == "buy":
        return price * (1.0 + spread / 2.0)
    elif side == "sell":
        return price * (1.0 - spread / 2.0)
    else:
        raise ValueError(f"side must be 'buy' or 'sell', got '{side}'")
