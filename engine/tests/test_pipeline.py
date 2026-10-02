"""End-to-end integration tests for IngestionPipeline using real fixture samples."""

from datetime import date
from pathlib import Path
import pytest

from aurumlens.db.repository import UnifiedRepository
from aurumlens.ingest.downloader import BhavcopyDownloader, DownloadResult
from aurumlens.ingest.pipeline import IngestionPipeline
from aurumlens.ingest.quality import PriceQualityEvaluator


class MockDownloader(BhavcopyDownloader):
    """Downloader that serves real fixture samples from data/fixtures/real_samples."""

    def __init__(self, fixtures_dir: Path) -> None:
        super().__init__()
        self.fixtures_dir = fixtures_dir

    def download_date(self, target_date: date, force_refresh: bool = False) -> DownloadResult:
        if target_date == date(2023, 9, 15):
            path = self.fixtures_dir / "bhavcopy_20230915_legacy.csv"
            content = path.read_text(encoding="utf-8")
            return DownloadResult(
                requested_date=target_date,
                returned_date=target_date,
                content=content,
                sha256="sha_legacy_fixture_123",
                storage_path="legacy/2023/2023-09-15_sha_legacy.csv",
                is_cached=True,
                status="OK",
                adapter_era="legacy"
            )
        elif target_date == date(2026, 10, 1):
            path = self.fixtures_dir / "bhavcopy_20261001_cdp.csv"
            content = path.read_text(encoding="utf-8")
            return DownloadResult(
                requested_date=target_date,
                returned_date=target_date,
                content=content,
                sha256="sha_cdp_fixture_456",
                storage_path="cdp/2026/2026-10-01_sha_cdp.csv",
                is_cached=True,
                status="OK",
                adapter_era="cdp"
            )
        elif target_date == date(2026, 10, 2):
            # Simulated holiday / closed date
            return DownloadResult(
                requested_date=target_date,
                returned_date=None,
                content="",
                sha256="sha_holiday_789",
                storage_path="cdp/2026/2026-10-02_no_data.csv",
                is_cached=False,
                status="REJECTED",
                reject_reason="MARKET_HOLIDAY_OR_NO_DATA",
                adapter_era="cdp"
            )
        else:
            raise ValueError(f"No mock fixture for {target_date}")


@pytest.fixture
def fixtures_dir():
    return Path("data/fixtures/real_samples")


def test_pipeline_ingest_both_eras_and_report(tmp_path, fixtures_dir):
    repo = UnifiedRepository(
        db_path=tmp_path / "test_aurumlens.duckdb",
        processed_dir=tmp_path / "processed",
        enable_supabase=False
    )
    downloader = MockDownloader(fixtures_dir)
    pipeline = IngestionPipeline(
        repository=repo,
        downloader=downloader,
        quality_evaluator=PriceQualityEvaluator(min_volume_for_price=5)
    )

    dates_to_ingest = [date(2023, 9, 15), date(2026, 10, 1), date(2026, 10, 2)]
    report = pipeline.ingest_dates(dates_to_ingest, dataset_version="test_v1")

    assert report.total_dates_requested == 3
    assert report.successful_dates == 2
    assert report.rejected_dates == 1
    assert report.duplicates_count == 0

    # Era checks
    assert report.records_by_era["legacy"] == 11   # 11 target futures in legacy sample
    assert report.records_by_era["cdp"] == 24      # 24 target futures in CDP sample
    assert report.total_records_ingested == 35

    # Symbol presence
    assert "GOLDM" in report.records_by_symbol
    assert "GOLDPETAL" in report.records_by_symbol
    assert "GOLDGUINEA" in report.records_by_symbol
    assert "GOLDTEN" in report.records_by_symbol

    # In legacy 2023, GOLDTEN did not exist; first observed date should be in 2026
    assert report.goldten_first_observed_date == date(2026, 10, 1)

    # Rejection verification
    assert len(report.rejections) == 1
    assert report.rejections[0]["reason"] == "MARKET_HOLIDAY_OR_NO_DATA"

    # Parquet snapshot verification
    snapshot_dir = tmp_path / "processed" / "dataset_test_v1"
    assert (snapshot_dir / "daily_price.parquet").exists()
    assert (snapshot_dir / "contract.parquet").exists()
    assert (snapshot_dir / "manifest.json").exists()

    repo.close()
