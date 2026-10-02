"""Tests for Price Quality Assessment Stage (FR18, Design §6.2)."""

from datetime import date
import pytest

from aurumlens.ingest.adapters.base import CanonicalRecord
from aurumlens.ingest.quality import PriceQualityEvaluator


def make_record(
    close: float = 75000.0,
    settlement: float = None,
    volume: int = 100,
    open_interest: int = 500
) -> CanonicalRecord:
    return CanonicalRecord(
        contract_id="GOLDM_20261105",
        symbol="GOLDM",
        trade_date=date(2026, 10, 1),
        expiry_date=date(2026, 11, 5),
        open=74900.0,
        high=75500.0,
        low=74800.0,
        close=close,
        settlement=settlement,
        volume=volume,
        open_interest=open_interest
    )


def test_ok_price_quality_default_close():
    evaluator = PriceQualityEvaluator(price_source="close", min_volume_for_price=5)
    rec = make_record(close=75000.0, volume=10)
    result = evaluator.evaluate_record(rec)
    assert result.price_quality == "OK"
    assert result.price_used == 75000.0
    assert result.price_source == "close"
    assert result.quality_reason is None


def test_price_source_settlement_selection():
    evaluator = PriceQualityEvaluator(price_source="settlement", min_volume_for_price=5)
    rec = make_record(close=75000.0, settlement=75050.0, volume=10)
    result = evaluator.evaluate_record(rec)
    assert result.price_quality == "OK"
    assert result.price_used == 75050.0
    assert result.price_source == "settlement"


def test_price_source_settlement_fallback_to_close_when_none():
    evaluator = PriceQualityEvaluator(price_source="settlement", min_volume_for_price=5)
    rec = make_record(close=75000.0, settlement=None, volume=10)
    result = evaluator.evaluate_record(rec)
    assert result.price_quality == "OK"
    assert result.price_used == 75000.0
    assert result.price_source == "close"


def test_low_volume_flagged_suspect():
    evaluator = PriceQualityEvaluator(min_volume_for_price=5)
    rec = make_record(close=75000.0, volume=2)
    result = evaluator.evaluate_record(rec)
    assert result.price_quality == "SUSPECT"
    assert "LOW_VOLUME" in (result.quality_reason or "")


def test_close_settlement_divergence_flagged_suspect():
    # Gap threshold = 0.015 (1.5%)
    evaluator = PriceQualityEvaluator(stale_gap_threshold=0.015)
    # 75000 vs 73000 -> 2000 / 73000 = 2.74% > 1.5%
    rec = make_record(close=75000.0, settlement=73000.0, volume=50)
    result = evaluator.evaluate_record(rec)
    assert result.price_quality == "SUSPECT"
    assert "CLOSE_SETTLEMENT_DIVERGENCE" in (result.quality_reason or "")


def test_non_positive_price_flagged_suspect():
    evaluator = PriceQualityEvaluator()
    rec = make_record(close=0.0, volume=50)
    result = evaluator.evaluate_record(rec)
    assert result.price_quality == "SUSPECT"
    assert "NON_POSITIVE_PRICE" in (result.quality_reason or "")


def test_multiple_suspect_reasons_joined():
    evaluator = PriceQualityEvaluator(min_volume_for_price=10, stale_gap_threshold=0.01)
    rec = make_record(close=75000.0, settlement=70000.0, volume=2)
    result = evaluator.evaluate_record(rec)
    assert result.price_quality == "SUSPECT"
    assert "LOW_VOLUME" in result.quality_reason
    assert "CLOSE_SETTLEMENT_DIVERGENCE" in result.quality_reason
