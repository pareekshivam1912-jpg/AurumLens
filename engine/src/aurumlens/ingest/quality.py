"""Price Quality Assessment Stage (FR18, Design §6.2).

Quant Invariants:
- Selects `price_used` based on configured `price_source` ('close' or 'settlement').
- Flags `SUSPECT` if:
  1. volume < min_volume_for_price (default 5 lots)
  2. |close - settlement| / settlement > stale_gap_threshold (default 1.5%)
  3. price_used <= 0
- Stores explicit, human-readable reason codes in `quality_reason`.
"""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from aurumlens.config.models import StrategyConfig
from aurumlens.ingest.adapters.base import CanonicalRecord


@dataclass(frozen=True)
class QualityAssessedRecord:
    """Canonical observation augmented with price-quality classification."""
    contract_id: str
    symbol: str
    trade_date: date
    expiry_date: date
    open: float
    high: float
    low: float
    close: float
    settlement: Optional[float]
    volume: int
    open_interest: int
    price_used: float
    price_source: str  # 'close' or 'settlement'
    price_quality: str  # 'OK' or 'SUSPECT'
    quality_reason: Optional[str] = None
    normalized_price: Optional[float] = None


class PriceQualityEvaluator:
    """Evaluates contract prices and assigns quality classification per Design §6.2."""

    def __init__(
        self,
        price_source: str = "close",
        min_volume_for_price: int = 5,
        stale_gap_threshold: float = 0.015
    ) -> None:
        if price_source not in ("close", "settlement"):
            raise ValueError(f"Invalid price_source: {price_source}. Expected 'close' or 'settlement'")
        self.price_source = price_source
        self.min_volume_for_price = min_volume_for_price
        self.stale_gap_threshold = stale_gap_threshold

    @classmethod
    def from_strategy_config(cls, config: StrategyConfig) -> "PriceQualityEvaluator":
        """Instantiate evaluator directly from versioned StrategyConfig."""
        pq = config.price_quality
        return cls(
            price_source=pq.price_source,
            min_volume_for_price=pq.min_volume_for_price,
            stale_gap_threshold=pq.stale_gap_threshold
        )

    def evaluate_record(self, record: CanonicalRecord) -> QualityAssessedRecord:
        """Evaluate a single CanonicalRecord and return a QualityAssessedRecord."""
        # Determine price_used
        if self.price_source == "settlement" and record.settlement is not None and record.settlement > 0:
            price_used = record.settlement
            actual_source = "settlement"
        else:
            price_used = record.close
            actual_source = "close"

        reasons: List[str] = []

        # 1. Non-positive price
        if price_used <= 0:
            reasons.append("NON_POSITIVE_PRICE")

        # 2. Volume below minimum
        if record.volume < self.min_volume_for_price:
            reasons.append(f"LOW_VOLUME(volume={record.volume}<min={self.min_volume_for_price})")

        # 3. Close vs settlement divergence
        if record.settlement is not None and record.settlement > 0:
            gap = abs(record.close - record.settlement) / record.settlement
            if gap > self.stale_gap_threshold:
                pct = round(gap * 100, 2)
                thresh_pct = round(self.stale_gap_threshold * 100, 2)
                reasons.append(f"CLOSE_SETTLEMENT_DIVERGENCE({pct}%>{thresh_pct}%)")

        if reasons:
            price_quality = "SUSPECT"
            quality_reason = "; ".join(reasons)
        else:
            price_quality = "OK"
            quality_reason = None

        return QualityAssessedRecord(
            contract_id=record.contract_id,
            symbol=record.symbol,
            trade_date=record.trade_date,
            expiry_date=record.expiry_date,
            open=record.open,
            high=record.high,
            low=record.low,
            close=record.close,
            settlement=record.settlement,
            volume=record.volume,
            open_interest=record.open_interest,
            price_used=price_used,
            price_source=actual_source,
            price_quality=price_quality,
            quality_reason=quality_reason,
            normalized_price=None  # Computed in Phase 2
        )

    def evaluate_batch(self, records: List[CanonicalRecord]) -> List[QualityAssessedRecord]:
        """Evaluate a collection of CanonicalRecords."""
        return [self.evaluate_record(r) for r in records]
