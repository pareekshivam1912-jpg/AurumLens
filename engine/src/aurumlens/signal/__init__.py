"""AurumLens Signal Engine — Costs, Slippage, Gates, Evidence, and Nearest-Miss."""

from aurumlens.signal.costs import (
    CostBreakdown,
    CostLine,
    compute_leg_side_costs,
    compute_pair_costs,
    compute_costs_from_config,
)
from aurumlens.signal.slippage import (
    SlippageEstimate,
    corwin_schultz_single,
    corwin_schultz_rolling,
    estimate_slippage,
    simulated_fill,
)
from aurumlens.signal.gates import (
    GateConfig,
    GateResult,
    PairDayInput,
    evaluate_gates,
    determine_status,
    collect_reason_codes,
)
from aurumlens.signal.evidence import (
    EvidenceRecord,
    build_evidence_record,
)
from aurumlens.signal.nearest_miss import (
    NearMissResult,
    compute_near_miss,
    rank_near_misses,
)

__all__ = [
    # Costs
    "CostBreakdown", "CostLine",
    "compute_leg_side_costs", "compute_pair_costs", "compute_costs_from_config",
    # Slippage
    "SlippageEstimate",
    "corwin_schultz_single", "corwin_schultz_rolling",
    "estimate_slippage", "simulated_fill",
    # Gates
    "GateConfig", "GateResult", "PairDayInput",
    "evaluate_gates", "determine_status", "collect_reason_codes",
    # Evidence
    "EvidenceRecord", "build_evidence_record",
    # Nearest miss
    "NearMissResult", "compute_near_miss", "rank_near_misses",
]
