"""Tests for DuckDBRepository and ParquetSnapshotStore."""

from datetime import date
from pathlib import Path
import pytest

from aurumlens.db.duckdb_repo import DuckDBRepository
from aurumlens.db.parquet_store import ParquetSnapshotStore
from aurumlens.ingest.quality import QualityAssessedRecord


@pytest.fixture
def memory_repo():
    repo = DuckDBRepository(Path(":memory:"))
    yield repo
    repo.close()


def make_quality_record(
    contract_id: str = "GOLDM_20261105",
    symbol: str = "GOLDM",
    trade_date: date = date(2026, 10, 1),
    expiry_date: date = date(2026, 11, 5),
    price_quality: str = "OK"
) -> QualityAssessedRecord:
    return QualityAssessedRecord(
        contract_id=contract_id,
        symbol=symbol,
        trade_date=trade_date,
        expiry_date=expiry_date,
        open=74900.0,
        high=75500.0,
        low=74800.0,
        close=75200.0,
        settlement=None,
        volume=150,
        open_interest=500,
        price_used=75200.0,
        price_source="close",
        price_quality=price_quality,
        quality_reason=None if price_quality == "OK" else "LOW_VOLUME",
        normalized_price=None
    )


def test_duckdb_source_file_and_duplicate_prevention(memory_repo):
    fid1 = memory_repo.insert_source_file(
        requested_date=date(2026, 10, 1),
        adapter="cdp",
        sha256="abc123sha",
        storage_path="cdp/2026/2026-10-01_abc123.csv",
        status="OK"
    )
    assert fid1 > 0

    # Same sha256 returns existing file_id
    fid2 = memory_repo.insert_source_file(
        requested_date=date(2026, 10, 1),
        adapter="cdp",
        sha256="abc123sha",
        storage_path="cdp/2026/2026-10-01_abc123.csv",
        status="OK"
    )
    assert fid2 == fid1


def test_duckdb_contract_tracking(memory_repo):
    cid = "GOLDM_20261105"
    memory_repo.upsert_contract(cid, "GOLDM", date(2026, 11, 5), date(2026, 10, 1))
    memory_repo.upsert_contract(cid, "GOLDM", date(2026, 11, 5), date(2026, 10, 5))
    memory_repo.upsert_contract(cid, "GOLDM", date(2026, 11, 5), date(2026, 9, 28))

    row = memory_repo.conn.execute("SELECT first_seen, last_seen FROM contract WHERE contract_id = ?", [cid]).fetchone()
    assert row[0] == date(2026, 9, 28)
    assert row[1] == date(2026, 10, 5)


def test_duckdb_daily_price_and_no_duplicates(memory_repo):
    fid = memory_repo.insert_source_file(
        requested_date=date(2026, 10, 1),
        adapter="cdp",
        sha256="hash1",
        storage_path="cdp/2026/test.csv",
        status="OK"
    )

    rec1 = make_quality_record(contract_id="GOLDM_20261105", symbol="GOLDM", trade_date=date(2026, 10, 1))
    rec2 = make_quality_record(contract_id="GOLDTEN_20261031", symbol="GOLDTEN", trade_date=date(2026, 10, 1), expiry_date=date(2026, 10, 31))

    memory_repo.upsert_contract(rec1.contract_id, rec1.symbol, rec1.expiry_date, rec1.trade_date)
    memory_repo.upsert_contract(rec2.contract_id, rec2.symbol, rec2.expiry_date, rec2.trade_date)

    inserted = memory_repo.insert_daily_prices([rec1, rec2], fid, "v1.0")
    assert inserted == 2

    # Duplicate insert attempt should insert 0 rows
    dup_inserted = memory_repo.insert_daily_prices([rec1], fid, "v1.0")
    assert dup_inserted == 0

    duplicates = memory_repo.check_duplicates()
    assert len(duplicates) == 0


def test_parquet_snapshot_and_manifest(tmp_path, memory_repo):
    fid = memory_repo.insert_source_file(
        requested_date=date(2026, 10, 1),
        adapter="cdp",
        sha256="hash_pq",
        storage_path="cdp/2026/pq.csv",
        status="OK"
    )
    rec = make_quality_record()
    memory_repo.upsert_contract(rec.contract_id, rec.symbol, rec.expiry_date, rec.trade_date)
    memory_repo.insert_daily_prices([rec], fid, "2026-10-01_v1")

    store = ParquetSnapshotStore(tmp_path / "processed")
    manifest = store.export_snapshot(memory_repo, "2026-10-01_v1")

    assert manifest["dataset_version"] == "2026-10-01_v1"
    assert manifest["files"]["daily_price"]["rows"] == 1
    assert manifest["files"]["contract"]["rows"] == 1

    dp_df, c_df, loaded_manifest = store.load_snapshot("2026-10-01_v1")
    assert len(dp_df) == 1
    assert len(c_df) == 1
    assert loaded_manifest["dataset_version"] == "2026-10-01_v1"
