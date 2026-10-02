"""DuckDB Repository Layer for local historical data engine.

Provides fast, typed analytical storage, unique constraint enforcement, and query helpers.
"""

from datetime import date, datetime
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import duckdb

from aurumlens.db.schema import ALL_DDL

if TYPE_CHECKING:
    from aurumlens.ingest.quality import QualityAssessedRecord

logger = logging.getLogger(__name__)


class DuckDBRepository:
    """Manages DuckDB connection, tables, and CRUD operations for AurumLens."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = str(db_path) if db_path else ":memory:"
        if db_path and db_path != Path(":memory:"):
            db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(self.db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        """Create all tables and sequences if they do not exist."""
        for ddl in ALL_DDL:
            self.conn.execute(ddl)

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()

    def insert_source_file(
        self,
        requested_date: date,
        adapter: str,
        sha256: str,
        storage_path: str,
        status: str,
        returned_date: Optional[date] = None,
        reject_reason: Optional[str] = None
    ) -> int:
        """Insert a source file record and return its generated file_id."""
        # Check if sha256 already exists
        existing = self.conn.execute(
            "SELECT file_id FROM source_file WHERE sha256 = ?", [sha256]
        ).fetchone()
        if existing:
            return existing[0]

        query = """
        INSERT INTO source_file (
            requested_date, returned_date, adapter, sha256, storage_path, status, reject_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        RETURNING file_id
        """
        result = self.conn.execute(
            query,
            [requested_date, returned_date, adapter, sha256, storage_path, status, reject_reason]
        ).fetchone()
        return result[0]

    def upsert_contract(
        self,
        contract_id: str,
        symbol: str,
        expiry_date: date,
        trade_date: date
    ) -> None:
        """Upsert a contract, maintaining first_seen and last_seen trade dates."""
        existing = self.conn.execute(
            "SELECT first_seen, last_seen FROM contract WHERE contract_id = ?",
            [contract_id]
        ).fetchone()

        if existing:
            first_seen, last_seen = existing
            new_first = min(first_seen, trade_date) if first_seen else trade_date
            new_last = max(last_seen, trade_date) if last_seen else trade_date
            self.conn.execute(
                """
                UPDATE contract 
                SET first_seen = ?, last_seen = ? 
                WHERE contract_id = ?
                """,
                [new_first, new_last, contract_id]
            )
        else:
            self.conn.execute(
                """
                INSERT INTO contract (contract_id, symbol, expiry_date, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?)
                """,
                [contract_id, symbol, expiry_date, trade_date, trade_date]
            )

    def insert_daily_prices(
        self,
        records: List[QualityAssessedRecord],
        file_id: int,
        dataset_version: str
    ) -> int:
        """Insert or ignore/update a batch of price-quality assessed records.
        
        Returns the number of rows inserted.
        """
        if not records:
            return 0

        # Enforce uniqueness on (contract_id, trade_date)
        rows_to_insert = []
        for r in records:
            # Check for existing record
            existing = self.conn.execute(
                "SELECT 1 FROM daily_price WHERE contract_id = ? AND trade_date = ?",
                [r.contract_id, r.trade_date]
            ).fetchone()

            if not existing:
                rows_to_insert.append((
                    r.contract_id,
                    r.trade_date,
                    r.open,
                    r.high,
                    r.low,
                    r.close,
                    r.settlement,
                    r.volume,
                    r.open_interest,
                    r.price_used,
                    r.price_source,
                    r.price_quality,
                    r.quality_reason,
                    r.normalized_price,
                    file_id,
                    dataset_version
                ))

        if rows_to_insert:
            self.conn.executemany(
                """
                INSERT INTO daily_price (
                    contract_id, trade_date, open, high, low, close, settlement,
                    volume, open_interest, price_used, price_source, price_quality,
                    quality_reason, normalized_price, file_id, dataset_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows_to_insert
            )

        return len(rows_to_insert)

    def check_duplicates(self) -> List[Tuple[str, date, int]]:
        """Verify strict constraint: return any (contract_id, trade_date) with count > 1."""
        return self.conn.execute(
            """
            SELECT contract_id, trade_date, count(*) as cnt 
            FROM daily_price 
            GROUP BY contract_id, trade_date 
            HAVING count(*) > 1
            """
        ).fetchall()

    def get_summary_stats(self) -> Dict[str, Any]:
        """Compute comprehensive ingestion summary statistics."""
        # 1. Total rows and symbol counts
        symbol_counts = self.conn.execute(
            """
            SELECT c.symbol, count(dp.trade_date) as cnt
            FROM daily_price dp
            JOIN contract c ON dp.contract_id = c.contract_id
            GROUP BY c.symbol
            ORDER BY c.symbol
            """
        ).fetchall()

        # 2. Date ranges
        date_range = self.conn.execute(
            """
            SELECT min(trade_date), max(trade_date), count(DISTINCT trade_date), count(*)
            FROM daily_price
            """
        ).fetchone()

        # 3. Source files
        source_stats = self.conn.execute(
            """
            SELECT 
                count(*) as total_files,
                sum(CASE WHEN status = 'OK' THEN 1 ELSE 0 END) as ok_files,
                sum(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) as rejected_files
            FROM source_file
            """
        ).fetchone()

        # 4. Suspect prices count
        suspect_stats = self.conn.execute(
            """
            SELECT count(*) 
            FROM daily_price 
            WHERE price_quality = 'SUSPECT'
            """
        ).fetchone()

        # 5. Duplicates check
        duplicates = self.check_duplicates()

        # 6. First observed GOLDTEN date
        goldten_first = self.conn.execute(
            """
            SELECT min(dp.trade_date)
            FROM daily_price dp
            JOIN contract c ON dp.contract_id = c.contract_id
            WHERE c.symbol = 'GOLDTEN'
            """
        ).fetchone()

        return {
            "symbol_counts": {s: cnt for s, cnt in symbol_counts},
            "min_trade_date": date_range[0] if date_range else None,
            "max_trade_date": date_range[1] if date_range else None,
            "unique_trade_dates": date_range[2] if date_range else 0,
            "total_daily_prices": date_range[3] if date_range else 0,
            "total_source_files": source_stats[0] if source_stats else 0,
            "ok_source_files": source_stats[1] if source_stats else 0,
            "rejected_source_files": source_stats[2] if source_stats else 0,
            "suspect_count": suspect_stats[0] if suspect_stats else 0,
            "duplicates_count": len(duplicates),
            "goldten_first_date": goldten_first[0] if goldten_first else None
        }
