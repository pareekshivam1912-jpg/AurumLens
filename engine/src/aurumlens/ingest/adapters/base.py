"""SourceAdapter interface and CanonicalRecord schema for AurumLens.

All era-specific parsing details (legacy vs CDP) are encapsulated within their respective adapters.
Each adapter maps its era-specific columns and date formats to this canonical schema.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

ALLOW_LISTED_SYMBOLS = {"GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"}


class CanonicalRecord(BaseModel):
    """Canonical contract-level observation produced by all source adapters."""
    contract_id: str = Field(description="Unique contract identity formatted as SYMBOL_YYYYMMDD")
    symbol: str = Field(description="Standardized allow-listed commodity symbol")
    trade_date: date = Field(description="Date of trade")
    expiry_date: date = Field(description="Contract expiry date")
    open: float = Field(ge=0.0)
    high: float = Field(ge=0.0)
    low: float = Field(ge=0.0)
    close: float = Field(ge=0.0)
    settlement: Optional[float] = Field(default=None, ge=0.0)
    volume: int = Field(ge=0)
    open_interest: int = Field(ge=0)
    instrument_name: str = "FUTCOM"
    raw_symbol: Optional[str] = None


class SourceAdapter(ABC):
    """Abstract interface for Bhavcopy format adapters."""

    @property
    @abstractmethod
    def era_name(self) -> str:
        """Name of the era ('legacy' or 'cdp')."""
        pass

    @abstractmethod
    def can_parse(self, content_sample: str) -> bool:
        """Heuristic check to determine if the adapter can parse the given CSV content."""
        pass

    @abstractmethod
    def parse(
        self,
        content: str,
        requested_date: date,
        symbols_filter: Optional[set[str]] = None
    ) -> List[CanonicalRecord]:
        """Parse raw CSV content into canonical records.
        
        Args:
            content: Raw CSV text content.
            requested_date: The trade date requested (must match data date).
            symbols_filter: Optional set of symbols to filter for (defaults to ALLOW_LISTED_SYMBOLS).
        
        Returns:
            List of CanonicalRecord objects.
            
        Raises:
            ValueError: On date mismatch, schema mismatch, or invalid rows.
        """
        pass
