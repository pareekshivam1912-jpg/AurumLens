"""Tests for Contract Price Converter Tool (FR22)."""

from pathlib import Path
import pytest

from aurumlens.config.loader import load_contracts_config
from aurumlens.tools.converter import convert_contract_price, denormalize_price


@pytest.fixture
def contracts_config():
    return load_contracts_config(Path("config/contracts.yaml"))


def test_denormalize_roundtrip():
    """Denormalizing a normalized price returns the original quoted price."""
    quoted = 120000.0
    qb = 10.0
    purity = 0.995

    # 120,000 * (10/10) * (0.999/0.995) = 120482.41206...
    norm = quoted * (0.999 / purity)
    denorm = denormalize_price(norm, qb, purity)
    assert round(denorm, 2) == 120000.00


def test_convert_goldten_fixture(contracts_config):
    """Converting GOLDTEN at 120,500 reproduces hand equivalents."""
    res = convert_contract_price(
        source_symbol="GOLDTEN",
        quoted_price=120500.0,
        contracts_config=contracts_config,
    )

    assert res.normalized_price_10g_999 == 120500.00
    assert res.source_symbol == "GOLDTEN"
    assert "Analytics only" in res.disclaimer

    eq = res.equivalents
    assert "GOLDM" in eq
    assert "GOLDTEN" in eq
    assert "GOLDPETAL" in eq

    # GOLDTEN equivalent is itself
    assert eq["GOLDTEN"].equivalent_quoted_price == 120500.00

    # GOLDPETAL (1g basis, 999 purity) -> 120,500 / 10 = 12,050.00
    assert eq["GOLDPETAL"].equivalent_quoted_price == 12050.00

    # GOLDM (10g basis, 0.995 purity) -> 120,500 * (0.995 / 0.999) = 120,017.52
    assert eq["GOLDM"].equivalent_quoted_price == 120017.52


def test_convert_invalid_symbol_raises(contracts_config):
    """Invalid symbol raises KeyError."""
    with pytest.raises(KeyError, match="not found in contracts config"):
        convert_contract_price("BITCOIN", 100000.0, contracts_config)
