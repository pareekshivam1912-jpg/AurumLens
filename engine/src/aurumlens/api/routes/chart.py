"""Interactive Chart Data API Routes for AurumLens.

Provides pre-calculated OHLCV, raw vs normalized price parity, and cross-contract
log spread series with rolling Bollinger bounds and Z-score deviations.

Strict Quantitative Mandates:
- No financial math in frontend: all normalizations, spreads, and rolling statistics
  are computed here using pure quant analytics functions.
- Purity Direction Rule (R16): Sub-999 purity (e.g. GOLDM 995) must always normalize
  UPWARD to Rs per 10g of 999 gold.
- Strict No Look-Ahead: Rolling statistics at date t use history strictly through t-1.
- Audit & Truthfulness: Any fixture or generated series beyond raw Bhavcopy snapshots
  is explicitly watermarked as SYNTHETIC_FIXTURE.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from aurumlens.analytics.normalization import normalize_contract_price
from aurumlens.analytics.spread import compute_log_spread, compute_spread
from aurumlens.config.loader import load_contracts_config

chart_router = APIRouter(prefix="/v1/chart", tags=["Chart"])

# Load contracts configuration
_root_dir = Path(__file__).resolve().parents[4]
_config_path = _root_dir / "config" / "contracts.yaml"
if not _config_path.exists():
    _config_path = Path("config/contracts.yaml")
_contracts_config = load_contracts_config(_config_path)

_DB_PATH = _root_dir / "data" / "aurumlens.duckdb"
if not _DB_PATH.exists():
    _DB_PATH = Path("data/aurumlens.duckdb")


# --- Response Models ---

class CandlePoint(BaseModel):
    time: str = Field(..., description="Trade date in YYYY-MM-DD")
    open: float
    high: float
    low: float
    close: float
    volume: int
    open_interest: int
    raw_price: float
    normalized_price: float = Field(..., description="Normalized price in Rs per 10g of 999 fine gold")
    price_quality: str = Field("OK", description="'OK' or 'SUSPECT'")
    quality_reason: Optional[str] = None


class ContractSeriesResponse(BaseModel):
    symbol: str
    quote_basis_g: float
    purity: float
    purity_status: str
    data_status: str = Field(..., description="'VERIFIED_REAL' or 'SYNTHETIC_FIXTURE'")
    synthetic: bool
    points_count: int
    points: List[CandlePoint]


class PairSpreadPoint(BaseModel):
    time: str
    raw_a: float
    raw_b: float
    norm_a: float
    norm_b: float
    raw_diff: float
    norm_diff: float
    log_spread_raw: float
    carry_adj: float
    log_spread_adj: float
    roll_mean: Optional[float] = None
    roll_upper: Optional[float] = None
    roll_lower: Optional[float] = None
    roll_std: Optional[float] = None
    zscore: Optional[float] = None
    rich_leg: Optional[str] = None
    status: str = Field("QUIET", description="'ALERT', 'QUIET', or 'WARMUP'")
    is_alert: bool = False
    quality_a: str = "OK"
    quality_b: str = "OK"


class PairSeriesResponse(BaseModel):
    pair_name: str
    leg_a_symbol: str
    leg_b_symbol: str
    data_status: str
    synthetic: bool
    lookback_window: int
    min_history_obs: int
    summary: Dict[str, Any]
    points_count: int
    points: List[PairSpreadPoint]


# --- Helpers ---

def _get_db_connection() -> Optional[duckdb.DuckDBPyConnection]:
    if _DB_PATH.exists():
        try:
            return duckdb.connect(str(_DB_PATH), read_only=True)
        except Exception:
            return None
    return None


def _get_purity_and_basis(symbol: str) -> tuple[float, float, str]:
    if symbol not in _contracts_config.contracts:
        raise ValueError(f"Unknown contract symbol: {symbol}")
    spec = _contracts_config.contracts[symbol]
    purity = spec.purity.value if hasattr(spec.purity, "value") else float(spec.purity)
    quote_basis = spec.quote_basis_g.value if hasattr(spec.quote_basis_g, "value") else float(spec.quote_basis_g)
    # Research fallback for disputed GOLDGUINEA if purity is null
    if purity is None:
        purity = 0.999
        status = "DISPUTED"
    else:
        status = spec.purity.status.value if hasattr(spec.purity.status, "value") else str(spec.purity.status)
    return float(purity), float(quote_basis), status


def _filter_by_range(points: List[Any], range_str: str) -> List[Any]:
    if not points or range_str.upper() == "ALL":
        return points
    
    last_date = datetime.strptime(points[-1].time if hasattr(points[-1], "time") else points[-1]["time"], "%Y-%m-%d").date()
    days_map = {
        "1W": 7,
        "1M": 30,
        "3M": 90,
        "6M": 180,
        "1Y": 365,
    }
    days = days_map.get(range_str.upper())
    if not days:
        return points
    cutoff = last_date - timedelta(days=days)
    return [
        p for p in points
        if datetime.strptime(p.time if hasattr(p, "time") else p["time"], "%Y-%m-%d").date() >= cutoff
    ]


# --- Contract OHLCV & Price Parity Series ---

@chart_router.get("/contract/{symbol}", response_model=ContractSeriesResponse)
def get_contract_chart(
    symbol: str,
    time_range: str = Query("ALL", alias="range", description="Time range: 1W, 1M, 3M, 6M, 1Y, ALL"),
) -> ContractSeriesResponse:
    """Retrieve OHLCV candle and normalized price parity series for a single contract."""
    symbol = symbol.upper()
    if symbol not in ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"]:
        raise HTTPException(status_code=400, detail=f"Unsupported symbol '{symbol}'. Must be one of GOLDM, GOLDTEN, GOLDGUINEA, GOLDPETAL.")

    purity, quote_basis, purity_status = _get_purity_and_basis(symbol)

    con = _get_db_connection()
    raw_rows: List[tuple] = []
    if con:
        try:
            # Query front or active contracts by date
            query = """
            SELECT 
                dp.trade_date,
                dp.open,
                dp.high,
                dp.low,
                dp.close,
                dp.settlement,
                dp.volume,
                dp.open_interest,
                dp.price_used,
                dp.price_quality,
                dp.quality_reason
            FROM daily_price dp
            JOIN contract c ON dp.contract_id = c.contract_id
            WHERE c.symbol = ?
            ORDER BY dp.trade_date ASC
            """
            raw_rows = con.execute(query, [symbol]).fetchall()
        finally:
            con.close()

    points: List[CandlePoint] = []

    if raw_rows:
        data_status = "VERIFIED_REAL"
        synthetic = False
        # Aggregate to one record per trade date (selecting highest volume if multiple expiries)
        seen_dates: Dict[str, tuple] = {}
        for r in raw_rows:
            t_date = str(r[0])
            vol = r[6] or 0
            if t_date not in seen_dates or vol > (seen_dates[t_date][6] or 0):
                seen_dates[t_date] = r

        for t_date in sorted(seen_dates.keys()):
            r = seen_dates[t_date]
            close_px = float(r[4] or r[8] or 0.0)
            norm_px = normalize_contract_price(
                price_used=close_px,
                symbol=symbol,
                contracts_config=_contracts_config,
                purity_override=0.999 if purity_status == "DISPUTED" else None,
            )
            points.append(
                CandlePoint(
                    time=t_date,
                    open=float(r[1] or close_px),
                    high=float(r[2] or close_px),
                    low=float(r[3] or close_px),
                    close=close_px,
                    volume=int(r[6] or 0),
                    open_interest=int(r[7] or 0),
                    raw_price=close_px,
                    normalized_price=round(norm_px, 2),
                    price_quality=str(r[9] or "OK"),
                    quality_reason=str(r[10]) if r[10] else None,
                )
            )
    else:
        # Calibrated baseline fixtures for development/testing if no raw database exists
        data_status = "SYNTHETIC_FIXTURE"
        synthetic = True
        base_spot = 120500.0
        # Quote basis scale
        scale_factor = (quote_basis / 10.0) * (purity / 0.999)
        base_price = base_spot * scale_factor

        start_date = date(2026, 8, 1)
        for i in range(65):
            curr_date = start_date + timedelta(days=i)
            if curr_date.weekday() >= 5:  # skip weekends
                continue
            noise = math.sin(i * 0.15) * 450.0 + (i * 12.0)
            close_px = round(base_price + (noise * scale_factor), 2)
            high_px = round(close_px + (120.0 * scale_factor), 2)
            low_px = round(close_px - (110.0 * scale_factor), 2)
            open_px = round(close_px - (20.0 * scale_factor), 2)
            norm_px = normalize_contract_price(
                price_used=close_px,
                symbol=symbol,
                contracts_config=_contracts_config,
                purity_override=0.999 if purity_status == "DISPUTED" else None,
            )
            points.append(
                CandlePoint(
                    time=curr_date.isoformat(),
                    open=open_px,
                    high=high_px,
                    low=low_px,
                    close=close_px,
                    volume=150 + (i * 2),
                    open_interest=450 + (i * 5),
                    raw_price=close_px,
                    normalized_price=round(norm_px, 2),
                    price_quality="OK",
                    quality_reason=None,
                )
            )

    filtered = _filter_by_range(points, time_range)
    return ContractSeriesResponse(
        symbol=symbol,
        quote_basis_g=quote_basis,
        purity=purity,
        purity_status=purity_status,
        data_status=data_status,
        synthetic=synthetic,
        points_count=len(filtered),
        points=filtered,
    )


# --- Cross-Contract Pair Spread & Z-Score Deviation Series ---

@chart_router.get("/pair/{pair_name}", response_model=PairSeriesResponse)
def get_pair_chart(
    pair_name: str,
    time_range: str = Query("ALL", alias="range", description="Time range: 1W, 1M, 3M, 6M, 1Y, ALL"),
    lookback: int = Query(60, ge=10, le=250, description="Rolling window lookback in trade sessions"),
    min_history: int = Query(30, ge=5, le=100, description="Minimum sessions required for Z-score calculation"),
) -> PairSeriesResponse:
    """Retrieve dual-contract normalized price comparison, log spread, rolling Bollinger bands, and Z-scores."""
    # Normalize pair string: e.g. "GOLDTEN_GOLDGUINEA" or "GOLDTEN-GOLDGUINEA"
    clean_pair = pair_name.replace("-", "_").upper()
    parts = clean_pair.split("_")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid pair format. Expected format: SYMBOL1_SYMBOL2 (e.g. GOLDTEN_GOLDGUINEA)")

    sym_a, sym_b = parts[0], parts[1]
    for s in [sym_a, sym_b]:
        if s not in ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"]:
            raise HTTPException(status_code=400, detail=f"Invalid symbol '{s}' in pair.")

    # Fetch individual series
    ser_a = get_contract_chart(sym_a, time_range="ALL")
    ser_b = get_contract_chart(sym_b, time_range="ALL")

    # Map by time
    map_a = {p.time: p for p in ser_a.points}
    map_b = {p.time: p for p in ser_b.points}

    common_dates = sorted(set(map_a.keys()).intersection(set(map_b.keys())))

    # In case the common dates in real DB are small (e.g. 5 days from sample), synthesize extended timeline
    is_synthetic = ser_a.synthetic or ser_b.synthetic or len(common_dates) < 30
    points: List[PairSpreadPoint] = []
    historical_spreads: List[float] = []

    # If we need extended series for robust 60-day lookback demonstrations
    if is_synthetic and len(common_dates) < 60:
        base_spot = 120500.0
        purity_a, basis_a, _ = _get_purity_and_basis(sym_a)
        purity_b, basis_b, _ = _get_purity_and_basis(sym_b)
        factor_a = (basis_a / 10.0) * (purity_a / 0.999)
        factor_b = (basis_b / 10.0) * (purity_b / 0.999)

        start_date = date(2026, 7, 1)
        simulated_points: List[PairSpreadPoint] = []
        sim_spreads: List[float] = []

        for i in range(85):
            curr_date = start_date + timedelta(days=i)
            if curr_date.weekday() >= 5:
                continue

            # Deterministic relative-value cycle:
            # Baseline mean spread ~ 0.00020 with occasional excursion reaching +2.45 sigma
            t_str = curr_date.isoformat()
            cycle = math.sin(i * 0.12) * 0.0006
            # Plant an anomaly excursion around day 75 (matching the Sept 18 alert fixture)
            spike = 0.0012 if (70 <= i <= 75) else 0.0
            log_spread_val = 0.00020 + cycle + spike

            norm_a_val = base_spot * (1.0 + (log_spread_val / 2.0))
            norm_b_val = base_spot * (1.0 - (log_spread_val / 2.0))

            raw_a_val = norm_a_val * factor_a
            raw_b_val = norm_b_val * factor_b

            # Compute rolling spread strictly through t-1
            spread_res = compute_spread(
                norm_a=norm_a_val,
                norm_b=norm_b_val,
                carry_adj=0.00082,  # standard 5-day curve carry at 6.5%
                history=sim_spreads,
                lookback_window=lookback,
                min_history_obs=min_history,
                symbol_a=sym_a,
                symbol_b=sym_b,
            )

            roll_upper = (spread_res.roll_mean + 2.0 * spread_res.roll_std) if (spread_res.roll_mean is not None and spread_res.roll_std is not None) else None
            roll_lower = (spread_res.roll_mean - 2.0 * spread_res.roll_std) if (spread_res.roll_mean is not None and spread_res.roll_std is not None) else None

            # Determine alert status
            z = spread_res.zscore
            if z is not None and abs(z) >= 2.0:
                pt_status = "ALERT"
                is_alert = True
            elif z is not None:
                pt_status = "QUIET"
                is_alert = False
            else:
                pt_status = "WARMUP"
                is_alert = False

            simulated_points.append(
                PairSpreadPoint(
                    time=t_str,
                    raw_a=round(raw_a_val, 2),
                    raw_b=round(raw_b_val, 2),
                    norm_a=round(norm_a_val, 2),
                    norm_b=round(norm_b_val, 2),
                    raw_diff=round(raw_a_val - raw_b_val, 2),
                    norm_diff=round(norm_a_val - norm_b_val, 2),
                    log_spread_raw=round(spread_res.log_spread_raw, 6),
                    carry_adj=round(spread_res.carry_adj, 6),
                    log_spread_adj=round(spread_res.log_spread_adj, 6),
                    roll_mean=round(spread_res.roll_mean, 6) if spread_res.roll_mean is not None else None,
                    roll_upper=round(roll_upper, 6) if roll_upper is not None else None,
                    roll_lower=round(roll_lower, 6) if roll_lower is not None else None,
                    roll_std=round(spread_res.roll_std, 6) if spread_res.roll_std is not None else None,
                    zscore=round(z, 2) if z is not None else None,
                    rich_leg=spread_res.rich_leg,
                    status=pt_status,
                    is_alert=is_alert,
                    quality_a="OK",
                    quality_b="OK",
                )
            )
            sim_spreads.append(spread_res.log_spread_adj)

        points = simulated_points
        data_status = "SYNTHETIC_FIXTURE"
        synthetic = True
    else:
        # Use strictly real synchronized dates
        for t_date in common_dates:
            pa = map_a[t_date]
            pb = map_b[t_date]
            
            # Carry adjustment (assumed standard or curve)
            carry_adj = 0.00082

            spread_res = compute_spread(
                norm_a=pa.normalized_price,
                norm_b=pb.normalized_price,
                carry_adj=carry_adj,
                history=historical_spreads,
                lookback_window=lookback,
                min_history_obs=min_history,
                symbol_a=sym_a,
                symbol_b=sym_b,
            )

            roll_upper = (spread_res.roll_mean + 2.0 * spread_res.roll_std) if (spread_res.roll_mean is not None and spread_res.roll_std is not None) else None
            roll_lower = (spread_res.roll_mean - 2.0 * spread_res.roll_std) if (spread_res.roll_mean is not None and spread_res.roll_std is not None) else None

            z = spread_res.zscore
            if z is not None and abs(z) >= 2.0:
                pt_status = "ALERT"
                is_alert = True
            elif z is not None:
                pt_status = "QUIET"
                is_alert = False
            else:
                pt_status = "WARMUP"
                is_alert = False

            points.append(
                PairSpreadPoint(
                    time=t_date,
                    raw_a=pa.raw_price,
                    raw_b=pb.raw_price,
                    norm_a=pa.normalized_price,
                    norm_b=pb.normalized_price,
                    raw_diff=round(pa.raw_price - pb.raw_price, 2),
                    norm_diff=round(pa.normalized_price - pb.normalized_price, 2),
                    log_spread_raw=round(spread_res.log_spread_raw, 6),
                    carry_adj=round(spread_res.carry_adj, 6),
                    log_spread_adj=round(spread_res.log_spread_adj, 6),
                    roll_mean=round(spread_res.roll_mean, 6) if spread_res.roll_mean is not None else None,
                    roll_upper=round(roll_upper, 6) if roll_upper is not None else None,
                    roll_lower=round(roll_lower, 6) if roll_lower is not None else None,
                    roll_std=round(spread_res.roll_std, 6) if spread_res.roll_std is not None else None,
                    zscore=round(z, 2) if z is not None else None,
                    rich_leg=spread_res.rich_leg,
                    status=pt_status,
                    is_alert=is_alert,
                    quality_a=pa.price_quality,
                    quality_b=pb.price_quality,
                )
            )
            historical_spreads.append(spread_res.log_spread_adj)

        data_status = "VERIFIED_REAL"
        synthetic = False

    filtered_points = _filter_by_range(points, time_range)
    latest = filtered_points[-1] if filtered_points else None

    summary = {
        "latest_date": latest.time if latest else None,
        "latest_zscore": latest.zscore if latest else None,
        "latest_norm_diff": latest.norm_diff if latest else None,
        "latest_log_spread_adj": latest.log_spread_adj if latest else None,
        "rich_leg": latest.rich_leg if latest else None,
        "status": latest.status if latest else "QUIET",
        "has_active_alert": any(p.is_alert for p in filtered_points[-5:]) if filtered_points else False,
    }

    return PairSeriesResponse(
        pair_name=f"{sym_a}_{sym_b}",
        leg_a_symbol=sym_a,
        leg_b_symbol=sym_b,
        data_status=data_status,
        synthetic=synthetic,
        lookback_window=lookback,
        min_history_obs=min_history,
        summary=summary,
        points_count=len(filtered_points),
        points=filtered_points,
    )
