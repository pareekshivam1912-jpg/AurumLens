"""Historical Data Ingestion Pipeline for AurumLens (Phase 1 / A3).

Orchestrates:
1. Downloader (polite caching, curl_cffi, SHA256 integrity).
2. Era adapter selection (legacy vs CDP).
3. Validator (date equality, symbol filtering, deduplication, conflicting duplicate rejection).
4. Price Quality stage (settlement/close selection, SUSPECT classification).
5. Persistence to UnifiedRepository (DuckDB + Parquet snapshot + Supabase).
6. Comprehensive Ingestion Reporting.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from aurumlens.config.loader import load_strategy_config
from aurumlens.db.repository import UnifiedRepository
from aurumlens.ingest.adapters import CDP_CUTOVER_DATE, get_adapter_for_date
from aurumlens.ingest.downloader import BhavcopyDownloader, DownloadResult
from aurumlens.ingest.quality import PriceQualityEvaluator, QualityAssessedRecord
from aurumlens.ingest.validator import IngestValidator, ValidationReport

logger = logging.getLogger(__name__)


@dataclass
class DateIngestResult:
    """Result of processing a single trading date."""
    requested_date: date
    returned_date: Optional[date]
    status: str  # 'OK' or 'REJECTED'
    adapter_era: str
    sha256: str
    raw_rows_count: int
    records_ingested: int
    duplicates_removed: int
    conflicting_duplicates: int
    suspect_count: int
    symbols: Set[str] = field(default_factory=set)
    reject_reason: Optional[str] = None


@dataclass
class IngestionReport:
    """Consolidated ingestion report covering an entire date range or batch."""
    dataset_version: str
    generated_at: str
    total_dates_requested: int
    successful_dates: int
    rejected_dates: int
    total_records_ingested: int
    records_by_symbol: Dict[str, int]
    records_by_era: Dict[str, int]
    min_trade_date: Optional[date]
    max_trade_date: Optional[date]
    unique_trade_dates: int
    suspect_count: int
    duplicates_count: int
    rejections: List[Dict[str, Any]]
    goldten_first_observed_date: Optional[date]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_version": self.dataset_version,
            "generated_at": self.generated_at,
            "total_dates_requested": self.total_dates_requested,
            "successful_dates": self.successful_dates,
            "rejected_dates": self.rejected_dates,
            "total_records_ingested": self.total_records_ingested,
            "records_by_symbol": self.records_by_symbol,
            "records_by_era": self.records_by_era,
            "date_range": {
                "min": self.min_trade_date.isoformat() if self.min_trade_date else None,
                "max": self.max_trade_date.isoformat() if self.max_trade_date else None,
                "unique_dates": self.unique_trade_dates
            },
            "suspect_count": self.suspect_count,
            "duplicates_count": self.duplicates_count,
            "goldten_first_observed_date": self.goldten_first_observed_date.isoformat() if self.goldten_first_observed_date else None,
            "rejections": self.rejections
        }


class IngestionPipeline:
    """Coordinates historical Bhavcopy ingestion from source to verified repository."""

    def __init__(
        self,
        repository: UnifiedRepository,
        downloader: Optional[BhavcopyDownloader] = None,
        validator: Optional[IngestValidator] = None,
        quality_evaluator: Optional[PriceQualityEvaluator] = None,
        config_path: Path = Path("config")
    ) -> None:
        self.repository = repository
        self.downloader = downloader or BhavcopyDownloader()
        self.validator = validator or IngestValidator()

        if quality_evaluator is None:
            strategy_cfg = load_strategy_config(config_path / "strategy.yaml")
            self.quality_evaluator = PriceQualityEvaluator.from_strategy_config(strategy_cfg)
        else:
            self.quality_evaluator = quality_evaluator

    def ingest_date(
        self,
        target_date: date,
        dataset_version: str,
        force_refresh: bool = False
    ) -> DateIngestResult:
        """Ingest a single trading date through all pipeline stages."""
        adapter = get_adapter_for_date(target_date)
        era = adapter.era_name

        # 1. Download / retrieve from cache
        dl_res = self.downloader.download_date(target_date, force_refresh=force_refresh)

        if dl_res.status != "OK":
            # Record rejection in repository
            self.repository.persist_ingestion_unit(
                requested_date=target_date,
                returned_date=None,
                adapter=era,
                content="",
                sha256=dl_res.sha256,
                storage_path=dl_res.storage_path,
                status="REJECTED",
                records=[],
                dataset_version=dataset_version,
                reject_reason=dl_res.reject_reason
            )
            return DateIngestResult(
                requested_date=target_date,
                returned_date=None,
                status="REJECTED",
                adapter_era=era,
                sha256=dl_res.sha256,
                raw_rows_count=0,
                records_ingested=0,
                duplicates_removed=0,
                conflicting_duplicates=0,
                suspect_count=0,
                reject_reason=dl_res.reject_reason
            )

        # 2. Validate and deduplicate
        val_res = self.validator.validate_and_deduplicate(
            content=dl_res.content,
            requested_date=target_date,
            adapter=adapter
        )

        if not val_res.is_valid:
            self.repository.persist_ingestion_unit(
                requested_date=target_date,
                returned_date=val_res.returned_date,
                adapter=era,
                content=dl_res.content,
                sha256=dl_res.sha256,
                storage_path=dl_res.storage_path,
                status="REJECTED",
                records=[],
                dataset_version=dataset_version,
                reject_reason=val_res.reject_reason
            )
            return DateIngestResult(
                requested_date=target_date,
                returned_date=val_res.returned_date,
                status="REJECTED",
                adapter_era=era,
                sha256=dl_res.sha256,
                raw_rows_count=val_res.total_raw_rows,
                records_ingested=0,
                duplicates_removed=val_res.duplicates_removed,
                conflicting_duplicates=val_res.conflicting_duplicates,
                suspect_count=0,
                reject_reason=val_res.reject_reason
            )

        # 3. Price-quality evaluation
        assessed_records = self.quality_evaluator.evaluate_batch(val_res.records)
        suspect_count = sum(1 for r in assessed_records if r.price_quality == "SUSPECT")

        # 4. Persist to repository
        self.repository.persist_ingestion_unit(
            requested_date=target_date,
            returned_date=target_date,
            adapter=era,
            content=dl_res.content,
            sha256=dl_res.sha256,
            storage_path=dl_res.storage_path,
            status="OK",
            records=assessed_records,
            dataset_version=dataset_version,
            reject_reason=None
        )

        return DateIngestResult(
            requested_date=target_date,
            returned_date=target_date,
            status="OK",
            adapter_era=era,
            sha256=dl_res.sha256,
            raw_rows_count=val_res.total_raw_rows,
            records_ingested=len(assessed_records),
            duplicates_removed=val_res.duplicates_removed,
            conflicting_duplicates=val_res.conflicting_duplicates,
            suspect_count=suspect_count,
            symbols=val_res.symbols_present
        )

    def ingest_dates(
        self,
        dates: List[date],
        dataset_version: str,
        export_snapshot: bool = True
    ) -> IngestionReport:
        """Ingest a series of dates, persist data, and generate a consolidation report."""
        results: List[DateIngestResult] = []
        for d in dates:
            res = self.ingest_date(d, dataset_version=dataset_version)
            results.append(res)

        # Query stats from DuckDB repository
        stats = self.repository.duckdb_repo.get_summary_stats()

        # Group by era
        era_counts: Dict[str, int] = {"legacy": 0, "cdp": 0}
        for r in results:
            if r.status == "OK":
                era_counts[r.adapter_era] = era_counts.get(r.adapter_era, 0) + r.records_ingested

        rejections = [
            {
                "requested_date": r.requested_date.isoformat(),
                "returned_date": r.returned_date.isoformat() if r.returned_date else None,
                "reason": r.reject_reason,
                "adapter": r.adapter_era
            }
            for r in results if r.status == "REJECTED"
        ]

        report = IngestionReport(
            dataset_version=dataset_version,
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_dates_requested=len(dates),
            successful_dates=sum(1 for r in results if r.status == "OK"),
            rejected_dates=len(rejections),
            total_records_ingested=stats["total_daily_prices"],
            records_by_symbol=stats["symbol_counts"],
            records_by_era=era_counts,
            min_trade_date=stats["min_trade_date"],
            max_trade_date=stats["max_trade_date"],
            unique_trade_dates=stats["unique_trade_dates"],
            suspect_count=stats["suspect_count"],
            duplicates_count=stats["duplicates_count"],
            rejections=rejections,
            goldten_first_observed_date=stats["goldten_first_date"]
        )

        if export_snapshot:
            self.repository.export_snapshot(dataset_version)

        return report
