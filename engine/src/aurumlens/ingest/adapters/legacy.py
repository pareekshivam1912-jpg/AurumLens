"""Legacy SourceAdapter for MCX Bhavcopy archives prior to October 16, 2023."""

import csv
from datetime import date, datetime
import io
from typing import List, Optional

from aurumlens.ingest.adapters.base import (
    ALLOW_LISTED_SYMBOLS,
    CanonicalRecord,
    SourceAdapter,
)


def parse_date(date_str: str) -> date:
    """Parse various MCX date representations explicitly without locale ambiguity."""
    date_str = date_str.strip()
    formats = [
        "%d %b %Y",     # 15 Sep 2023
        "%d-%b-%Y",     # 15-SEP-2023, 15-Sep-2023
        "%d%b%Y",       # 29SEP2023
        "%m/%d/%Y",     # 09/15/2023
        "%d/%m/%Y",     # 15/09/2023
        "%Y-%m-%d",     # 2023-09-15
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date string: '{date_str}'")


class LegacyAdapter(SourceAdapter):
    """Adapter for pre-October 2023 Bhavcopy format."""

    @property
    def era_name(self) -> str:
        return "legacy"

    def can_parse(self, content_sample: str) -> bool:
        sample_lower = content_sample[:1000].lower()
        has_symbol = "symbol" in sample_lower
        has_expiry = "expiry" in sample_lower
        has_date = "date" in sample_lower
        return has_symbol and has_expiry and has_date

    def parse(
        self,
        content: str,
        requested_date: date,
        symbols_filter: Optional[set[str]] = None
    ) -> List[CanonicalRecord]:
        symbols = symbols_filter if symbols_filter is not None else ALLOW_LISTED_SYMBOLS
        reader = csv.DictReader(io.StringIO(content.strip()))

        if not reader.fieldnames:
            raise ValueError("Empty or malformed CSV content: no headers found.")

        # Normalize column header lookup (case-insensitive and stripped)
        field_map = {name.strip().lower(): name for name in reader.fieldnames}

        # Find mandatory column mappings
        date_col = next((field_map[k] for k in ["date", "trade date", "tradedate"] if k in field_map), None)
        sym_col = next((field_map[k] for k in ["symbol", "symbol name", "commodity"] if k in field_map), None)
        exp_col = next((field_map[k] for k in ["expiry date", "expirydate", "expiry_dt"] if k in field_map), None)
        inst_col = next((field_map[k] for k in ["instrument name", "instrument", "inst_type"] if k in field_map), None)
        open_col = next((field_map[k] for k in ["open", "open price"] if k in field_map), None)
        high_col = next((field_map[k] for k in ["high", "high price"] if k in field_map), None)
        low_col = next((field_map[k] for k in ["low", "low price"] if k in field_map), None)
        close_col = next((field_map[k] for k in ["close", "closing price", "close price"] if k in field_map), None)
        vol_col = next((field_map[k] for k in ["volume(lots)", "volume", "vol_contr"] if k in field_map), None)
        oi_col = next((field_map[k] for k in ["open interest(lots)", "open interest", "open_int", "oi"] if k in field_map), None)
        settle_col = next((field_map[k] for k in ["settlement price", "settlement", "settle_pr"] if k in field_map), None)

        mandatory = [("date", date_col), ("symbol", sym_col), ("expiry", exp_col), ("open", open_col),
                     ("high", high_col), ("low", low_col), ("close", close_col), ("volume", vol_col), ("oi", oi_col)]
        missing = [name for name, val in mandatory if val is None]
        if missing:
            raise ValueError(f"LegacyAdapter missing mandatory columns: {missing}. Available: {reader.fieldnames}")

        records: List[CanonicalRecord] = []
        verified_date_matched = False

        for row_idx, row in enumerate(reader, start=2):
            raw_sym = row.get(sym_col, "")
            symbol = raw_sym.strip().upper()
            if symbol not in symbols:
                continue

            inst = row.get(inst_col, "FUTCOM").strip().upper() if inst_col else "FUTCOM"
            # Filter futures only
            if inst not in ("FUTCOM", "FUTIDX", "FUTURE", ""):
                continue

            # Validate date match
            row_date_raw = row.get(date_col, "")
            row_trade_date = parse_date(row_date_raw)
            if not verified_date_matched:
                if row_trade_date != requested_date:
                    raise ValueError(
                        f"Requested date {requested_date} does not match Bhavcopy returned date {row_trade_date} (row {row_idx})"
                    )
                verified_date_matched = True

            expiry_raw = row.get(exp_col, "")
            expiry_date = parse_date(expiry_raw)

            contract_id = f"{symbol}_{expiry_date.strftime('%Y%m%d')}"

            # Numerical values with safety fallbacks
            try:
                open_p = float(row.get(open_col) or 0.0)
                high_p = float(row.get(high_col) or 0.0)
                low_p = float(row.get(low_col) or 0.0)
                close_p = float(row.get(close_col) or 0.0)
                vol = int(float(row.get(vol_col) or 0))
                oi = int(float(row.get(oi_col) or 0))
                settle_p = float(row.get(settle_col)) if (settle_col and row.get(settle_col)) else None
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid numeric data in row {row_idx} ({symbol}): {e}")

            records.append(
                CanonicalRecord(
                    contract_id=contract_id,
                    symbol=symbol,
                    trade_date=row_trade_date,
                    expiry_date=expiry_date,
                    open=open_p,
                    high=high_p,
                    low=low_p,
                    close=close_p,
                    settlement=settle_p,
                    volume=vol,
                    open_interest=oi,
                    instrument_name=inst,
                    raw_symbol=raw_sym,
                )
            )

        return records
