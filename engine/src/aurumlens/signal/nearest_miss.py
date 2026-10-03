"""Nearest-miss service for QUIET pair-days.

Implements Design §6.12 and FR17.

For a QUIET pair-day, compute each numeric gate's ratio (capped at 1.0):
- |z| / entry_z
- net_edge / hurdle
- volume / min_volume, OI / min_oi (both legs)

near_miss_score = (number_of_gates_passed, min_ratio_over_failing_gates)
Rank pairs by (gates_passed DESC, min_failing_ratio DESC).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from aurumlens.signal.gates import GateConfig, GateResult, PairDayInput


@dataclass(frozen=True)
class NearMissResult:
    """Near-miss analysis for a QUIET pair-day."""
    pair_name: str
    gates_passed: int
    gates_total: int
    min_failing_ratio: float
    blocking_gates: List[str]
    ratios: Dict[str, float]


def _safe_ratio(value: Optional[float], threshold: float) -> float:
    """Compute value/threshold ratio, capped at 1.0. Returns 0.0 if threshold is 0."""
    if threshold <= 0 or value is None:
        return 0.0
    return min(value / threshold, 1.0)


def compute_near_miss(
    gate_results: List[GateResult],
    pair_day: PairDayInput,
    config: GateConfig,
) -> NearMissResult:
    """Compute near-miss score for a pair-day.

    Parameters
    ----------
    gate_results : list[GateResult]
        Results from evaluate_gates (all 12 gates).
    pair_day : PairDayInput
        Input data for the pair-day.
    config : GateConfig
        Gate thresholds.

    Returns
    -------
    NearMissResult
    """
    # Compute ratios for numeric gates
    abs_z = abs(pair_day.zscore) if pair_day.zscore is not None else 0.0
    hurdle = pair_day.total_costs_inr + pair_day.slippage_inr + pair_day.safety_buffer_inr

    ratios: Dict[str, float] = {
        "Z_SCORE_THRESHOLD": _safe_ratio(abs_z, config.entry_z),
        "COST_HURDLE": _safe_ratio(pair_day.expected_convergence_inr, hurdle) if hurdle > 0 else (1.0 if pair_day.expected_convergence_inr > 0 else 0.0),
        "LIQUIDITY_VOLUME_A": _safe_ratio(pair_day.volume_a, config.min_volume),
        "LIQUIDITY_VOLUME_B": _safe_ratio(pair_day.volume_b, config.min_volume),
        "LIQUIDITY_OI_A": _safe_ratio(pair_day.oi_a, config.min_oi),
        "LIQUIDITY_OI_B": _safe_ratio(pair_day.oi_b, config.min_oi),
    }

    # Count passes and find blocking gates
    gates_passed = sum(1 for g in gate_results if g.passed)
    gates_total = len(gate_results)
    blocking = [g.reason_code for g in gate_results if not g.passed and g.reason_code]

    # Minimum ratio over failing numeric gates
    failing_ratios: List[float] = []
    for g in gate_results:
        if not g.passed and g.gate_name in ratios:
            failing_ratios.append(ratios[g.gate_name])

    min_failing = min(failing_ratios) if failing_ratios else 0.0

    return NearMissResult(
        pair_name=pair_day.pair_name,
        gates_passed=gates_passed,
        gates_total=gates_total,
        min_failing_ratio=round(min_failing, 6),
        blocking_gates=blocking,
        ratios=ratios,
    )


def rank_near_misses(results: List[NearMissResult]) -> List[NearMissResult]:
    """Rank near-miss results: most gates passed first, then highest min ratio.

    Returns
    -------
    list[NearMissResult]
        Sorted list, best near-miss first.
    """
    return sorted(
        results,
        key=lambda r: (r.gates_passed, r.min_failing_ratio),
        reverse=True,
    )
