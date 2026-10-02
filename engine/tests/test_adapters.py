"""Tests for SourceAdapters using real Bhavcopy sample files from both eras."""

from datetime import date
from pathlib import Path
import pytest

from aurumlens.ingest import (
    ALLOW_LISTED_SYMBOLS,
    CDPAdapter,
    LegacyAdapter,
    get_adapter_for_date,
    CDP_CUTOVER_DATE,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "fixtures" / "real_samples"


def test_adapter_selection_by_date():
    pre_cdp = date(2023, 9, 15)
    post_cdp = date(2023, 10, 16)
    future_date = date(2026, 10, 1)

    assert isinstance(get_adapter_for_date(pre_cdp), LegacyAdapter)
    assert isinstance(get_adapter_for_date(post_cdp), CDPAdapter)
    assert isinstance(get_adapter_for_date(future_date), CDPAdapter)


def test_parse_real_legacy_sample():
    sample_path = FIXTURES_DIR / "bhavcopy_20230915_legacy.csv"
    assert sample_path.exists(), f"Missing real legacy sample file at {sample_path}"

    with open(sample_path, "r", encoding="utf-8") as f:
        content = f.read()

    adapter = LegacyAdapter()
    assert adapter.can_parse(content)

    requested_date = date(2023, 9, 15)
    records = adapter.parse(content, requested_date=requested_date)

    assert len(records) > 0
    symbols_found = {r.symbol for r in records}
    # GOLDM, GOLDGUINEA, GOLDPETAL existed in 2023; GOLDTEN was launched in 2025
    assert "GOLDM" in symbols_found
    assert "GOLDGUINEA" in symbols_found
    assert "GOLDPETAL" in symbols_found
    assert "GOLDTEN" not in symbols_found

    # Check contract IDs and values
    for r in records:
        assert r.trade_date == requested_date
        assert r.symbol in ALLOW_LISTED_SYMBOLS
        assert r.contract_id.startswith(r.symbol + "_")
        assert r.close > 0.0
        assert r.volume >= 0
        assert r.open_interest >= 0


def test_legacy_date_mismatch_rejected():
    sample_path = FIXTURES_DIR / "bhavcopy_20230915_legacy.csv"
    with open(sample_path, "r", encoding="utf-8") as f:
        content = f.read()

    adapter = LegacyAdapter()
    wrong_date = date(2023, 9, 16)
    with pytest.raises(ValueError, match="Requested date .* does not match"):
        adapter.parse(content, requested_date=wrong_date)


def test_parse_real_cdp_sample():
    sample_path = FIXTURES_DIR / "bhavcopy_20261001_cdp.csv"
    assert sample_path.exists(), f"Missing real CDP sample file at {sample_path}"

    with open(sample_path, "r", encoding="utf-8") as f:
        content = f.read()

    adapter = CDPAdapter()
    assert adapter.can_parse(content)

    requested_date = date(2026, 10, 1)
    records = adapter.parse(content, requested_date=requested_date)

    assert len(records) == 24
    symbols_found = {r.symbol for r in records}
    # In 2026, all four contracts exist
    assert symbols_found == {"GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"}

    # Spot check GOLDTEN
    goldten_records = [r for r in records if r.symbol == "GOLDTEN"]
    assert len(goldten_records) >= 5
    oct_goldten = next(r for r in goldten_records if r.expiry_date == date(2026, 10, 30))
    assert oct_goldten.close == 149436.0
    assert oct_goldten.volume == 22286
    assert oct_goldten.open_interest == 29866
    assert oct_goldten.contract_id == "GOLDTEN_20261030"


def test_cdp_date_mismatch_rejected():
    sample_path = FIXTURES_DIR / "bhavcopy_20261001_cdp.csv"
    with open(sample_path, "r", encoding="utf-8") as f:
        content = f.read()

    adapter = CDPAdapter()
    wrong_date = date(2026, 10, 2)
    with pytest.raises(ValueError, match="Requested date .* does not match"):
        adapter.parse(content, requested_date=wrong_date)
