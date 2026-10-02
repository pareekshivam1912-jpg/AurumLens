"""AurumLens Analytics Module - Normalization, Sizing, Pairing, Carry, and Spread."""

from aurumlens.analytics.normalization import (
    normalize,
    normalize_contract_price,
    normalize_price,
    purity_direction_test,
)
from aurumlens.analytics.sizing import (
    SizingResult,
    calculate_lot_ratio,
    compute_lot_ratio,
    fine_grams_per_lot,
    lot_ratio,
    size_contracts,
    size_pair,
)
from aurumlens.analytics.pairing import (
    ContractInfo,
    PairMatch,
    NO_EXPIRY_PAIR,
    NO_EXPIRY_PAIR_REASON,
    compute_expiry_gap_days,
    find_best_pair,
)
from aurumlens.analytics.carry import (
    CarryResult,
    compute_curve_carry_rate,
    compute_carry_adjustment,
    compute_carry_adj,
    compute_carry,
    DAYS_IN_YEAR,
    SOURCE_CURVE,
    SOURCE_FALLBACK,
)
from aurumlens.analytics.spread import (
    SpreadResult,
    compute_log_spread,
    compute_zscore,
    compute_mad_score,
    compute_spread,
)

__all__ = [
    # Normalization
    "normalize",
    "normalize_price",
    "normalize_contract_price",
    "purity_direction_test",
    # Sizing
    "fine_grams_per_lot",
    "calculate_lot_ratio",
    "compute_lot_ratio",
    "lot_ratio",
    "size_pair",
    "size_contracts",
    "SizingResult",
    # Pairing
    "ContractInfo",
    "PairMatch",
    "NO_EXPIRY_PAIR",
    "NO_EXPIRY_PAIR_REASON",
    "compute_expiry_gap_days",
    "find_best_pair",
    # Carry
    "CarryResult",
    "compute_curve_carry_rate",
    "compute_carry_adjustment",
    "compute_carry_adj",
    "compute_carry",
    "DAYS_IN_YEAR",
    "SOURCE_CURVE",
    "SOURCE_FALLBACK",
    # Spread
    "SpreadResult",
    "compute_log_spread",
    "compute_zscore",
    "compute_mad_score",
    "compute_spread",
]
