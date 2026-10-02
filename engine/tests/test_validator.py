"""Tests for IngestValidator: date matching, symbol allow-listing, and duplicate prevention."""

from datetime import date
import pytest

from aurumlens.ingest.adapters import CDPAdapter, LegacyAdapter
from aurumlens.ingest.adapters.base import CanonicalRecord
from aurumlens.ingest.validator import IngestValidator


@pytest.fixture
def validator():
    return IngestValidator()


def test_date_mismatch_rejected(validator):
    """A file whose trade dates do not match requested_date must be rejected."""
    adapter = CDPAdapter()
    csv_content = """Date,Instrument Name,Symbol,Expiry Date,Option Type,Strike Price,Open,High,Low,Close,Previous Close,Volume(Lots),Volume(In 000's),Value(Lacs),Open Interest(Lots)
01 Oct 2026,FUTCOM,GOLDM      ,05NOV2026,-,0.0,75000.0,75500.0,74900.0,75200.0,75100.0,100,10.0,752.0,500
"""
    wrong_requested_date = date(2026, 10, 2)
    report = validator.validate_and_deduplicate(csv_content, wrong_requested_date, adapter)
    assert not report.is_valid
    assert "DATE_MISMATCH" in (report.reject_reason or "")
    assert report.supported_contract_records == 0


def test_holiday_or_empty_content(validator):
    """Empty or whitespace-only content must produce an invalid report with EMPTY_CONTENT."""
    adapter = CDPAdapter()
    report = validator.validate_and_deduplicate("   \n  ", date(2026, 10, 1), adapter)
    assert not report.is_valid
    assert report.reject_reason == "EMPTY_CONTENT"


def test_malformed_schema_rejected(validator):
    """CSV with missing required columns must be rejected."""
    adapter = CDPAdapter()
    bad_csv = """RandomCol1,RandomCol2,RandomCol3
val1,val2,val3
"""
    report = validator.validate_and_deduplicate(bad_csv, date(2026, 10, 1), adapter)
    assert not report.is_valid
    assert "SCHEMA_ERROR" in (report.reject_reason or "")


def test_supported_symbol_filter_and_padding_strip(validator):
    """Only allow-listed contracts are kept; trailing whitespace is stripped."""
    adapter = CDPAdapter()
    csv_content = """Date,Instrument Name,Symbol,Expiry Date,Option Type,Strike Price,Open,High,Low,Close,Previous Close,Volume(Lots),Volume(In 000's),Value(Lacs),Open Interest(Lots)
01 Oct 2026,FUTCOM,GOLDM      ,05NOV2026,-,0.0,75000.0,75500.0,74900.0,75200.0,75100.0,100,10.0,752.0,500
01 Oct 2026,FUTCOM,SILVER     ,05DEC2026,-,0.0,90000.0,91000.0,89500.0,90500.0,90000.0,50,5.0,450.0,200
01 Oct 2026,FUTCOM,CRUDEOIL   ,19OCT2026,-,0.0,6000.0,6100.0,5950.0,6050.0,6000.0,500,50.0,3000.0,1500
01 Oct 2026,FUTCOM,GOLDPETAL  ,31OCT2026,-,0.0,7500.0,7550.0,7490.0,7520.0,7510.0,20,1.0,75.2,100
"""
    report = validator.validate_and_deduplicate(csv_content, date(2026, 10, 1), adapter)
    assert report.is_valid
    assert report.supported_contract_records == 2
    assert report.symbols_present == {"GOLDM", "GOLDPETAL"}
    symbols = [r.symbol for r in report.records]
    assert "SILVER" not in symbols
    assert "CRUDEOIL" not in symbols


def test_duplicate_prevention_identical_deduplicated(validator):
    """Identical duplicate rows for the same contract + trade_date are safely deduplicated."""
    adapter = CDPAdapter()
    csv_content = """Date,Instrument Name,Symbol,Expiry Date,Option Type,Strike Price,Open,High,Low,Close,Previous Close,Volume(Lots),Volume(In 000's),Value(Lacs),Open Interest(Lots)
01 Oct 2026,FUTCOM,GOLDM      ,05NOV2026,-,0.0,75000.0,75500.0,74900.0,75200.0,75100.0,100,10.0,752.0,500
01 Oct 2026,FUTCOM,GOLDM      ,05NOV2026,-,0.0,75000.0,75500.0,74900.0,75200.0,75100.0,100,10.0,752.0,500
"""
    report = validator.validate_and_deduplicate(csv_content, date(2026, 10, 1), adapter)
    assert report.is_valid
    assert report.supported_contract_records == 1
    assert report.duplicates_removed == 1
    assert report.conflicting_duplicates == 0


def test_conflicting_duplicate_rejected(validator):
    """Conflicting duplicate rows (different price for same contract + date) MUST be rejected."""
    adapter = CDPAdapter()
    csv_content = """Date,Instrument Name,Symbol,Expiry Date,Option Type,Strike Price,Open,High,Low,Close,Previous Close,Volume(Lots),Volume(In 000's),Value(Lacs),Open Interest(Lots)
01 Oct 2026,FUTCOM,GOLDM      ,05NOV2026,-,0.0,75000.0,75500.0,74900.0,75200.0,75100.0,100,10.0,752.0,500
01 Oct 2026,FUTCOM,GOLDM      ,05NOV2026,-,0.0,75000.0,75500.0,74900.0,75999.0,75100.0,100,10.0,752.0,500
"""
    report = validator.validate_and_deduplicate(csv_content, date(2026, 10, 1), adapter)
    assert not report.is_valid
    assert report.conflicting_duplicates == 1
    assert "CONFLICTING_DUPLICATES_DETECTED" in (report.reject_reason or "")
