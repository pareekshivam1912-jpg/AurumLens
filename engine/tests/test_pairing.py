"""Tests for smallest-gap expiry matching (R17, Design §6.4).

Key Fixture:
    GOLDTEN Oct-31 against GOLDM {Oct-5, Nov-5, Dec-5} must choose Nov-5 (gap 5).
"""

from datetime import date
import pytest

from aurumlens.analytics.pairing import (
    ContractInfo,
    NO_EXPIRY_PAIR,
    compute_expiry_gap_days,
    find_best_pair,
)


def test_hand_fixture_goldten_nov5_pairing():
    """Design §6.4 Fixture: GOLDTEN Oct-31 against GOLDM {Oct-5, Nov-5, Dec-5} must choose Nov-5.

    Gap calculation:
    - Oct-31 vs Oct-5 = 26 days
    - Oct-31 vs Nov-5 = 5 days  <-- SMALLEST
    - Oct-31 vs Dec-5 = 35 days
    """
    contracts_goldten = [
        ContractInfo(
            contract_id="GOLDTEN_20261031",
            symbol="GOLDTEN",
            expiry_date=date(2026, 10, 31),
            open_interest=500,
        )
    ]

    contracts_goldm = [
        ContractInfo(
            contract_id="GOLDM_20261005",
            symbol="GOLDM",
            expiry_date=date(2026, 10, 5),
            open_interest=2000,
        ),
        ContractInfo(
            contract_id="GOLDM_20261105",
            symbol="GOLDM",
            expiry_date=date(2026, 11, 5),
            open_interest=1500,
        ),
        ContractInfo(
            contract_id="GOLDM_20261205",
            symbol="GOLDM",
            expiry_date=date(2026, 12, 5),
            open_interest=800,
        ),
    ]

    match = find_best_pair(
        symbol_a="GOLDTEN",
        symbol_b="GOLDM",
        active_contracts_a=contracts_goldten,
        active_contracts_b=contracts_goldm,
        max_expiry_gap_days=35,
    )

    assert match is not None
    assert match.leg_a_contract_id == "GOLDTEN_20261031"
    assert match.leg_b_contract_id == "GOLDM_20261105"
    assert match.leg_b_expiry == date(2026, 11, 5)
    assert match.expiry_gap_days == 5


def test_max_expiry_gap_exceeded_returns_none():
    """If all combinations exceed max_expiry_gap_days, return NO_EXPIRY_PAIR (None)."""
    contracts_a = [
        ContractInfo(
            contract_id="GOLDTEN_20261031",
            symbol="GOLDTEN",
            expiry_date=date(2026, 10, 31),
        )
    ]
    contracts_b = [
        ContractInfo(
            contract_id="GOLDM_20261215",
            symbol="GOLDM",
            expiry_date=date(2026, 12, 15),  # 45 days gap > 35
        )
    ]

    match = find_best_pair(
        symbol_a="GOLDTEN",
        symbol_b="GOLDM",
        active_contracts_a=contracts_a,
        active_contracts_b=contracts_b,
        max_expiry_gap_days=35,
    )
    assert match is NO_EXPIRY_PAIR


def test_tie_breaking_prefers_nearer_expiry():
    """On equal expiry gap, prefer the combination with the nearer expiry date."""
    # Target date reference: T_target = 2026-10-15
    # Pair candidate 1: A=2026-10-10, B=2026-10-20 -> gap=10, min_expiry=2026-10-10
    # Pair candidate 2: A=2026-11-10, B=2026-11-20 -> gap=10, min_expiry=2026-11-10
    contracts_a = [
        ContractInfo("A_NEAR", "A", date(2026, 10, 10), open_interest=100),
        ContractInfo("A_FAR", "A", date(2026, 11, 10), open_interest=100),
    ]
    contracts_b = [
        ContractInfo("B_NEAR", "B", date(2026, 10, 20), open_interest=100),
        ContractInfo("B_FAR", "B", date(2026, 11, 20), open_interest=100),
    ]

    match = find_best_pair("A", "B", contracts_a, contracts_b, max_expiry_gap_days=35)
    assert match is not None
    assert match.leg_a_contract_id == "A_NEAR"
    assert match.leg_b_contract_id == "B_NEAR"


def test_tie_breaking_prefers_higher_combined_oi():
    """On equal gap and equal expiry, prefer higher combined OI."""
    contracts_a = [
        ContractInfo("A_1", "A", date(2026, 11, 5), open_interest=500),
    ]
    contracts_b = [
        ContractInfo("B_LOW_OI", "B", date(2026, 11, 10), open_interest=100),
        ContractInfo("B_HIGH_OI", "B", date(2026, 11, 10), open_interest=900),
    ]

    match = find_best_pair("A", "B", contracts_a, contracts_b, max_expiry_gap_days=35)
    assert match is not None
    assert match.leg_b_contract_id == "B_HIGH_OI"
    assert match.combined_oi == 1400.0
