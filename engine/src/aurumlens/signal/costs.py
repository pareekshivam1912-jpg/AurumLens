"""Itemized cost model for AurumLens cross-contract trades.

Implements Design §6.9. For each leg (A, B) and each side (buy, sell):

| Component  | Formula                                      |
|------------|----------------------------------------------|
| Brokerage  | min(flat_inr, pct × V)  (mode: min_flat_pct) |
| Exchange   | exchange.rate × V                            |
| SEBI fee   | sebi.rate × V                                |
| CTT        | ctt_sell.rate × V,  **sell side only**        |
| Stamp duty | stamp_buy.rate × V, **buy side only**         |
| GST        | gst.rate × (brokerage + exchange + sebi)      |

Total = sum over 2 legs × 2 sides. Every component stored as a CostLine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass(frozen=True)
class CostLine:
    """Single cost component for one leg on one side."""
    component: str   # 'brokerage', 'ctt', 'exchange', 'sebi', 'stamp', 'gst'
    leg: str         # 'A' or 'B'
    side: str        # 'buy' or 'sell'
    amount_inr: float


@dataclass(frozen=True)
class CostBreakdown:
    """Itemized cost breakdown for a pair trade (2 legs × 2 sides)."""
    lines: List[CostLine]
    total_inr: float
    cost_per_10g: float  # total / (pair_fine_grams / 10)

    def by_component(self) -> dict[str, float]:
        """Sum amounts by component name."""
        result: dict[str, float] = {}
        for line in self.lines:
            result[line.component] = result.get(line.component, 0.0) + line.amount_inr
        return result


def compute_leg_side_costs(
    turnover_inr: float,
    side: str,
    leg: str,
    brokerage_flat_inr: float = 20.0,
    brokerage_pct: float = 0.0003,
    brokerage_mode: str = "min_flat_pct",
    ctt_sell_rate: float = 0.0001,
    exchange_rate: float = 0.000021,
    sebi_rate: float = 0.000001,
    stamp_buy_rate: float = 0.00002,
    gst_rate: float = 0.18,
) -> List[CostLine]:
    """Compute all cost components for one leg on one side.

    Parameters
    ----------
    turnover_inr : float
        Trade turnover value in INR for this leg-side.
    side : str
        'buy' or 'sell'.
    leg : str
        'A' or 'B'.

    Returns
    -------
    list[CostLine]
        Individual cost components.
    """
    if side not in ("buy", "sell"):
        raise ValueError(f"side must be 'buy' or 'sell', got '{side}'")
    if leg not in ("A", "B"):
        raise ValueError(f"leg must be 'A' or 'B', got '{leg}'")

    lines: List[CostLine] = []

    # Brokerage
    if brokerage_mode == "min_flat_pct":
        brokerage = min(brokerage_flat_inr, brokerage_pct * turnover_inr)
    elif brokerage_mode == "flat":
        brokerage = brokerage_flat_inr
    elif brokerage_mode == "pct":
        brokerage = brokerage_pct * turnover_inr
    else:
        brokerage = min(brokerage_flat_inr, brokerage_pct * turnover_inr)

    lines.append(CostLine("brokerage", leg, side, round(brokerage, 4)))

    # Exchange fee
    exchange_fee = exchange_rate * turnover_inr
    lines.append(CostLine("exchange", leg, side, round(exchange_fee, 4)))

    # SEBI fee
    sebi_fee = sebi_rate * turnover_inr
    lines.append(CostLine("sebi", leg, side, round(sebi_fee, 4)))

    # CTT — sell side only
    if side == "sell":
        ctt = ctt_sell_rate * turnover_inr
        lines.append(CostLine("ctt", leg, side, round(ctt, 4)))

    # Stamp duty — buy side only
    if side == "buy":
        stamp = stamp_buy_rate * turnover_inr
        lines.append(CostLine("stamp", leg, side, round(stamp, 4)))

    # GST on base (brokerage + exchange + sebi), NOT on CTT or stamp
    gst_base = brokerage + exchange_fee + sebi_fee
    gst = gst_rate * gst_base
    lines.append(CostLine("gst", leg, side, round(gst, 4)))

    return lines


def compute_pair_costs(
    turnover_a: float,
    turnover_b: float,
    pair_fine_grams: float,
    **cost_params: Any,
) -> CostBreakdown:
    """Compute full itemized cost breakdown for a pair trade.

    Each leg has an entry (buy) and exit (sell) side.

    Parameters
    ----------
    turnover_a : float
        Turnover in INR for leg A (one side).
    turnover_b : float
        Turnover in INR for leg B (one side).
    pair_fine_grams : float
        Total fine grams in the smaller leg (for cost-per-10g calculation).
    """
    all_lines: List[CostLine] = []

    for leg, turnover in [("A", turnover_a), ("B", turnover_b)]:
        for side in ("buy", "sell"):
            side_lines = compute_leg_side_costs(
                turnover_inr=turnover, side=side, leg=leg, **cost_params
            )
            all_lines.extend(side_lines)

    total = sum(line.amount_inr for line in all_lines)
    cost_per_10g = total / (pair_fine_grams / 10.0) if pair_fine_grams > 0 else 0.0

    return CostBreakdown(
        lines=all_lines,
        total_inr=round(total, 2),
        cost_per_10g=round(cost_per_10g, 2),
    )


def compute_costs_from_config(
    turnover_a: float,
    turnover_b: float,
    pair_fine_grams: float,
    costs_config: Any,
) -> CostBreakdown:
    """Convenience: compute pair costs using the Pydantic CostsConfig model."""
    params: dict[str, Any] = {}

    if hasattr(costs_config, "brokerage"):
        b = costs_config.brokerage
        params["brokerage_flat_inr"] = b.flat_inr or 20.0
        params["brokerage_pct"] = b.pct or 0.0003
        params["brokerage_mode"] = b.mode or "min_flat_pct"

    if hasattr(costs_config, "ctt_sell"):
        params["ctt_sell_rate"] = costs_config.ctt_sell.rate or 0.0001

    if hasattr(costs_config, "exchange"):
        params["exchange_rate"] = costs_config.exchange.rate or 0.000021

    if hasattr(costs_config, "sebi"):
        params["sebi_rate"] = costs_config.sebi.rate or 0.000001

    if hasattr(costs_config, "stamp_buy"):
        params["stamp_buy_rate"] = costs_config.stamp_buy.rate or 0.00002

    if hasattr(costs_config, "gst"):
        params["gst_rate"] = costs_config.gst.rate or 0.18

    return compute_pair_costs(turnover_a, turnover_b, pair_fine_grams, **params)
