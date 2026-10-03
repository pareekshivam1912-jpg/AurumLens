"""Evidence record builder for AurumLens pair-day signals.

Implements PRD §11. Each pair-day record (ALERT or QUIET) contains:
- Identity: pair, trade date, contracts, expiries, gap
- Prices: quoted, source, quality flags, normalized
- Spread and score: carry, spread, z-score, rich leg
- Economics: convergence, costs, slippage, safety, net edge
- Liquidity: volume, OI for both legs
- Sizing: lot ratio and residual fine grams
- Gates: pass/fail and margin for every gate, plus reason codes
- Nearest miss: how close the pair came to alerting
- Versioning: config_version, dataset_version
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, List, Optional

from aurumlens.signal.gates import GateResult, determine_status, collect_reason_codes


@dataclass
class EvidenceRecord:
    """Complete evidence record for a pair-day signal."""
    # Identity
    pair_name: str
    trade_date: date
    leg_a_contract_id: str = ""
    leg_b_contract_id: str = ""
    leg_a_expiry: Optional[date] = None
    leg_b_expiry: Optional[date] = None
    expiry_gap_days: int = 0

    # Prices
    quoted_price_a: float = 0.0
    quoted_price_b: float = 0.0
    price_source: str = "close"
    quality_a: str = "OK"
    quality_b: str = "OK"
    normalized_price_a: float = 0.0
    normalized_price_b: float = 0.0

    # Spread and score
    carry_rate: float = 0.0
    carry_source: str = "FALLBACK"
    log_spread_raw: float = 0.0
    log_spread_adj: float = 0.0
    roll_mean: Optional[float] = None
    roll_std: Optional[float] = None
    zscore: Optional[float] = None
    rich_leg: Optional[str] = None

    # Economics
    expected_convergence_inr: float = 0.0
    cost_breakdown: Any = None
    slippage_estimate: float = 0.0
    slippage_model: str = "corwin_schultz"
    safety_buffer_inr: float = 0.0
    net_expected_edge_inr: float = 0.0

    # Liquidity
    volume_a: float = 0.0
    volume_b: float = 0.0
    volume_sma_a: Optional[float] = None
    volume_sma_b: Optional[float] = None
    oi_a: float = 0.0
    oi_b: float = 0.0

    # Sizing
    lots_a: int = 0
    lots_b: int = 0
    residual_fine_g: float = 0.0

    # Gates
    gate_results: List[GateResult] = field(default_factory=list)
    status: str = "QUIET"
    reason_codes: List[str] = field(default_factory=list)

    # Nearest miss
    near_miss_score: Optional[tuple] = None

    # Versioning
    config_version: str = ""
    dataset_version: str = ""


def build_evidence_record(
    pair_name: str,
    trade_date: date,
    gate_results: List[GateResult],
    **kwargs: Any,
) -> EvidenceRecord:
    """Build a complete evidence record from gate results and computed analytics.

    Automatically determines status (ALERT/QUIET) and collects reason codes.
    """
    status = determine_status(gate_results)
    reason_codes = collect_reason_codes(gate_results)

    # Compute net expected edge
    expected_conv = kwargs.get("expected_convergence_inr", 0.0)
    total_costs = 0.0
    cost_breakdown = kwargs.get("cost_breakdown")
    if cost_breakdown is not None and hasattr(cost_breakdown, "total_inr"):
        total_costs = cost_breakdown.total_inr
    slippage_est = kwargs.get("slippage_estimate", 0.0)
    safety_buf = kwargs.get("safety_buffer_inr", 0.0)
    net_edge = expected_conv - total_costs - slippage_est - safety_buf

    return EvidenceRecord(
        pair_name=pair_name,
        trade_date=trade_date,
        gate_results=gate_results,
        status=status,
        reason_codes=reason_codes,
        net_expected_edge_inr=round(net_edge, 2),
        **{k: v for k, v in kwargs.items()
           if k in EvidenceRecord.__dataclass_fields__ and k not in (
               "gate_results", "status", "reason_codes", "net_expected_edge_inr",
           )},
    )
