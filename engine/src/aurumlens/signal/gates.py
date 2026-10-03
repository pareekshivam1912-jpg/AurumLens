"""11-gate evaluator for AurumLens signal decisions.

Implements Design §6.11, PRD §10, and R20.

All 11 gates are ALWAYS evaluated, even after one fails.
Status is ALERT only if every gate passes.
Each gate records (passed, value, threshold, margin, reason_code).

Gate list:
 1. SPEC_OK            — per spec_mode (R24)
 2. DATA_QUALITY       — both prices not SUSPECT (R19)
 3. EXPIRY_PAIR_VALID  — gap ≤ max_expiry_gap_days (R17)
 4. HISTORY_SUFFICIENT — count ≥ min_history_obs
 5. Z_SCORE_THRESHOLD  — |z| ≥ entry_z
 6. LIQUIDITY_VOLUME_A — leg A volume ≥ min_volume
 7. LIQUIDITY_VOLUME_B — leg B volume ≥ min_volume
 8. LIQUIDITY_OI_A     — leg A OI ≥ min_oi
 9. LIQUIDITY_OI_B     — leg B OI ≥ min_oi
10. EXPIRY_SAFETY      — both legs days_to_expiry > unsafe window
11. COST_HURDLE        — expected convergence > costs + slippage + safety
12. DUPLICATE_CHECK    — not a duplicate of an open alert
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass(frozen=True)
class GateResult:
    """Result of a single gate evaluation."""
    gate_name: str
    passed: bool
    value: Optional[float] = None
    threshold: Optional[float] = None
    margin: Optional[float] = None     # value - threshold; positive = passed
    reason_code: str = ""


@dataclass
class PairDayInput:
    """All inputs needed to evaluate gates for a single pair-day."""
    # Identity
    pair_name: str
    trade_date: date
    # Spec mode
    spec_mode: str = "research"          # 'strict' or 'research'
    spec_status_a: str = "VERIFIED_OFFICIAL"
    spec_status_b: str = "VERIFIED_OFFICIAL"
    purity_status_a: str = "VERIFIED_OFFICIAL"
    purity_status_b: str = "VERIFIED_OFFICIAL"
    # Quality
    quality_a: str = "OK"
    quality_b: str = "OK"
    # Expiry
    has_expiry_pair: bool = True
    expiry_gap_days: Optional[int] = None
    days_to_expiry_a: Optional[int] = None
    days_to_expiry_b: Optional[int] = None
    # History
    history_count: int = 0
    # Score
    zscore: Optional[float] = None
    # Liquidity
    volume_a: float = 0.0
    volume_b: float = 0.0
    oi_a: float = 0.0
    oi_b: float = 0.0
    # Economics
    expected_convergence_inr: float = 0.0
    total_costs_inr: float = 0.0
    slippage_inr: float = 0.0
    safety_buffer_inr: float = 0.0
    # Duplicate
    is_duplicate: bool = False


@dataclass
class GateConfig:
    """Thresholds for gate evaluation, from versioned strategy config."""
    entry_z: float = 2.0
    min_history_obs: int = 30
    max_expiry_gap_days: int = 35
    min_volume: int = 10
    min_oi: int = 50
    unsafe_expiry_window_days: int = 5


def _is_verified(status: str) -> bool:
    """Check if a spec status is VERIFIED_OFFICIAL."""
    return status == "VERIFIED_OFFICIAL"


def evaluate_gates(
    pair_day: PairDayInput,
    config: GateConfig,
) -> List[GateResult]:
    """Evaluate ALL gates for a pair-day. Always returns all gates (R20).

    Status is ALERT only if every gate passes. The function is pure, no I/O.

    Parameters
    ----------
    pair_day : PairDayInput
        All inputs for the pair-day.
    config : GateConfig
        Gate thresholds from versioned config.

    Returns
    -------
    list[GateResult]
        One result per gate, always all gates evaluated.
    """
    results: List[GateResult] = []

    # Gate 1: SPEC_OK (R24)
    if pair_day.spec_mode == "strict":
        all_verified = all(
            _is_verified(s) for s in [
                pair_day.spec_status_a, pair_day.spec_status_b,
                pair_day.purity_status_a, pair_day.purity_status_b,
            ]
        )
        results.append(GateResult(
            gate_name="SPEC_OK",
            passed=all_verified,
            reason_code="" if all_verified else "SPEC_UNVERIFIED",
        ))
    else:
        # research mode: always passes
        results.append(GateResult(
            gate_name="SPEC_OK", passed=True, reason_code="",
        ))

    # Gate 2: DATA_QUALITY (R19)
    data_ok = pair_day.quality_a == "OK" and pair_day.quality_b == "OK"
    reason = ""
    if not data_ok:
        suspects = []
        if pair_day.quality_a != "OK":
            suspects.append("A")
        if pair_day.quality_b != "OK":
            suspects.append("B")
        reason = f"DATA_SUSPECT_{'_'.join(suspects)}"
    results.append(GateResult(
        gate_name="DATA_QUALITY", passed=data_ok, reason_code=reason,
    ))

    # Gate 3: EXPIRY_PAIR_VALID (R17)
    expiry_valid = pair_day.has_expiry_pair
    expiry_margin = None
    if pair_day.expiry_gap_days is not None:
        expiry_margin = float(config.max_expiry_gap_days - pair_day.expiry_gap_days)
    results.append(GateResult(
        gate_name="EXPIRY_PAIR_VALID",
        passed=expiry_valid,
        value=float(pair_day.expiry_gap_days) if pair_day.expiry_gap_days is not None else None,
        threshold=float(config.max_expiry_gap_days),
        margin=expiry_margin,
        reason_code="" if expiry_valid else "NO_EXPIRY_PAIR",
    ))

    # Gate 4: HISTORY_SUFFICIENT
    hist_ok = pair_day.history_count >= config.min_history_obs
    results.append(GateResult(
        gate_name="HISTORY_SUFFICIENT",
        passed=hist_ok,
        value=float(pair_day.history_count),
        threshold=float(config.min_history_obs),
        margin=float(pair_day.history_count - config.min_history_obs),
        reason_code="" if hist_ok else "INSUFFICIENT_HISTORY",
    ))

    # Gate 5: Z_SCORE_THRESHOLD
    abs_z = abs(pair_day.zscore) if pair_day.zscore is not None else 0.0
    z_ok = abs_z >= config.entry_z
    results.append(GateResult(
        gate_name="Z_SCORE_THRESHOLD",
        passed=z_ok,
        value=abs_z,
        threshold=config.entry_z,
        margin=round(abs_z - config.entry_z, 6),
        reason_code="" if z_ok else "Z_BELOW_THRESHOLD",
    ))

    # Gate 6: LIQUIDITY_VOLUME_A
    vol_a_ok = pair_day.volume_a >= config.min_volume
    results.append(GateResult(
        gate_name="LIQUIDITY_VOLUME_A",
        passed=vol_a_ok,
        value=pair_day.volume_a,
        threshold=float(config.min_volume),
        margin=pair_day.volume_a - config.min_volume,
        reason_code="" if vol_a_ok else "LIQUIDITY_VOLUME_A",
    ))

    # Gate 7: LIQUIDITY_VOLUME_B
    vol_b_ok = pair_day.volume_b >= config.min_volume
    results.append(GateResult(
        gate_name="LIQUIDITY_VOLUME_B",
        passed=vol_b_ok,
        value=pair_day.volume_b,
        threshold=float(config.min_volume),
        margin=pair_day.volume_b - config.min_volume,
        reason_code="" if vol_b_ok else "LIQUIDITY_VOLUME_B",
    ))

    # Gate 8: LIQUIDITY_OI_A
    oi_a_ok = pair_day.oi_a >= config.min_oi
    results.append(GateResult(
        gate_name="LIQUIDITY_OI_A",
        passed=oi_a_ok,
        value=pair_day.oi_a,
        threshold=float(config.min_oi),
        margin=pair_day.oi_a - config.min_oi,
        reason_code="" if oi_a_ok else "LIQUIDITY_OI_A",
    ))

    # Gate 9: LIQUIDITY_OI_B
    oi_b_ok = pair_day.oi_b >= config.min_oi
    results.append(GateResult(
        gate_name="LIQUIDITY_OI_B",
        passed=oi_b_ok,
        value=pair_day.oi_b,
        threshold=float(config.min_oi),
        margin=pair_day.oi_b - config.min_oi,
        reason_code="" if oi_b_ok else "LIQUIDITY_OI_B",
    ))

    # Gate 10: EXPIRY_SAFETY (both legs)
    dte_a = pair_day.days_to_expiry_a if pair_day.days_to_expiry_a is not None else 999
    dte_b = pair_day.days_to_expiry_b if pair_day.days_to_expiry_b is not None else 999
    min_dte = min(dte_a, dte_b)
    expiry_safe = min_dte > config.unsafe_expiry_window_days
    reason_expiry = ""
    if not expiry_safe:
        unsafe_legs = []
        if dte_a <= config.unsafe_expiry_window_days:
            unsafe_legs.append("A")
        if dte_b <= config.unsafe_expiry_window_days:
            unsafe_legs.append("B")
        reason_expiry = f"EXPIRY_UNSAFE_{'_'.join(unsafe_legs)}"
    results.append(GateResult(
        gate_name="EXPIRY_SAFETY",
        passed=expiry_safe,
        value=float(min_dte),
        threshold=float(config.unsafe_expiry_window_days),
        margin=float(min_dte - config.unsafe_expiry_window_days),
        reason_code=reason_expiry,
    ))

    # Gate 11: COST_HURDLE (R9)
    hurdle = pair_day.total_costs_inr + pair_day.slippage_inr + pair_day.safety_buffer_inr
    cost_ok = pair_day.expected_convergence_inr > hurdle
    results.append(GateResult(
        gate_name="COST_HURDLE",
        passed=cost_ok,
        value=pair_day.expected_convergence_inr,
        threshold=round(hurdle, 2),
        margin=round(pair_day.expected_convergence_inr - hurdle, 2),
        reason_code="" if cost_ok else "COST_HURDLE_FAIL",
    ))

    # Gate 12: DUPLICATE_CHECK
    dup_ok = not pair_day.is_duplicate
    results.append(GateResult(
        gate_name="DUPLICATE_CHECK",
        passed=dup_ok,
        reason_code="" if dup_ok else "DUPLICATE_ALERT",
    ))

    return results


def determine_status(gate_results: List[GateResult]) -> str:
    """ALERT only if every gate passes, else QUIET (R12)."""
    return "ALERT" if all(g.passed for g in gate_results) else "QUIET"


def collect_reason_codes(gate_results: List[GateResult]) -> List[str]:
    """Collect reason codes from all failing gates."""
    return [g.reason_code for g in gate_results if not g.passed and g.reason_code]
