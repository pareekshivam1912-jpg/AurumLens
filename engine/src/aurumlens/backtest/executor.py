"""Trade execution and P&L attribution for walk-forward backtesting.

Implements Design §6.15:
- Entry at t+1 using execution_price plus adverse slippage.
- Exit on: reversion (|z| < exit_z), time stop (max_holding_days), or unsafe expiry window.
- Attribution:
    residual_gold_pnl = residual_fine_g / 10 × ΔP_norm(ref_leg)
    strategy_pnl = gross_pnl − residual_gold_pnl
    net = gross − costs − slippage
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional


@dataclass
class TradeEntry:
    """A single trade entry in the backtest ledger."""
    trade_id: str
    pair_name: str
    entry_date: date
    exit_date: Optional[date] = None
    exit_reason: str = ""  # 'REVERSION', 'TIME_STOP', 'UNSAFE_EXPIRY'

    # Contracts
    leg_a_contract_id: str = ""
    leg_b_contract_id: str = ""

    # Lots and sizing
    lots_a: int = 0
    lots_b: int = 0
    residual_fine_g: float = 0.0

    # Entry prices (after slippage)
    entry_price_a: float = 0.0
    entry_price_b: float = 0.0
    entry_spread: float = 0.0

    # Exit prices (after slippage)
    exit_price_a: float = 0.0
    exit_price_b: float = 0.0
    exit_spread: float = 0.0

    # P&L components
    gross_pnl: float = 0.0
    residual_gold_pnl: float = 0.0
    strategy_pnl: float = 0.0
    total_costs: float = 0.0
    total_slippage: float = 0.0
    net_pnl: float = 0.0

    # Metadata
    fold_index: int = 0
    is_holdout: bool = False
    holding_days: int = 0
    entry_zscore: float = 0.0
    exit_zscore: Optional[float] = None
    rich_leg: str = ""


def compute_trade_pnl(
    entry_norm_a: float,
    entry_norm_b: float,
    exit_norm_a: float,
    exit_norm_b: float,
    lots_a: int,
    lots_b: int,
    fine_grams_a: float,
    fine_grams_b: float,
    residual_fine_g: float,
    total_costs: float,
    total_slippage: float,
    rich_leg: str = "A",
) -> Dict[str, float]:
    """Compute P&L attribution for a single trade.

    The trade is: short the rich leg, long the cheap leg.
    If rich_leg == 'A': short A, long B.
    If rich_leg == 'B': short B, long A.

    Attribution per Design §6.15:
        gross_pnl = Σ (exit - entry) × lots × fine_grams × direction
        residual_gold_pnl = residual_fine_g / 10 × ΔP_norm(ref_leg)
        strategy_pnl = gross_pnl − residual_gold_pnl
        net = gross − costs − slippage

    Parameters
    ----------
    entry_norm_a, entry_norm_b : float
        Normalized entry prices (₹/10g 999) for legs A and B.
    exit_norm_a, exit_norm_b : float
        Normalized exit prices.
    lots_a, lots_b : int
        Integer lot counts.
    fine_grams_a, fine_grams_b : float
        Fine grams per lot for each leg.
    residual_fine_g : float
        Unhedged fine grams (n_A*g_A - n_B*g_B).
    total_costs, total_slippage : float
        Itemized costs and slippage in ₹.
    rich_leg : str
        Which leg is rich ('A' or 'B'). Rich leg is shorted.

    Returns
    -------
    dict with keys: gross_pnl, residual_gold_pnl, strategy_pnl, net_pnl
    """
    # Direction: short rich, long cheap
    # P&L = (entry_price - exit_price) for short leg × notional
    #      + (exit_price - entry_price) for long leg × notional
    # Normalized prices are per 10g, so notional factor = lots × fine_grams / 10

    notional_a = lots_a * fine_grams_a / 10.0  # in units of 10g
    notional_b = lots_b * fine_grams_b / 10.0

    delta_a = exit_norm_a - entry_norm_a  # price change per 10g for A
    delta_b = exit_norm_b - entry_norm_b

    if rich_leg == "A":
        # Short A (profit when A falls), Long B (profit when B rises)
        gross_pnl = -delta_a * notional_a + delta_b * notional_b
    else:
        # Short B, Long A
        gross_pnl = delta_a * notional_a - delta_b * notional_b

    # Residual gold P&L: attributed to unhedged gold exposure
    # Use the average delta as reference
    ref_delta = (delta_a + delta_b) / 2.0
    residual_gold_pnl = (residual_fine_g / 10.0) * ref_delta

    strategy_pnl = gross_pnl - residual_gold_pnl
    net_pnl = gross_pnl - total_costs - total_slippage

    return {
        "gross_pnl": round(gross_pnl, 2),
        "residual_gold_pnl": round(residual_gold_pnl, 2),
        "strategy_pnl": round(strategy_pnl, 2),
        "net_pnl": round(net_pnl, 2),
    }


def should_exit(
    holding_days: int,
    current_zscore: Optional[float],
    days_to_expiry_a: int,
    days_to_expiry_b: int,
    exit_z: float = 0.5,
    max_holding_days: int = 15,
    unsafe_expiry_window_days: int = 5,
) -> Optional[str]:
    """Check exit conditions. Returns reason or None if no exit.

    Exit conditions (first match):
    1. REVERSION: |z| < exit_z (spread has reverted)
    2. TIME_STOP: holding_days >= max_holding_days
    3. UNSAFE_EXPIRY: either leg within unsafe window

    Parameters
    ----------
    Returns 'REVERSION', 'TIME_STOP', 'UNSAFE_EXPIRY', or None.
    """
    # Reversion
    if current_zscore is not None and abs(current_zscore) < exit_z:
        return "REVERSION"

    # Time stop
    if holding_days >= max_holding_days:
        return "TIME_STOP"

    # Unsafe expiry
    min_dte = min(days_to_expiry_a, days_to_expiry_b)
    if min_dte <= unsafe_expiry_window_days:
        return "UNSAFE_EXPIRY"

    return None
