"""Validation and Deduplication Engine for AurumLens Ingest.

Strict Quant Rules:
- Requested date must strictly match returned date.
- Supported symbols only: GOLDM, GOLDTEN, GOLDGUINEA, GOLDPETAL.
- Conflicting duplicates are REJECTED and logged; never silently repaired or overwritten.
- Identical duplicate records are safely deduplicated.
"""

from dataclasses import dataclass, field
from datetime import date
import logging
from typing import Dict, List, Optional, Set, Tuple

from aurumlens.ingest.adapters.base import ALLOW_LISTED_SYMBOLS, CanonicalRecord, SourceAdapter

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Detailed summary of data validation and deduplication results."""
    requested_date: date
    returned_date: Optional[date]
    total_raw_rows: int
    parsed_canonical_records: int
    supported_contract_records: int
    duplicates_removed: int
    conflicting_duplicates: int
    is_valid: bool
    reject_reason: Optional[str] = None
    records: List[CanonicalRecord] = field(default_factory=list)
    symbols_present: Set[str] = field(default_factory=set)


class IngestValidator:
    """Validates raw content, applies adapter parsing, enforces symbol filters, and checks duplicates."""

    def __init__(self, allowed_symbols: Optional[Set[str]] = None) -> None:
        self.allowed_symbols = allowed_symbols or ALLOW_LISTED_SYMBOLS

    def validate_and_deduplicate(
        self,
        content: str,
        requested_date: date,
        adapter: SourceAdapter
    ) -> ValidationReport:
        """Parse raw CSV through adapter and run strict validation and duplicate checks.
        
        Args:
            content: Raw CSV text from Bhavcopy.
            requested_date: Expected trade date.
            adapter: Era-appropriate SourceAdapter.
            
        Returns:
            ValidationReport with validated records or rejection details.
        """
        if not content or not content.strip():
            return ValidationReport(
                requested_date=requested_date,
                returned_date=None,
                total_raw_rows=0,
                parsed_canonical_records=0,
                supported_contract_records=0,
                duplicates_removed=0,
                conflicting_duplicates=0,
                is_valid=False,
                reject_reason="EMPTY_CONTENT"
            )

        # 1. Parse via adapter
        try:
            records = adapter.parse(
                content=content,
                requested_date=requested_date,
                symbols_filter=self.allowed_symbols
            )
        except ValueError as e:
            # Date mismatch or schema failure
            err_msg = str(e)
            if "does not match" in err_msg.lower():
                standardized_reason = f"DATE_MISMATCH: {err_msg}"
            elif "missing mandatory columns" in err_msg.lower():
                standardized_reason = f"SCHEMA_ERROR: {err_msg}"
            else:
                standardized_reason = err_msg

            logger.warning(f"Validation failed for {requested_date}: {standardized_reason}")
            return ValidationReport(
                requested_date=requested_date,
                returned_date=None,
                total_raw_rows=len(content.strip().splitlines()) - 1,
                parsed_canonical_records=0,
                supported_contract_records=0,
                duplicates_removed=0,
                conflicting_duplicates=0,
                is_valid=False,
                reject_reason=standardized_reason
            )

        total_parsed = len(records)
        if total_parsed == 0:
            return ValidationReport(
                requested_date=requested_date,
                returned_date=requested_date,
                total_raw_rows=len(content.strip().splitlines()) - 1,
                parsed_canonical_records=0,
                supported_contract_records=0,
                duplicates_removed=0,
                conflicting_duplicates=0,
                is_valid=True,
                records=[]
            )

        # 2. Check returned trade date vs requested date on all parsed records
        for rec in records:
            if rec.trade_date != requested_date:
                reject_msg = f"DATE_MISMATCH: record trade_date {rec.trade_date} != requested {requested_date}"
                logger.error(reject_msg)
                return ValidationReport(
                    requested_date=requested_date,
                    returned_date=rec.trade_date,
                    total_raw_rows=len(content.strip().splitlines()) - 1,
                    parsed_canonical_records=total_parsed,
                    supported_contract_records=0,
                    duplicates_removed=0,
                    conflicting_duplicates=0,
                    is_valid=False,
                    reject_reason=reject_msg
                )

        # 3. Deduplication and Conflicting Duplicate Detection
        # Key: (contract_id, trade_date)
        unique_records: Dict[Tuple[str, date], CanonicalRecord] = {}
        duplicates_removed = 0
        conflicting_duplicates = 0
        conflicting_details = []

        for rec in records:
            key = (rec.contract_id, rec.trade_date)
            if key in unique_records:
                existing = unique_records[key]
                # Compare critical quantitative attributes: open, high, low, close, volume, open_interest
                is_identical = (
                    abs(existing.close - rec.close) < 1e-6 and
                    abs(existing.open - rec.open) < 1e-6 and
                    abs(existing.high - rec.high) < 1e-6 and
                    abs(existing.low - rec.low) < 1e-6 and
                    existing.volume == rec.volume and
                    existing.open_interest == rec.open_interest
                )
                if is_identical:
                    duplicates_removed += 1
                else:
                    conflicting_duplicates += 1
                    conflicting_details.append(
                        f"Conflict on {rec.contract_id}: existing close={existing.close}, new close={rec.close}"
                    )
            else:
                unique_records[key] = rec

        if conflicting_duplicates > 0:
            reject_msg = f"CONFLICTING_DUPLICATES_DETECTED: {'; '.join(conflicting_details)}"
            logger.error(reject_msg)
            return ValidationReport(
                requested_date=requested_date,
                returned_date=requested_date,
                total_raw_rows=len(content.strip().splitlines()) - 1,
                parsed_canonical_records=total_parsed,
                supported_contract_records=0,
                duplicates_removed=duplicates_removed,
                conflicting_duplicates=conflicting_duplicates,
                is_valid=False,
                reject_reason=reject_msg
            )

        final_records = list(unique_records.values())
        symbols = {r.symbol for r in final_records}

        return ValidationReport(
            requested_date=requested_date,
            returned_date=requested_date,
            total_raw_rows=len(content.strip().splitlines()) - 1,
            parsed_canonical_records=total_parsed,
            supported_contract_records=len(final_records),
            duplicates_removed=duplicates_removed,
            conflicting_duplicates=0,
            is_valid=True,
            records=final_records,
            symbols_present=symbols
        )
