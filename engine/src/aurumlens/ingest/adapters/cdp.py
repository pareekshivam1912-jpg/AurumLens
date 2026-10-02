"""CDP SourceAdapter for MCX Bhavcopy archives post October 16, 2023 (TCS CDP platform)."""

import csv
from datetime import date
import io
from typing import List, Optional

from aurumlens.ingest.adapters.base import (
    ALLOW_LISTED_SYMBOLS,
    CanonicalRecord,
    SourceAdapter,
)
from aurumlens.ingest.adapters.legacy import parse_date


class CDPAdapter(SourceAdapter):
    """Adapter for post-October 2023 TCS CDP Bhavcopy format."""

    @property
    def era_name(self) -> str:
        return "cdp"

    def can_parse(self, content_sample: str) -> bool:
        sample_lower = content_sample[:1000].lower()
        has_symbol = "symbol" in sample_lower or "commodity" in sample_lower
        has_expiry = "expiry" in sample_lower
        return has_symbol and has_expiry

    def parse(
        self,
        content: str,
        requested_date: date,
        symbols_filter: Optional[set[str]] = None
    ) -> List[CanonicalRecord]:
        symbols = symbols_filter if symbols_filter is not None else ALLOW_LISTED_SYMBOLS
        cleaned_content = content.strip()

        # Determine delimiter (comma or pipe)
        sample_line = cleaned_content.splitlines()[0] if cleaned_content else ""
        delimiter = "|" if "|" in sample_line else ","

        reader = csv.DictReader(io.StringIO(cleaned_content), delimiter=delimiter)

        if not reader.fieldnames:
            raise ValueError("Empty or malformed CSV content: no headers found.")

        field_map = {name.strip().lower(): name for name in reader.fieldnames}

        # Candidate names in CDP format
        date_col = next((field_map[k] for k in ["date", "trade date", "bizdt", "tradedate"] if k in field_map), None)
        sym_col = next((field_map[k] for k in ["symbol", "commodity", "tradgsymb", "symbol name"] if k in field_map), None)
        exp_col = next((field_map[k] for k in ["expiry date", "expirydate", "xprydt", "expiry_dt"] if k in field_map), None)
        inst_col = next((field_map[k] for k in ["instrument name", "instrument", "instname", "inst_type"] if k in field_map), None)
        open_col = next((field_map[k] for k in ["open", "open price", "opnpric"] if k in field_map), None)
        high_col = next((field_map[k] for k in ["high", "high price", "hghpric"] if k in field_map), None)
        low_col = next((field_map[k] for k in ["low", "low price", "lwpric"] if k in field_map), None)
        close_col = next((field_map[k] for k in ["close", "closing price", "clspric"] if k in field_map), None)
        vol_col = next((field_map[k] for k in ["volume(lots)", "volume", "ttltradgvol", "vol_contr"] if k in field_map), None)
        oi_col = next((field_map[k] for k in ["open interest(lots)", "open interest", "opnintrst", "open_int", "oi"] if k in field_map), None)
        settle_col = next((field_map[k] for k in ["settlement price", "settlement", "sttlmpric", "settle_pr"] if k in field_map), None)

        mandatory = [("date", date_col), ("symbol", sym_col), ("expiry", exp_col), ("open", open_col),
                     ("high", high_col), ("low", low_col), ("close", close_col), ("volume", vol_col), ("oi", oi_col)]
        missing = [name for name, val in mandatory if val is None]
        if missing:
            raise ValueError(f"CDPAdapter missing mandatory columns: {missing}. Available: {reader.fieldnames}")

        records: List[CanonicalRecord] = []
        verified_date_matched = False

        for row_idx, row in enumerate(reader, start=2):
            raw_sym = row.get(sym_col, "")
            symbol = raw_sym.strip().upper()
            if symbol not in symbols:
                continue

            inst = row.get(inst_col, "FUTCOM").strip().upper() if inst_col else "FUTCOM"
            # Futures contracts only
            if inst not in ("FUTCOM", "FUTIDX", "FUTURE", ""):
                continue

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

            try:
                open_p = float(row.get(open_col) or 0.0)
                high_p = float(row.get(high_col) or 0.0)
                low_p = float(row.get(low_col) or 0.0)
                close_p = float(row.get(close_col) or 0.0)
                vol = int(float(row.get(vol_col) or 0))
                oi = int(float(row.get(oi_col) or 0))
                settle_p = float(row.get(settle_col)) if (settle_col and row.get(settle_col)) else None
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid numeric data in CDP row {row_idx} ({symbol}): {e}")

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
