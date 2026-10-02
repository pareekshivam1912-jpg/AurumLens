"""Pydantic configuration models and facts register schemas for AurumLens.

Every external fact or parameter carries a verification status:
- VERIFIED_OFFICIAL: Confirmed directly from MCX/SEBI circular or official contract specification.
- SECONDARY: Sourced from broker specifications or industry publications.
- DISPUTED: Competing or contradictory values exist across sources (e.g. GOLDGUINEA purity).
- TO_VERIFY / TO_VALIDATE: Unconfirmed candidate or placeholder value.
"""

from enum import Enum
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class FactStatus(str, Enum):
    VERIFIED_OFFICIAL = "VERIFIED_OFFICIAL"
    SECONDARY = "SECONDARY"
    DISPUTED = "DISPUTED"
    TO_VERIFY = "TO_VERIFY"
    TO_VALIDATE = "TO_VALIDATE"


class SpecMode(str, Enum):
    STRICT = "strict"
    RESEARCH = "research"


class FieldMeta(BaseModel, Generic[T]):
    """Every specification field tracks its provenance, status, and value."""
    value: Optional[T] = None
    status: FactStatus = FactStatus.TO_VERIFY
    source: Optional[str] = None
    verified_at: Optional[str] = None
    candidates: Optional[List[T]] = None
    note: Optional[str] = None


class TargetBasis(BaseModel):
    grams: float = 10.0
    purity: float = 0.999


class ContractSpecConfig(BaseModel):
    trading_unit_g: FieldMeta[float]
    quote_basis_g: FieldMeta[float]
    purity: FieldMeta[float]
    expiry_rule: FieldMeta[str]
    tender_days: FieldMeta[int]
    tick_size: Optional[FieldMeta[float]] = None


class ContractsConfig(BaseModel):
    spec_mode: SpecMode = SpecMode.RESEARCH
    target_basis: TargetBasis = TargetBasis()
    contracts: dict[str, ContractSpecConfig]


class BrokerageCostConfig(BaseModel):
    mode: str = "min_flat_pct"
    flat_inr: Optional[float] = None
    pct: Optional[float] = None
    status: FactStatus = FactStatus.SECONDARY
    note: Optional[str] = None
    source: Optional[str] = None
    verified_at: Optional[str] = None


class RateCostConfig(BaseModel):
    rate: Optional[float] = None
    status: FactStatus = FactStatus.SECONDARY
    note: Optional[str] = None
    source: Optional[str] = None
    verified_at: Optional[str] = None
    applies_to: Optional[List[str]] = None


class ValueCostConfig(BaseModel):
    value: Optional[float] = None
    status: FactStatus = FactStatus.TO_VALIDATE
    note: Optional[str] = None


class CostsConfig(BaseModel):
    brokerage: BrokerageCostConfig
    ctt_sell: RateCostConfig
    exchange: RateCostConfig
    sebi: RateCostConfig
    stamp_buy: RateCostConfig
    gst: RateCostConfig
    safety_buffer_inr_per_10g: ValueCostConfig


class ScoringConfig(BaseModel):
    lookback_window: int = 60
    min_history_obs: int = 30
    entry_z: float = 2.0
    exit_z: float = 0.5
    score_method: str = "zscore"  # zscore | mad


class PairingConfig(BaseModel):
    max_expiry_gap_days: int = 35
    carry_fallback_rate: Optional[float] = None
    block_on_carry_fallback: bool = False


class PriceQualityConfig(BaseModel):
    price_source: str = "close"  # settlement | close
    min_volume_for_price: int = 5
    stale_gap_threshold: float = 0.015


class LiquidityConfig(BaseModel):
    min_volume: int = 10
    min_oi: int = 50
    volume_sma_days: int = 5


class ExpiryConfig(BaseModel):
    unsafe_expiry_window_days: int = 5


class SlippageConfig(BaseModel):
    slippage_model: str = "corwin_schultz"  # corwin_schultz | fixed_bps
    fallback_bps: dict[str, float] = Field(default_factory=dict)
    cs_window: int = 5


class ConvergenceConfig(BaseModel):
    convergence_capture_ratio: float = 0.65


class SizingConfig(BaseModel):
    max_lots_per_leg: int = 50
    max_notional_inr: float = 2_500_000.0


class BacktestConfig(BaseModel):
    max_holding_days: int = 15
    train_window: int = 120
    test_window: int = 30
    holdout_start: Optional[str] = None
    execution_price: str = "close"


class StrategyConfig(BaseModel):
    scoring: ScoringConfig = ScoringConfig()
    pairing: PairingConfig = PairingConfig()
    price_quality: PriceQualityConfig = PriceQualityConfig()
    liquidity: LiquidityConfig = LiquidityConfig()
    expiry: ExpiryConfig = ExpiryConfig()
    slippage: SlippageConfig = SlippageConfig()
    convergence: ConvergenceConfig = ConvergenceConfig()
    sizing: SizingConfig = SizingConfig()
    backtest: BacktestConfig = BacktestConfig()


class MarketEvent(BaseModel):
    event_date: str
    label: str
    category: Optional[str] = "REGULATORY"
    source: Optional[str] = None
    verified: bool = False


class EventsConfig(BaseModel):
    events: List[MarketEvent] = Field(default_factory=list)
