"""Supabase Repository Layer for AurumLens.

Uses the service-role key from the environment (SUPABASE_SERVICE_ROLE_KEY)
to upload raw Bhavcopies to the private `bhavcopy-raw` Storage bucket and
upsert records into `source_file`, `contract`, and `daily_price`.

Quant/Security Invariants:
- Service role key is read ONLY from environment; NEVER committed, logged, or exposed in web/.
- Gracefully handles offline mode if service role key is absent.
- Storage files are immutable and keyed by `{era}/{yyyy}/{yyyy-mm-dd}_{sha256[:12]}.csv`.
"""

from datetime import date
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SupabaseRepository:
    """Writes raw files and analytical data to Supabase using the service-role key."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        service_role_key: Optional[str] = None
    ) -> None:
        self.supabase_url = (
            supabase_url
            or os.environ.get("SUPABASE_URL")
            or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
            or "https://iozdysrapznxefleqcfu.supabase.co"
        )
        self.service_role_key = service_role_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self._client = None

        if self.service_role_key:
            try:
                from supabase import create_client
                self._client = create_client(self.supabase_url, self.service_role_key)
                logger.info(f"Supabase client initialized for {self.supabase_url} with service-role")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self._client = None
        else:
            logger.info("SUPABASE_SERVICE_ROLE_KEY not found in environment; operating in offline/local mode")

    @property
    def is_connected(self) -> bool:
        """Return True if Supabase client is configured and ready to write."""
        return self._client is not None

    def upload_raw_file(self, storage_path: str, content: str, bucket_name: str = "bhavcopy-raw") -> bool:
        """Upload raw Bhavcopy CSV content to private storage bucket.
        
        Files are keyed by path containing sha256 to ensure immutability.
        """
        if not self.is_connected:
            return False

        try:
            content_bytes = content.encode("utf-8")
            # Supabase storage upload
            res = self._client.storage.from_(bucket_name).upload(
                path=storage_path,
                file=content_bytes,
                file_options={"content-type": "text/csv", "upsert": "false"}
            )
            logger.info(f"Uploaded raw file to Supabase Storage: {bucket_name}/{storage_path}")
            return True
        except Exception as e:
            # If already exists, that's fine (immutable)
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                logger.info(f"File already exists in Supabase Storage: {storage_path}")
                return True
            logger.warning(f"Failed to upload {storage_path} to Supabase Storage: {e}")
            return False

    def insert_source_file(
        self,
        requested_date: date,
        adapter: str,
        sha256: str,
        storage_path: str,
        status: str,
        returned_date: Optional[date] = None,
        reject_reason: Optional[str] = None
    ) -> Optional[int]:
        """Insert a source_file row and return generated file_id."""
        if not self.is_connected:
            return None

        payload = {
            "requested_date": requested_date.isoformat(),
            "returned_date": returned_date.isoformat() if returned_date else None,
            "adapter": adapter,
            "sha256": sha256,
            "storage_path": storage_path,
            "status": status,
            "reject_reason": reject_reason
        }

        try:
            # Check if exists by sha256
            existing = self._client.table("source_file").select("file_id").eq("sha256", sha256).execute()
            if existing.data:
                return existing.data[0]["file_id"]

            res = self._client.table("source_file").insert(payload).execute()
            if res.data:
                return res.data[0]["file_id"]
        except Exception as e:
            logger.error(f"Error inserting source_file to Supabase: {e}")

        return None

    def upsert_contract(
        self,
        contract_id: str,
        symbol: str,
        expiry_date: date,
        trade_date: date
    ) -> None:
        """Upsert contract record in Supabase."""
        if not self.is_connected:
            return

        payload = {
            "contract_id": contract_id,
            "symbol": symbol,
            "expiry_date": expiry_date.isoformat(),
            "first_seen": trade_date.isoformat(),
            "last_seen": trade_date.isoformat()
        }

        try:
            self._client.table("contract").upsert(
                payload,
                on_conflict="contract_id"
            ).execute()
        except Exception as e:
            logger.error(f"Error upserting contract {contract_id} to Supabase: {e}")

    def insert_daily_prices(
        self,
        records: List[Any],
        file_id: int,
        dataset_version: str
    ) -> int:
        """Upsert a batch of QualityAssessedRecord objects into public.daily_price."""
        if not self.is_connected or not records:
            return 0

        rows = []
        for r in records:
            rows.append({
                "contract_id": r.contract_id,
                "trade_date": r.trade_date.isoformat(),
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "settlement": r.settlement,
                "volume": r.volume,
                "open_interest": r.open_interest,
                "price_used": r.price_used,
                "price_source": r.price_source,
                "price_quality": r.price_quality,
                "quality_reason": r.quality_reason,
                "normalized_price": r.normalized_price,
                "file_id": file_id,
                "dataset_version": dataset_version
            })

        try:
            self._client.table("daily_price").upsert(
                rows,
                on_conflict="contract_id,trade_date"
            ).execute()
            return len(rows)
        except Exception as e:
            logger.error(f"Error upserting daily_price rows to Supabase: {e}")
            return 0
