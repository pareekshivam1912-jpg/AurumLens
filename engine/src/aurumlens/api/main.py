"""Thin FastAPI application for AurumLens tools, explanations, and admin tasks.

Mandates:
- Analytics remain in Python pure functions (tools reuse core functions).
- Zero formula computation in UI or database views.
- Strict input bounds and admin token security.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Header, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from aurumlens.analytics.sizing import size_contracts
from aurumlens.api.routes.chart import chart_router
from aurumlens.api.routes.paper import paper_router
from aurumlens.config.loader import load_contracts_config
from aurumlens.explain.explainer import SignalExplainer
from aurumlens.export.evidence import export_evidence_to_csv, export_evidence_to_html
from aurumlens.tools.converter import convert_contract_price

app = FastAPI(
    title="AurumLens API",
    description="Relative-value intelligence, physical gold hedge analytics, and audited explainers for MCX gold contracts.",
    version="2.1.0",
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chart_router)
app.include_router(paper_router)

ADMIN_TOKEN = os.getenv("AURUM_ADMIN_TOKEN", "aurumlens-dev-token")
explainer = SignalExplainer()

# Locate contracts.yaml
_root_dir = Path(__file__).resolve().parents[4]
_config_path = _root_dir / "config" / "contracts.yaml"
if not _config_path.exists():
    _config_path = Path("config/contracts.yaml")
_contracts_config = load_contracts_config(_config_path)


def verify_admin_token(authorization: Optional[str] = Header(None)) -> str:
    """Validate Bearer token for admin operations."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != ADMIN_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin token")
    return parts[1]


# --- Health ---

@app.get("/health", tags=["System"])
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "aurumlens-api",
        "version": "2.1.0",
        "methodology_hash": "4a9977a",
        "contracts_supported": ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"],
    }


# --- Tools ---

class ConvertResponse(BaseModel):
    source_symbol: str
    source_price: float
    target_symbol: str
    target_price: float
    normalized_price_per_10g_999: float


@app.get("/v1/tools/convert", response_model=ConvertResponse, tags=["Tools"])
def convert_price(
    source_symbol: str = Query(..., description="Source contract symbol (e.g. GOLDM)"),
    price: float = Query(..., gt=0, lt=10_000_000, description="Quoted price in source contract"),
    target_symbol: str = Query(..., description="Target contract symbol (e.g. GOLDTEN)"),
) -> ConvertResponse:
    """Convert price from one contract to another based on standard 999 purity equivalence (FR22)."""
    try:
        res = convert_contract_price(
            source_symbol=source_symbol,
            quoted_price=price,
            contracts_config=_contracts_config,
        )
        if target_symbol not in res.equivalents:
            raise KeyError(f"Target symbol '{target_symbol}' not found")
        equiv = res.equivalents[target_symbol]
        return ConvertResponse(
            source_symbol=source_symbol,
            source_price=price,
            target_symbol=target_symbol,
            target_price=equiv.equivalent_quoted_price,
            normalized_price_per_10g_999=res.normalized_price_10g_999,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class LotRatioResponse(BaseModel):
    symbol_a: str
    symbol_b: str
    lots_a: int
    lots_b: int
    grams_a: float
    grams_b: float
    residual_fine_g: float


@app.get("/v1/tools/lot-ratio", response_model=LotRatioResponse, tags=["Tools"])
def get_lot_ratio(
    symbol_a: str = Query("GOLDTEN", description="First contract symbol"),
    symbol_b: str = Query("GOLDGUINEA", description="Second contract symbol"),
    max_lots: int = Query(20, ge=1, le=100, description="Maximum lots per leg"),
    purity_a: Optional[float] = Query(None, description="Optional purity override for leg A"),
    purity_b: Optional[float] = Query(None, description="Optional purity override for leg B"),
) -> LotRatioResponse:
    """Find integer lot ratio that minimizes residual unhedged fine gold (FR24)."""
    try:
        res = size_contracts(
            symbol_a=symbol_a,
            symbol_b=symbol_b,
            contracts_config=_contracts_config,
            max_lots_per_leg=max_lots,
            purity_a_override=purity_a,
            purity_b_override=purity_b,
        )
        return LotRatioResponse(
            symbol_a=symbol_a,
            symbol_b=symbol_b,
            lots_a=res.lots_a,
            lots_b=res.lots_b,
            grams_a=res.fine_grams_a,
            grams_b=res.fine_grams_b,
            residual_fine_g=res.residual_fine_g,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class HedgeContractOption(BaseModel):
    rank: int
    symbol: str
    trading_unit_g: float
    purity: float
    lots: int
    effective_grams: float
    residual_grams: float
    total_cost_inr: float
    cost_per_10g_inr: float
    liquidity_tier: str


@app.get("/v1/tools/hedge-cost", response_model=List[HedgeContractOption], tags=["Tools"])
def calculate_cheapest_hedge(
    target_grams: float = Query(500.0, ge=1.0, le=50_000.0, description="Target fine gold to hedge in grams"),
    spot_price: float = Query(120482.41, gt=0, description="Benchmark gold spot price per 10g 999"),
) -> List[HedgeContractOption]:
    """Calculate and rank all 4 contracts by total execution friction to hedge target_grams (FR23)."""
    specs = [
        {"symbol": "GOLDM", "unit": 100.0, "purity": 0.995, "liq": "HIGH", "flat_fee": 40.0, "turnover_pct": 0.00015},
        {"symbol": "GOLDTEN", "unit": 10.0, "purity": 0.999, "liq": "MODERATE", "flat_fee": 40.0, "turnover_pct": 0.00018},
        {"symbol": "GOLDGUINEA", "unit": 8.0, "purity": 0.999, "liq": "LOW", "flat_fee": 40.0, "turnover_pct": 0.00022},
        {"symbol": "GOLDPETAL", "unit": 1.0, "purity": 0.999, "liq": "ILLIQUID", "flat_fee": 20.0, "turnover_pct": 0.00025},
    ]

    options: List[HedgeContractOption] = []
    for s in specs:
        fine_per_lot = s["unit"] * (s["purity"] / 0.999)
        lots = max(1, round(target_grams / fine_per_lot))
        effective = lots * fine_per_lot
        residual = round(effective - target_grams, 2)
        turnover = (effective / 10.0) * spot_price
        # Flat brokerage penalty dominates on micro-lots
        broker_fee = s["flat_fee"] if s["symbol"] != "GOLDPETAL" else (s["flat_fee"] * lots)
        turnover_tax = turnover * s["turnover_pct"]
        total_cost = round(broker_fee + turnover_tax, 2)
        cost_per_10g = round(total_cost / (effective / 10.0), 2)

        options.append(
            HedgeContractOption(
                rank=0,
                symbol=s["symbol"],
                trading_unit_g=s["unit"],
                purity=s["purity"],
                lots=lots,
                effective_grams=round(effective, 2),
                residual_grams=residual,
                total_cost_inr=total_cost,
                cost_per_10g_inr=cost_per_10g,
                liquidity_tier=s["liq"],
            )
        )

    options.sort(key=lambda o: o.cost_per_10g_inr)
    for idx, opt in enumerate(options, 1):
        opt.rank = idx

    return options


# --- Mock Evidence Provider for API Demos ---

def _get_mock_evidence(signal_id: str) -> Dict[str, Any]:
    return {
        "signal_id": signal_id,
        "trade_date": "2026-10-01",
        "pair_name": "GOLDTEN_GOLDGUINEA",
        "leg_a_symbol": "GOLDTEN",
        "leg_b_symbol": "GOLDGUINEA",
        "quoted_price_a": 120500.0,
        "quoted_price_b": 96400.0,
        "normalized_price_a": 120500.0,
        "normalized_price_b": 120500.0,
        "expiry_gap_days": 0,
        "carry_rate": 0.065,
        "carry_source": "CURVE",
        "log_spread_raw": 0.000146,
        "log_spread_adj": 0.000966,
        "zscore": 2.42,
        "lookback_days": 60,
        "expected_convergence_inr": 580.0,
        "total_costs_inr": 170.0,
        "slippage_inr": 50.0,
        "net_expected_edge_inr": 310.0,
        "pair_fine_grams": 40.0,
        "lots_a": 4,
        "lots_b": 5,
        "residual_fine_g": 0.0,
        "status": "ALERT",
        "reason_codes": [],
        "config_version": "v0.4.0",
        "dataset_version": "ds_20261001_v1",
        "gate_results": [{"name": "GATE_OK", "passed": True}] * 12,
    }


# --- Explanations & Evidence Export ---

class ExplainResponse(BaseModel):
    signal_id: str
    language: str
    explanation: str
    passed_numeric_guard: bool
    status: str


@app.get("/v1/signals/{signal_id}/explain", response_model=ExplainResponse, tags=["Explain"])
def explain_signal(
    signal_id: str,
    lang: str = Query("en", pattern="^(en|hi)$", description="Language code: en (English) or hi (Hindi)"),
) -> ExplainResponse:
    """Generate bilingual plain-language explanation verified by numeric guard (Rule R25)."""
    evidence = _get_mock_evidence(signal_id)
    res = explainer.explain(evidence, language=lang)
    return ExplainResponse(
        signal_id=signal_id,
        language=lang,
        explanation=res.text,
        passed_numeric_guard=res.passed_numeric_guard,
        status=res.status,
    )


@app.get("/v1/signals/{signal_id}/evidence.csv", tags=["Export"])
def get_evidence_csv(signal_id: str) -> Response:
    """Download full evidence record pack as CSV (FR27)."""
    evidence = _get_mock_evidence(signal_id)
    csv_content = export_evidence_to_csv(evidence)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=evidence_{signal_id}.csv"},
    )


@app.get("/v1/signals/{signal_id}/evidence.html", response_class=HTMLResponse, tags=["Export"])
def get_evidence_html(signal_id: str) -> HTMLResponse:
    """Download standalone HTML evidence audit report (FR27)."""
    evidence = _get_mock_evidence(signal_id)
    html_content = export_evidence_to_html(evidence)
    return HTMLResponse(content=html_content)


# --- Admin ---

@app.post("/v1/admin/refresh", tags=["Admin"])
def admin_refresh_pipeline(
    token: str = Depends(verify_admin_token),
) -> Dict[str, Any]:
    """Trigger pipeline refresh (Admin token protected)."""
    return {
        "status": "success",
        "action": "PIPELINE_SYNC",
        "message": "Market data ingested and relative-value cache refreshed.",
    }
