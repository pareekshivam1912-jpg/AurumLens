"""Tests for AurumLens configuration models, facts register, and version hashing."""

from pathlib import Path
import pytest

from aurumlens.config import (
    FactStatus,
    SpecMode,
    compute_config_version,
    load_all_configs,
)

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def test_config_files_exist():
    assert (CONFIG_DIR / "contracts.yaml").exists()
    assert (CONFIG_DIR / "costs.yaml").exists()
    assert (CONFIG_DIR / "strategy.yaml").exists()
    assert (CONFIG_DIR / "events.yaml").exists()


def test_config_version_hash():
    v1 = compute_config_version(CONFIG_DIR)
    v2 = compute_config_version(CONFIG_DIR)
    assert len(v1) == 12
    assert v1 == v2
    assert all(c in "0123456789abcdef" for c in v1)


def test_contracts_config_and_disputed_guinea():
    configs = load_all_configs(CONFIG_DIR)
    contracts = configs.contracts.contracts

    assert "GOLDM" in contracts
    assert "GOLDTEN" in contracts
    assert "GOLDGUINEA" in contracts
    assert "GOLDPETAL" in contracts

    # Verify GOLDGUINEA purity is strictly DISPUTED with null value
    guinea = contracts["GOLDGUINEA"]
    assert guinea.purity.status == FactStatus.DISPUTED
    assert guinea.purity.value is None
    assert guinea.purity.candidates == [0.995, 0.999]

    # Verify target basis
    assert configs.contracts.target_basis.grams == 10.0
    assert configs.contracts.target_basis.purity == 0.999

    # Verify trading units
    assert contracts["GOLDM"].trading_unit_g.value == 100.0
    assert contracts["GOLDTEN"].trading_unit_g.value == 10.0
    assert contracts["GOLDGUINEA"].trading_unit_g.value == 8.0
    assert contracts["GOLDPETAL"].trading_unit_g.value == 1.0


def test_costs_config():
    configs = load_all_configs(CONFIG_DIR)
    costs = configs.costs

    assert costs.brokerage.status == FactStatus.SECONDARY
    assert costs.ctt_sell.rate == 0.0001
    assert costs.exchange.rate == 0.000021
    assert costs.sebi.rate == 0.000001
    assert costs.stamp_buy.rate == 0.00002
    assert costs.gst.rate == 0.18
    assert costs.safety_buffer_inr_per_10g.status == FactStatus.TO_VALIDATE
    assert costs.safety_buffer_inr_per_10g.value is None


def test_strategy_and_events_config():
    configs = load_all_configs(CONFIG_DIR)
    strategy = configs.strategy
    events = configs.events

    assert strategy.scoring.lookback_window == 60
    assert strategy.scoring.entry_z == 2.0
    assert strategy.scoring.exit_z == 0.5
    assert strategy.pairing.max_expiry_gap_days == 35
    assert strategy.expiry.unsafe_expiry_window_days == 5

    assert len(events.events) >= 4
    for ev in events.events:
        assert ev.event_date is not None
        assert ev.label is not None
