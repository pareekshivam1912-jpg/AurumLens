"""Parquet Dataset Snapshot Store with dataset_version tracking.

Quant Invariants:
- Snapshots are immutable and identified by `dataset_version`.
- Every snapshot includes a manifest with row counts, date bounds, symbol counts, and SHA256 checksums.
- Enables reproducible backtesting and fully offline demos.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from aurumlens.db.duckdb_repo import DuckDBRepository

logger = logging.getLogger(__name__)


def compute_file_sha256(file_path: Path) -> str:
    """Compute sha256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class ParquetSnapshotStore:
    """Exports and loads versioned Parquet dataset snapshots from DuckDB."""

    def __init__(self, processed_dir: Optional[Path] = None) -> None:
        self.processed_dir = processed_dir or Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def export_snapshot(
        self,
        repo: DuckDBRepository,
        dataset_version: str
    ) -> Dict[str, Any]:
        """Export daily_price and contract tables to a versioned Parquet snapshot.
        
        Args:
            repo: DuckDBRepository instance containing ingested data.
            dataset_version: Version identifier string (e.g. '2026-09-30_v1').
            
        Returns:
            Manifest dictionary with snapshot metadata.
        """
        snapshot_dir = self.processed_dir / f"dataset_{dataset_version}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # 1. Export daily_price
        dp_df = repo.conn.execute("SELECT * FROM daily_price ORDER BY trade_date, contract_id").df()
        dp_path = snapshot_dir / "daily_price.parquet"
        dp_df.to_parquet(dp_path, index=False, engine="pyarrow")
        dp_sha = compute_file_sha256(dp_path)

        # 2. Export contract
        c_df = repo.conn.execute("SELECT * FROM contract ORDER BY symbol, expiry_date").df()
        c_path = snapshot_dir / "contract.parquet"
        c_df.to_parquet(c_path, index=False, engine="pyarrow")
        c_sha = compute_file_sha256(c_path)

        # 3. Export source_file
        sf_df = repo.conn.execute("SELECT * FROM source_file ORDER BY requested_date").df()
        sf_path = snapshot_dir / "source_file.parquet"
        sf_df.to_parquet(sf_path, index=False, engine="pyarrow")
        sf_sha = compute_file_sha256(sf_path)

        # 4. Generate manifest
        stats = repo.get_summary_stats()
        manifest = {
            "dataset_version": dataset_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": {
                "daily_price": {
                    "path": str(dp_path.name),
                    "rows": len(dp_df),
                    "sha256": dp_sha
                },
                "contract": {
                    "path": str(c_path.name),
                    "rows": len(c_df),
                    "sha256": c_sha
                },
                "source_file": {
                    "path": str(sf_path.name),
                    "rows": len(sf_df),
                    "sha256": sf_sha
                }
            },
            "statistics": stats
        }

        manifest_path = snapshot_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        logger.info(f"Parquet snapshot {dataset_version} created at {snapshot_dir}")

        return manifest

    def load_snapshot(
        self,
        dataset_version: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """Load DataFrames and manifest for a given dataset_version."""
        snapshot_dir = self.processed_dir / f"dataset_{dataset_version}"
        if not snapshot_dir.exists():
            raise FileNotFoundError(f"Snapshot directory not found: {snapshot_dir}")

        dp_path = snapshot_dir / "daily_price.parquet"
        c_path = snapshot_dir / "contract.parquet"
        manifest_path = snapshot_dir / "manifest.json"

        if not dp_path.exists() or not c_path.exists() or not manifest_path.exists():
            raise FileNotFoundError(f"Missing snapshot files in {snapshot_dir}")

        dp_df = pd.read_parquet(dp_path, engine="pyarrow")
        c_df = pd.read_parquet(c_path, engine="pyarrow")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        return dp_df, c_df, manifest
