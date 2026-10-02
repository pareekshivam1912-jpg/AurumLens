"""Smallest-gap expiry matching module for AurumLens cross-contract pairing.

Implements expiry matching per Design §6.4 (R17):
For each pair (A, B) and date t:
1. List active contracts of A and B that have rows on t.
2. For every combination, compute gap = |T_A - T_B| in calendar days.
3. Keep combinations with gap <= max_expiry_gap_days (from config).
4. Choose smallest gap. On tie: prefer nearer expiry, then higher combined OI.
5. Record both contract IDs and the gap. If nothing qualifies, return NO_EXPIRY_PAIR (None).

Fixture:
    GOLDTEN Oct-31 against GOLDM {Oct-5, Nov-5, Dec-5} must choose Nov-5 (gap 5).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class ContractInfo:
    """Metadata for an active contract on a given trade date.

    Attributes:
        contract_id: Canonical contract identifier (e.g. 'GOLDTEN_20261031').
        symbol: MCX symbol name (e.g. 'GOLDTEN', 'GOLDM').
        expiry_date: Contract expiry date.
        open_interest: Open interest on trade date t (default: 0.0).
    """

    contract_id: str
    symbol: str
    expiry_date: date
    open_interest: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.expiry_date, str):
            object.__setattr__(self, "expiry_date", date.fromisoformat(self.expiry_date))
        elif isinstance(self.expiry_date, datetime):
            object.__setattr__(self, "expiry_date", self.expiry_date.date())
        if not isinstance(self.open_interest, float):
            object.__setattr__(self, "open_interest", float(self.open_interest or 0.0))


@dataclass(frozen=True)
class PairMatch:
    """Selected contract pairing result based on smallest expiry gap.

    Attributes:
        leg_a_contract_id: Selected contract ID for leg A.
        leg_b_contract_id: Selected contract ID for leg B.
        leg_a_expiry: Expiry date of leg A contract.
        leg_b_expiry: Expiry date of leg B contract.
        expiry_gap_days: Absolute difference |T_A - T_B| in calendar days.
        combined_oi: Combined open interest across both legs.
    """

    leg_a_contract_id: str
    leg_b_contract_id: str
    leg_a_expiry: date
    leg_b_expiry: date
    expiry_gap_days: int
    combined_oi: float


# Sentinel / alias for when no expiry pair qualifies
NO_EXPIRY_PAIR: Optional[PairMatch] = None
NO_EXPIRY_PAIR_REASON: str = "NO_EXPIRY_PAIR"


def compute_expiry_gap_days(expiry_a: date | str, expiry_b: date | str) -> int:
    """Compute absolute calendar day gap |T_A - T_B| between two expiries."""
    d_a = date.fromisoformat(expiry_a) if isinstance(expiry_a, str) else expiry_a
    d_b = date.fromisoformat(expiry_b) if isinstance(expiry_b, str) else expiry_b
    return abs((d_a - d_b).days)


def find_best_pair(
    symbol_a: str,
    symbol_b: str,
    active_contracts_a: list[ContractInfo],
    active_contracts_b: list[ContractInfo],
    max_expiry_gap_days: int = 35,
) -> Optional[PairMatch]:
    """Find the optimal contract pairing between two symbols by smallest expiry gap.

    Per Design §6.4 (R17):
    1. Filters active contracts of A and B on date t.
    2. Computes gap = |T_A - T_B| in calendar days for every combination.
    3. Keeps combinations with gap <= max_expiry_gap_days.
    4. Selects smallest gap. On tie: prefers nearer expiry (earlier calendar date),
       then higher combined OI.
    5. Returns PairMatch if a combination qualifies, else NO_EXPIRY_PAIR (None).

    Fixture Check:
        GOLDTEN Oct-31 against GOLDM {Oct-5, Nov-5, Dec-5}:
        - Oct-31 vs Oct-5: gap = 26 days
        - Oct-31 vs Nov-5: gap = 5 days  <-- chosen (smallest gap)
        - Oct-31 vs Dec-5: gap = 35 days

    Args:
        symbol_a: Symbol name for leg A (e.g. 'GOLDTEN').
        symbol_b: Symbol name for leg B (e.g. 'GOLDM').
        active_contracts_a: Active contracts of symbol A with data on date t.
        active_contracts_b: Active contracts of symbol B with data on date t.
        max_expiry_gap_days: Maximum allowable calendar day gap (default: 35).

    Returns:
        PairMatch containing selected contracts and gap, or None if none qualify.
    """
    if not active_contracts_a or not active_contracts_b:
        return NO_EXPIRY_PAIR

    if max_expiry_gap_days < 0:
        return NO_EXPIRY_PAIR

    # Filter contracts matching symbol_a and symbol_b if symbols are populated
    contracts_a = [
        c for c in active_contracts_a
        if not c.symbol or c.symbol.upper() == symbol_a.upper()
    ]
    contracts_b = [
        c for c in active_contracts_b
        if not c.symbol or c.symbol.upper() == symbol_b.upper()
    ]

    if not contracts_a or not contracts_b:
        return NO_EXPIRY_PAIR

    candidates: list[tuple[int, date, float, date, ContractInfo, ContractInfo]] = []

    for ca in contracts_a:
        exp_a = ca.expiry_date
        if isinstance(exp_a, str):
            exp_a = date.fromisoformat(exp_a)
        elif isinstance(exp_a, datetime):
            exp_a = exp_a.date()

        for cb in contracts_b:
            exp_b = cb.expiry_date
            if isinstance(exp_b, str):
                exp_b = date.fromisoformat(exp_b)
            elif isinstance(exp_b, datetime):
                exp_b = exp_b.date()

            gap = abs((exp_a - exp_b).days)
            if gap <= max_expiry_gap_days:
                combined_oi = float((ca.open_interest or 0.0) + (cb.open_interest or 0.0))
                nearer_expiry = min(exp_a, exp_b)

                # Rank tuple:
                # 1. gap: smallest gap first
                # 2. nearer_expiry: earlier calendar date first (nearer expiry)
                # 3. -combined_oi: higher open interest first
                # 4. exp_a: earlier leg A expiry
                # 5. contract IDs for deterministic tie breaking
                candidates.append((
                    gap,
                    nearer_expiry,
                    -combined_oi,
                    exp_a,
                    ca,
                    cb,
                ))

    if not candidates:
        return NO_EXPIRY_PAIR

    candidates.sort(key=lambda item: (
        item[0],
        item[1],
        item[2],
        item[3],
        item[4].contract_id,
        item[5].contract_id,
    ))

    best = candidates[0]
    best_ca = best[4]
    best_cb = best[5]
    best_gap = best[0]
    best_oi = -best[2]

    exp_a_clean = (
        best_ca.expiry_date
        if isinstance(best_ca.expiry_date, date)
        else date.fromisoformat(str(best_ca.expiry_date))
    )
    exp_b_clean = (
        best_cb.expiry_date
        if isinstance(best_cb.expiry_date, date)
        else date.fromisoformat(str(best_cb.expiry_date))
    )

    return PairMatch(
        leg_a_contract_id=best_ca.contract_id,
        leg_b_contract_id=best_cb.contract_id,
        leg_a_expiry=exp_a_clean,
        leg_b_expiry=exp_b_clean,
        expiry_gap_days=best_gap,
        combined_oi=best_oi,
    )
