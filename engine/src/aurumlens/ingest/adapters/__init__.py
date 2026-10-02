from datetime import date
from typing import Optional

from aurumlens.ingest.adapters.base import (
    ALLOW_LISTED_SYMBOLS,
    CanonicalRecord,
    SourceAdapter,
)
from aurumlens.ingest.adapters.legacy import LegacyAdapter
from aurumlens.ingest.adapters.cdp import CDPAdapter

# MCX CDP platform cutover trade date
CDP_CUTOVER_DATE = date(2023, 10, 16)


def get_adapter_for_date(trade_date: date) -> SourceAdapter:
    """Select appropriate format adapter based on historical platform era."""
    if trade_date < CDP_CUTOVER_DATE:
        return LegacyAdapter()
    return CDPAdapter()


__all__ = [
    "ALLOW_LISTED_SYMBOLS",
    "CanonicalRecord",
    "SourceAdapter",
    "LegacyAdapter",
    "CDPAdapter",
    "CDP_CUTOVER_DATE",
    "get_adapter_for_date",
]
