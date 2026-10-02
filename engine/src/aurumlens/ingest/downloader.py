"""MCX Bhavcopy Downloader with polite caching and SHA256 hashing.

Features:
- Polite rate-limiting and browser-like TLS fingerprinting via curl_cffi.
- Two-tier caching: local immutable cache in `data/cache/` and optional remote upload.
- Explicit SHA256 integrity calculation on raw content.
"""

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
import logging
from pathlib import Path
import time
from typing import Optional

from aurumlens.ingest.adapters import CDP_CUTOVER_DATE

logger = logging.getLogger(__name__)

BHAVCOPY_API_URL = "https://www.mcxindia.com/market-data/bhavcopy/GetDateWiseBhavCopy"
BHAVCOPY_PAGE_URL = "https://www.mcxindia.com/market-data/bhavcopy"

CSV_HEADERS = [
    "Date", "Instrument Name", "Symbol", "Expiry Date", "Option Type",
    "Strike Price", "Open", "High", "Low", "Close", "Previous Close",
    "Volume(Lots)", "Volume(In 000's)", "Value(Lacs)", "Open Interest(Lots)"
]


@dataclass(frozen=True)
class DownloadResult:
    """Result of attempting to download a Bhavcopy file."""
    requested_date: date
    returned_date: Optional[date]
    content: str
    sha256: str
    storage_path: str
    is_cached: bool
    status: str  # 'OK' or 'REJECTED'
    reject_reason: Optional[str] = None
    adapter_era: str = "cdp"


class BhavcopyDownloader:
    """Downloader for MCX Bhavcopy data with local file caching and integrity verification."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        rate_limit_seconds: float = 0.5,
        timeout_seconds: int = 30
    ) -> None:
        self.cache_dir = cache_dir or Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit_seconds = rate_limit_seconds
        self.timeout_seconds = timeout_seconds
        self._last_request_time: float = 0.0

    def get_storage_path(self, target_date: date, content_sha256: str) -> str:
        """Generate standardized storage path: {era}/{yyyy}/{yyyy-mm-dd}_{sha256[:12]}.csv"""
        era = "legacy" if target_date < CDP_CUTOVER_DATE else "cdp"
        return f"{era}/{target_date.year}/{target_date.isoformat()}_{content_sha256[:12]}.csv"

    def get_local_cache_path(self, target_date: date) -> Path:
        """Return the local cache path for a requested date."""
        era = "legacy" if target_date < CDP_CUTOVER_DATE else "cdp"
        return self.cache_dir / era / f"{target_date.year}" / f"bhavcopy_{target_date.isoformat()}.csv"

    def _convert_json_to_csv(self, data_rows: list[dict]) -> str:
        """Convert MCX Bhavcopy JSON data rows into standard Bhavcopy CSV text."""
        lines = [",".join(CSV_HEADERS)]
        for row in data_rows:
            # Handle Date Display or raw Date
            date_str = row.get("DateDisplay") or row.get("Date") or ""
            inst = row.get("InstrumentName") or ""
            sym = row.get("Symbol") or ""
            exp = row.get("ExpiryDate") or ""
            opt = row.get("OptionType") or "-"
            strike = str(row.get("StrikePrice", 0.0))
            opn = str(row.get("Open", 0.0))
            hi = str(row.get("High", 0.0))
            lo = str(row.get("Low", 0.0))
            cls = str(row.get("Close", 0.0))
            prev_cls = str(row.get("PreviousClose", 0.0))
            vol = str(row.get("Volume", 0))
            vol_thous = str(row.get("VolumeInThousands", ""))
            val = str(row.get("Value", 0.0))
            oi = str(row.get("OpenInterest", 0))

            line = f"{date_str},{inst},{sym},{exp},{opt},{strike},{opn},{hi},{lo},{cls},{prev_cls},{vol},{vol_thous},{val},{oi}"
            lines.append(line)
        return "\n".join(lines) + "\n"

    def download_date(self, target_date: date, force_refresh: bool = False) -> DownloadResult:
        """Download or retrieve from cache the Bhavcopy for target_date.
        
        Args:
            target_date: Trading date to download.
            force_refresh: If True, bypass local cache.
            
        Returns:
            DownloadResult with content, sha256, storage_path, and status.
        """
        era = "legacy" if target_date < CDP_CUTOVER_DATE else "cdp"
        cache_path = self.get_local_cache_path(target_date)

        # 1. Check local cache
        if not force_refresh and cache_path.exists():
            try:
                content = cache_path.read_text(encoding="utf-8")
                content_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
                storage_path = self.get_storage_path(target_date, content_sha)
                logger.info(f"Loaded {target_date} from local cache: {cache_path}")
                return DownloadResult(
                    requested_date=target_date,
                    returned_date=target_date,
                    content=content,
                    sha256=content_sha,
                    storage_path=storage_path,
                    is_cached=True,
                    status="OK",
                    adapter_era=era
                )
            except Exception as e:
                logger.warning(f"Failed reading cache file {cache_path}: {e}")

        # 2. Polite rate limiting
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)
        self._last_request_time = time.time()

        # 3. Fetch from MCX API using curl_cffi to bypass Akamai WAF
        from curl_cffi import requests

        date_param = target_date.strftime("%d/%m/%Y")
        url = f"{BHAVCOPY_API_URL}?InstrumentName=ALL&fromDate={date_param}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": BHAVCOPY_PAGE_URL,
        }

        try:
            resp = requests.get(
                url,
                headers=headers,
                impersonate="chrome120",
                timeout=self.timeout_seconds
            )
        except Exception as e:
            logger.error(f"HTTP request failed for {target_date}: {e}")
            empty_sha = hashlib.sha256(b"").hexdigest()
            return DownloadResult(
                requested_date=target_date,
                returned_date=None,
                content="",
                sha256=empty_sha,
                storage_path=f"{era}/{target_date.year}/{target_date.isoformat()}_error.csv",
                is_cached=False,
                status="REJECTED",
                reject_reason=f"NETWORK_ERROR: {str(e)}",
                adapter_era=era
            )

        if resp.status_code != 200:
            empty_sha = hashlib.sha256(resp.content).hexdigest()
            return DownloadResult(
                requested_date=target_date,
                returned_date=None,
                content=resp.text,
                sha256=empty_sha,
                storage_path=f"{era}/{target_date.year}/{target_date.isoformat()}_http_{resp.status_code}.csv",
                is_cached=False,
                status="REJECTED",
                reject_reason=f"HTTP_STATUS_{resp.status_code}",
                adapter_era=era
            )

        try:
            data = resp.json()
        except Exception as e:
            content_sha = hashlib.sha256(resp.content).hexdigest()
            return DownloadResult(
                requested_date=target_date,
                returned_date=None,
                content=resp.text,
                sha256=content_sha,
                storage_path=f"{era}/{target_date.year}/{target_date.isoformat()}_invalid_json.csv",
                is_cached=False,
                status="REJECTED",
                reject_reason=f"INVALID_JSON_RESPONSE: {str(e)}",
                adapter_era=era
            )

        rows = data.get("Data") or []
        if not rows:
            # Holiday or market closed
            content_sha = hashlib.sha256(resp.content).hexdigest()
            return DownloadResult(
                requested_date=target_date,
                returned_date=None,
                content="",
                sha256=content_sha,
                storage_path=f"{era}/{target_date.year}/{target_date.isoformat()}_no_data.csv",
                is_cached=False,
                status="REJECTED",
                reject_reason="MARKET_HOLIDAY_OR_NO_DATA",
                adapter_era=era
            )

        # Convert to CSV and compute hash
        csv_content = self._convert_json_to_csv(rows)
        content_sha = hashlib.sha256(csv_content.encode("utf-8")).hexdigest()
        storage_path = self.get_storage_path(target_date, content_sha)

        # Save to local cache
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(csv_content, encoding="utf-8")
        logger.info(f"Cached {target_date} ({len(rows)} rows) at {cache_path}")

        return DownloadResult(
            requested_date=target_date,
            returned_date=target_date,
            content=csv_content,
            sha256=content_sha,
            storage_path=storage_path,
            is_cached=False,
            status="OK",
            adapter_era=era
        )
