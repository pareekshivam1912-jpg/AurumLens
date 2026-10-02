"""CLI and execution script for historical Bhavcopy ingestion across legacy and CDP eras.

Usage:
    python -m aurumlens.scripts.ingest_historical --dataset-version 2026-10-01_v1
"""

import argparse
from datetime import date, timedelta
import json
import logging
from pathlib import Path
import sys
from typing import List

from aurumlens.db.repository import UnifiedRepository
from aurumlens.ingest.downloader import BhavcopyDownloader
from aurumlens.ingest.pipeline import IngestionPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aurumlens.ingest")


def get_default_sample_dates() -> List[date]:
    """Curated list of real trading dates across both eras, plus a weekend to verify reject logging."""
    return [
        # Pre-October 2023 legacy era (GOLDM, GOLDGUINEA, GOLDPETAL; GOLDTEN not yet launched)
        date(2023, 9, 11),
        date(2023, 9, 12),
        date(2023, 9, 13),
        date(2023, 9, 14),
        date(2023, 9, 15),

        # Weekend test date (Sunday - market closed, verifies rejection logging)
        date(2026, 9, 27),

        # Post-October 2023 CDP era (all 4 contracts active: GOLDM, GOLDTEN, GOLDGUINEA, GOLDPETAL)
        date(2026, 9, 28),
        date(2026, 9, 29),
        date(2026, 9, 30),
        date(2026, 10, 1),
    ]


def run_ingestion(
    dataset_version: str = "2026-10-01_v1",
    dates: List[date] = None,
    db_path: Path = Path("data/aurumlens.duckdb"),
    processed_dir: Path = Path("data/processed")
) -> dict:
    """Run full historical ingestion pipeline and export versioned Parquet snapshot."""
    if dates is None:
        dates = get_default_sample_dates()

    logger.info(f"Starting historical ingestion for {len(dates)} dates with dataset_version={dataset_version}")

    repo = UnifiedRepository(
        db_path=db_path,
        processed_dir=processed_dir,
        enable_supabase=True
    )
    downloader = BhavcopyDownloader(rate_limit_seconds=0.5)
    pipeline = IngestionPipeline(repository=repo, downloader=downloader)

    report = pipeline.ingest_dates(
        dates=dates,
        dataset_version=dataset_version,
        export_snapshot=True
    )

    report_dict = report.to_dict()
    report_file = processed_dir / f"ingestion_report_{dataset_version}.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report_dict, indent=2), encoding="utf-8")
    logger.info(f"Ingestion report written to {report_file}")

    return report_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest historical MCX Bhavcopy data.")
    parser.add_argument("--dataset-version", default="2026-10-01_v1", help="Dataset version identifier")
    args = parser.parse_args()

    report = run_ingestion(dataset_version=args.dataset_version)
    print("\n" + "=" * 60)
    print("INGESTION REPORT SUMMARY")
    print("=" * 60)
    print(json.dumps(report, indent=2))
