"""Tests for contract price normalization (R16, Design §6.3).

Hand fixtures from Design §6.3:
| Contract | Quoted | Factor | Normalized ₹/10 g 999 |
|---|---|---|---|
| GOLDM (995, per 10 g) | 120,000 | 1.0 × 0.999/0.995 = 1.0040201 | 120,482.41 |
| GOLDTEN (999, per 10 g) | 120,500 | 1.0 | 120,500.00 |
| GOLDGUINEA (999, per 8 g) | 96,400 | 1.25 | 120,500.00 |
| GOLDPETAL (999, per 1 g) | 12,050 | 10 | 120,500.00 |
"""

from pathlib import Path
import pytest

from aurumlens.analytics.normalization import (
    normalize_contract_price,
    normalize_price,
    purity_direction_test,
)
from aurumlens.config.loader import load_contracts_config


def test_hand_fixture_goldm_120482():
    """GOLDM at 120,000 quoted (995 purity, 10g basis) normalizes to 120,482.41."""
    p_norm = normalize_price(
        price_used=120000.0,
        quote_basis_g=10.0,
        purity=0.995,
        target_purity=0.999,
        target_basis_g=10.0,
    )
    # 120000 * (10/10) * (0.999/0.995) = 120482.41206...
    assert round(p_norm, 2) == 120482.41


def test_hand_fixture_goldten():
    """GOLDTEN at 120,500 quoted (999 purity, 10g basis) normalizes to 120,500.00."""
    p_norm = normalize_price(
        price_used=120500.0,
        quote_basis_g=10.0,
        purity=0.999,
        target_purity=0.999,
        target_basis_g=10.0,
    )
    assert round(p_norm, 2) == 120500.00


def test_hand_fixture_goldguinea():
    """GOLDGUINEA at 96,400 quoted (999 purity, 8g basis) normalizes to 120,500.00."""
    p_norm = normalize_price(
        price_used=96400.0,
        quote_basis_g=8.0,
        purity=0.999,
        target_purity=0.999,
        target_basis_g=10.0,
    )
    # 96400 * (10/8) * 1.0 = 120500.00
    assert round(p_norm, 2) == 120500.00


def test_hand_fixture_goldpetal():
    """GOLDPETAL at 12,050 quoted (999 purity, 1g basis) normalizes to 120,500.00."""
    p_norm = normalize_price(
        price_used=120500 / 10,
        quote_basis_g=1.0,
        purity=0.999,
        target_purity=0.999,
        target_basis_g=10.0,
    )
    assert round(p_norm, 2) == 120500.00


def test_purity_direction_rule_r16():
    """R16 Direction Test: Normalizing a sub-999 contract MUST yield a higher price.

    Lower purity normalizes UP, because 0.999 gold is more concentrated than 0.995 gold.
    """
    assert purity_direction_test(price=120000.0, purity=0.995, quote_basis_g=10.0)
    assert purity_direction_test(price=60000.0, purity=0.916, quote_basis_g=10.0)

    # Direct verification
    p_raw_weight_scaled = 120000.0 * (10.0 / 10.0)
    p_normalized = normalize_price(price_used=120000.0, quote_basis_g=10.0, purity=0.995)
    assert p_normalized > p_raw_weight_scaled


def test_normalize_with_config():
    """Verify normalization using actual contracts.yaml configuration."""
    cfg = load_contracts_config(Path("config/contracts.yaml"))

    p_goldm = normalize_contract_price(120000.0, "GOLDM", cfg)
    assert round(p_goldm, 2) == 120482.41

    p_goldten = normalize_contract_price(120500.0, "GOLDTEN", cfg)
    assert round(p_goldten, 2) == 120500.00

    p_petal = normalize_contract_price(12050.0, "GOLDPETAL", cfg)
    assert round(p_petal, 2) == 120500.00


def test_normalize_validation_guards():
    """Validation checks: negative prices or invalid purity/weights must raise ValueError."""
    with pytest.raises(ValueError, match="price_used cannot be negative"):
        normalize_price(-100.0, 10.0, 0.995)

    with pytest.raises(ValueError, match="quote_basis_g must be strictly positive"):
        normalize_price(100.0, 0.0, 0.995)

    with pytest.raises(ValueError, match="purity must be strictly positive"):
        normalize_price(100.0, 10.0, 0.0)
