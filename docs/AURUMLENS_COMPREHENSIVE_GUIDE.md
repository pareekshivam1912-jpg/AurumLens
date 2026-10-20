# AurumLens — Comprehensive System & User Guide v2.1

> **Analytics only — not investment advice.**  
> Institutional Relative-Value Intelligence, Risk-Gated Arbitrage Detection, and Physical Gold Hedge Analytics for Multi-Contract MCX Gold Derivatives.

---

## Table of Contents
1. [Executive Summary & Product Boundaries](#1-executive-summary--product-boundaries)
2. [The Core Quant Problem: Why AurumLens?](#2-the-core-quant-problem-why-aurumlens)
3. [End-to-End System Architecture](#3-end-to-end-system-architecture)
4. [Mathematical & Analytical Methodologies](#4-mathematical--analytical-methodologies)
5. [Complete Functional Guide: The 9 Dashboard Screens](#5-complete-functional-guide-the-9-dashboard-screens)
6. [API Reference: FastAPI Microservice](#6-api-reference-fastapi-microservice)
7. [Step-by-Step User & Developer Guide](#7-step-by-step-user--developer-guide)
8. [Live Demo Walkthrough & Pitch Playbook](#8-live-demo-walkthrough--pitch-playbook)
9. [Regulatory Compliance & Facts Register](#9-regulatory-compliance--facts-register)

---

## 1. Executive Summary & Product Boundaries

**AurumLens** is an institutional quantitative intelligence system for India's domestic gold futures market on the Multi Commodity Exchange (MCX). It monitors relative mispricings between different MCX gold futures contracts, isolates true structural discrepancies from carry friction and taxes, runs every opportunity through an **12-Gate Waterfall Evaluator**, and equips jewelers and bullion desks with pre-trade hedging cost calculators.

### Product Boundaries & Safeguards (Rule R1–R5)
- **No Direction Prediction:** AurumLens does NOT predict whether gold will go up or down. It evaluates relative cross-contract value only.
- **Universe:** 4 MCX gold contracts:
  - **GOLDM** (100g trading unit, 10g quote basis, 995 purity)
  - **GOLDTEN** (10g trading unit, 10g quote basis, 999 purity)
  - **GOLDGUINEA** (8g trading unit, 8g quote basis, 999 purity — *disputed spec*)
  - **GOLDPETAL** (1g trading unit, 1g quote basis, 999 purity)
- **Core Signal Output:** Binary **ALERT** or **QUIET**, accompanied by an immutable Evidence Record and the Nearest-Miss analysis.
- **Zero Real-Money Execution in MVP:** Live execution is not permitted without regulatory licensing; simulated paper execution is isolated behind an adapter.
- **No Client-Side Computation:** The Next.js frontend and SQL views never compute financial math. All analytics are pure, version-controlled Python functions.

---

## 2. The Core Quant Problem: Why AurumLens?

In theory, "gold is gold." In practice on MCX, comparing raw quoted prices is fatal:
1. **Purity Differences:** GOLDM is priced on 995 fineness (23.88 carats), whereas GOLDTEN, GOLDGUINEA, and GOLDPETAL are priced on 999 fineness (24 carats).
2. **Quote Basis Distortions:** GOLDM and GOLDTEN quote in ₹/10g; GOLDGUINEA quotes in ₹/8g; GOLDPETAL quotes in ₹/1g.
3. **Calendar Carry Friction:** Contracts trade on different expiry cycles (e.g. October vs November). Contango/backwardation creates natural price gaps that are not arbitrage.
4. **Asymmetric Indian Transaction Costs:**
   - Commodities Transaction Tax (CTT): 0.01% on **sell side only**.
   - Stamp Duty: 0.002% on **buy side only**.
   - GST: 18% applied strictly to broker + exchange + SEBI turnover fees (not on tax).
   - Flat Brokerage Dominance: A flat ₹20/order fee destroys profitability on micro-lots (e.g. GOLDPETAL requires 500 separate lots to hedge 500g, incurring a +828% fee penalty).

AurumLens solves this entire matrix in real time.

---

## 3. End-to-End System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          1. DATA INGESTION                             │
│  MCX Daily Bhavcopy (Legacy format + Modern CDP JSON/CSV)              │
│  Hash Verification (SHA-256) ──▶ Immutable Raw Parquet Snapshots      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                       2. PYTHON QUANT ENGINE                           │
│  ┌───────────────────────┐  ┌───────────────────────┐                 │
│  │ Price Normalization   │  │ Expiry Matching       │                 │
│  │ (₹/10g 999 Parity)    │  │ (Smallest Calendar Gap│                 │
│  └───────────┬───────────┘  └───────────┬───────────┘                 │
│              └─────────────┬────────────┘                             │
│                            ▼                                          │
│  ┌──────────────────────────────────────────────────┐                 │
│  │ Carry-Adjusted Log Spread Engine                 │                 │
│  │ s_t = ln(P_A) - ln(P_B) + r_carry * (T_B-T_A)/365│                 │
│  └─────────────────────────┬────────────────────────┘                 │
│                            ▼                                          │
│  ┌──────────────────────────────────────────────────┐                 │
│  │ 12-Gate Waterfall Risk & Economic Evaluator      │                 │
│  │ (Spec, Quality, Expiry, History, Z, 4xLiq, Cost) │                 │
│  └───────────┬──────────────────────────┬───────────┘                 │
│              │ ALERT                    │ QUIET                       │
│              ▼                          ▼                             │
│       Evidence Record             Nearest Miss                        │
└──────────────┬──────────────────────────┬─────────────────────────────┘
               │                          │
┌──────────────▼──────────────────────────▼─────────────────────────────┐
│                 3. PERSISTENCE & STORAGE (SUPABASE)                    │
│  PostgreSQL with Row Level Security (RLS)                             │
│  Read-Only for Browser Client (Anon Key) • Write only by Python Engine│
└──────────────────────────────┬────────────────────────────────────────┘
                               │
       ┌───────────────────────┴───────────────────────┐
       ▼                                               ▼
┌──────────────────────────────┐        ┌──────────────────────────────┐
│       4. FASTAPI SERVICE     │        │     5. NEXT.JS 14 FRONTEND   │
│  /v1/tools/convert           │        │  9 Stitch Fintech Screens    │
│  /v1/tools/lot-ratio         │        │  Tailwind CSS • Realtime     │
│  /v1/tools/hedge-cost        │        │  Interactive Demo Scenarios  │
│  /v1/explain (Bilingual)     │        │  Zero Client-Side Math       │
└──────────────────────────────┘        └──────────────────────────────┘
```

---

## 4. Mathematical & Analytical Methodologies

### 4.1 Price Normalization (Rule R16)
Every quoted price is standardized to **₹ per 10 grams of 999 fine gold**:
$$P_{\text{norm}} = P_{\text{quoted}} \times \left(\frac{10}{\text{quote\_basis\_g}}\right) \times \left(\frac{0.999}{\text{purity}}\right)$$

*Key Verification (Purity Direction Rule):* Normalizing sub-999 purity (such as GOLDM @ 995) must scale the price **UPWARD**:
$$\text{₹}120,000 \times 1.0 \times \left(\frac{0.999}{0.995}\right) = \text{₹}120,482.41$$

### 4.2 Expiry Matching (Rule R17)
Pairs active contracts by minimizing absolute calendar gap $|T_A - T_B|$, strictly requiring $|T_A - T_B| \le \text{max\_expiry\_gap\_days}$ (default 35 days). Ties break toward nearer expiry, then higher combined Open Interest.

### 4.3 Carry Adjustment (Rule R18)
$$r_{\text{curve}} = \frac{\ln(P_{\text{far}} / P_{\text{near}})}{(T_{\text{far}} - T_{\text{near}}) / 365}$$
If two valid expiries exist, AurumLens computes market-implied curve carry. If not, it falls back to configured rate $r_{\text{fallback}}$ and explicitly flags `carry_source = FALLBACK`.

### 4.4 Adjusted Log Spread & Rolling Bands (Rule R18)
$$s_t = \ln(P_{A,\text{norm}}) - \ln(P_{B,\text{norm}}) + r \cdot \frac{T_B - T_A}{365}$$
$$z_t = \frac{s_t - \mu_{t-1}}{\sigma_{t-1}}$$
Scoring strictly uses history through $t-1$ (no look-ahead bias). Convergence is evaluated to rolling mean $\mu_{t-1}$, never to zero.

### 4.5 The 12-Gate Waterfall (Rule R20)
Every single gate is evaluated on every session. An anomaly score alone never alerts.
1. `SPEC_OK`: Contract specs verified official (or watermarked in research mode).
2. `DATA_QUALITY`: Neither contract's price is marked SUSPECT.
3. `EXPIRY_PAIR_VALID`: Expiry gap $\le 35$ calendar days.
4. `HISTORY_SUFFICIENT`: Observations in lookback window $\ge 30$.
5. `Z_SCORE_THRESHOLD`: $|z_t| \ge \text{entry\_z}$ (default 2.0).
6. `LIQUIDITY_VOLUME_A`: Leg A daily turnover $\ge 10$ lots.
7. `LIQUIDITY_VOLUME_B`: Leg B daily turnover $\ge 10$ lots.
8. `LIQUIDITY_OI_A`: Leg A Open Interest $\ge 50$ lots.
9. `LIQUIDITY_OI_B`: Leg B Open Interest $\ge 50$ lots.
10. `EXPIRY_SAFETY`: Both legs $> 5$ days prior to tender/delivery window.
11. `COST_HURDLE`: Expected convergence edge $> \text{Round-trip Costs} + \text{Slippage} + \text{Safety Buffer}$.
12. `DUPLICATE_CHECK`: No active open simulated alert on this pair.

### 4.6 Nearest-Miss Analysis (Rule R21, FR17)
When a pair evaluates to QUIET, AurumLens computes how close it was to alerting:
$$\text{Ratio}_i = \min\left(1.0, \frac{\text{Value}_i}{\text{Threshold}_i}\right)$$
Pairs are ranked lexicographically by $(\text{Gates Passed} \downarrow, \min \text{Failing Ratio} \downarrow)$.

---

## 5. Complete Functional Guide: The 9 Dashboard Screens

### Screen 1: Overview Dashboard (`/`)
- **Market State Pill:** Displays live institutional market regime (`QUIET` in green or `ALERT` in amber).
- **2×3 Pair Matrix:** Overview of all 6 possible pair combinations (GOLDTEN-GOLDM, GOLDTEN-GOLDGUINEA, etc.).
- **Nearest-Miss Card:** Live callout showing the closest inactive opportunity, how many gates passed, and what blocked it.
- **Realtime Banner:** Instant pop-up alert whenever an `INSERT` event occurs on the Supabase `signal` table.

### Screen 2: Pair Deep-Dive & 12-Gate Waterfall (`/pair-analysis`)
- **Interactive 3-Scenario Switcher:** Toggle instantly between:
  - *Date 1: Alert Day* (12/12 gates pass, z = +2.45).
  - *Date 2: Nearest Miss Day* (11/12 gates pass, z = +1.67 vs 2.0 hurdle).
  - *Date 3: Blocked Day* (Extreme z = +2.85, but blocked by 4 lots/day volume & 3-day tender expiry).
- **12-Gate Waterfall Table:** Detailed audit showing gate name, PASS/FAIL badge, measured value, threshold, margin, and reason code.
- **Carry & Spread Decomposition:** Side-by-side view of raw spread, carry adjustment, and normalized prices.
- **Itemized Friction Ledger:** Displays exact Indian statutory costs (Brokerage, Exchange, SEBI, CTT, Stamp Duty, GST).

### Screen 3: Walk-Forward Backtesting (`/backtest`)
- **Fold Visualizer:** Walk-forward expanding window simulation with strict holdout isolation.
- **Attribution Waterfall:** Gross P&L vs Round-Trip Friction vs Adverse Slippage vs Net Arbitrage P&L vs Residual Gold Delta.
- **Baseline Benchmarking:** Compares strategy performance against Buy-and-Hold and Seeded Random Entry.
- **Deflated Sharpe Ratio (DSR):** Computes Bailey & López de Prado (2014) haircut for selection bias across multi-parameter trials.

### Screen 4: Contract Horizon & Macro Calendar (`/calendar`)
- **Q4 Expiry Gantt Chart:** Visualizes rolling horizon across active contracts.
- **SEBI 5-Day Tender Warning Zone:** Highlights the mandatory pre-expiry physical delivery period where speculative positions are barred.
- **Macro Pins:** Annotates RBI Monetary Policy Committee meetings, US Non-Farm Payrolls, and Fed rate decisions.

### Screen 5: Alert Audit Ledger (`/alerts`)
- **Immutable Ledger:** Full audit trail stamped with `config_version` and `dataset_version`.
- **Slide-Over Evidence Pack:** Displays deep-dive audit trail with bilingual explanation in English and Hindi.
- **NumericGuard Protection:** Verified regex engine guaranteeing that LLM or template text can never alter financial figures.
- **One-Click Export:** Download evidence dossiers as CSV or standalone HTML reports.

### Screen 6: Physical Gold Hedge Tools (`/hedge-tools`)
- **Cheapest-to-Hedge (FR23):** Enter any target fine gold weight (e.g. 500g). The engine ranks all 4 contracts from lowest to highest total transaction friction and highlights the optimal vehicle.
- **Contract Parity Converter (FR22):** Select source contract and price; instantly computes normalized ₹/10g 999 parity across all 4 contracts.
- **Integer Lot Sizer (FR24):** Select Leg A and Leg B to find integer lot combinations that drive leftover unhedged gold to near zero.

### Screen 7: Data Health & Governance (`/data-health`)
- **Canonical Facts Register:** Displays official status of all contract specifications (`VERIFIED_OFFICIAL` vs `DISPUTED`).
- **SUSPECT Monitor:** Flags prices with low volume, wide close-settlement discrepancies, or stale feeds.
- **Ingestion Log:** SHA-256 integrity hashes for all raw source files.

### Screen 8: Methodology & Formulas (`/methodology`)
- Complete mathematical documentation of normalization, carry, Corwin-Schultz slippage, and waterfall logic.
- Pipeline DAG diagram.

### Screen 9: Paper Trading & Reversion Simulator (`/paper-trading`)
- Simulated forward paper execution with zero-duplicate guard.
- Tracks mark-to-market and half-life convergence.

---

## 6. API Reference: FastAPI Microservice

The FastAPI service runs on `http://localhost:8000` with interactive Swagger docs at `/docs`.

### Core System & Quantitative Endpoints
| Endpoint | Method | Description | Parameters |
|---|---|---|---|
| `/v1/health` | GET | Health & version status | None |
| `/v1/tools/convert` | GET | Cross-contract parity conversion (FR22) | `source_symbol`, `price`, `target_symbol` |
| `/v1/tools/lot-ratio` | GET | Integer lot sizing ratio (FR24) | `symbol_a`, `symbol_b`, `max_lots` |
| `/v1/tools/hedge-cost` | GET | Ranked cheapest-to-hedge calculator (FR23) | `target_grams`, `spot_price` |
| `/v1/signals/{id}/explain` | GET | Bilingual explanation with NumericGuard | `lang` (en/hi) |
| `/v1/signals/{id}/evidence.csv` | GET | Export evidence pack to CSV format | None |
| `/v1/signals/{id}/evidence.html` | GET | Export audited evidence report in standalone HTML | None |
| `/v1/admin/refresh` | POST | Trigger market data pipeline sync | Header: `Bearer <token>` |

### Interactive Charting Suite Endpoints (Phase 1)
| Endpoint | Method | Description | Parameters |
|---|---|---|---|
| `/v1/chart/contract/{symbol}` | GET | OHLCV candles & normalized parity prices | `symbol`, `range` (1W, 1M, 3M, 6M, 1Y, ALL) |
| `/v1/chart/pair/{pair_name}` | GET | Cross-contract log spreads, Bollinger bands ($\mu \pm 2\sigma$), and Z-scores | `pair_name`, `range`, `lookback`, `min_history` |

### Paper Portfolio & Risk Simulation Endpoints (Phase 3)
| Endpoint | Method | Description | Parameters |
|---|---|---|---|
| `/v1/paper/portfolio` | GET | Full portfolio ledger, MTM equity, and margin | None |
| `/v1/paper/stage` | POST | Stage candidate paper trade (Phase 1 of two-phase flow) | `OrderStageRequest` |
| `/v1/paper/confirm` | POST | Confirm & execute staged trade (Phase 2 of two-phase flow) | `OrderConfirmRequest` |
| `/v1/paper/close` | POST | Close position with exit reason code | `PositionCloseRequest` |
| `/v1/paper/simulate-risk` | POST | What-If risk stress runner under spot/spread shocks | `RiskStressRequest` |

### Unified AurumLens AI Conversational Endpoints (Phase 4)
| Endpoint | Method | Description | Parameters |
|---|---|---|---|
| `/v1/chat` | POST | Conversational assistant with NumericGuard and tool dispatching | `ChatRequest` (message, language, session_id) |
| `/v1/chat/suggestions` | GET | Quick prompt starter chips | None |

---

## 7. Step-by-Step User & Developer Guide

### Prerequisites
- **Python 3.12+** (configured in PATH)
- **Node.js 18+** & `npm`
- **Docker** (optional, for local Supabase)

### Method A: One-Click Prototype Launch (Recommended)
Simply double-click:
```bash
run_demo.bat
```
*(Or in PowerShell: `./run_demo.ps1`)*

This script:
1. Launches the FastAPI Python engine on `http://localhost:8000`
2. Launches the Next.js frontend on `http://localhost:3000`
3. Opens your default web browser to the prototype dashboard

### Method B: Manual Startup

**Terminal 1 — Python Engine API:**
```bash
cd engine
$env:PYTHONPATH="src"
python -m uvicorn aurumlens.api.main:app --port 8000 --reload
```

**Terminal 2 — Next.js Frontend:**
```bash
cd web
npm run dev
```

### Running System Verification & Rehearsals

```bash
# Run the 134-test Python test suite (~6s)
python -m pytest -q

# Run repository security & credential leak scanner
python scripts/scan_secrets.py

# Run full 27-requirement PRD compliance audit
python scripts/verify_fr_checklist.py

# Run the full 3-round automated offline rehearsal runner
python scripts/rehearse_demo.py
```

---

## 8. Live Demo Walkthrough & Pitch Playbook

### The 3-Minute Pitch Script

1. **The Hook (30s):**
   > *"Gold is gold — so why do four MCX gold contracts trade at wildly different prices? A jeweler holding physical inventory or a bullion trader trying to hedge has no simple way to compare them. Normalizing for purity, quote basis, carry, and asymmetric taxes is complex. That is why we built AurumLens."*

2. **The Normalization (30s):**
   > *Navigate to `/hedge-tools` → Parity Converter.*
   > *"We normalize everything into ₹ per 10g of 999-fine gold. When we enter ₹1,20,000 for GOLDM (995 purity), our engine proves that lower purity normalizes upward to ₹120,482.41."*

3. **The Evidence & 12-Gate Waterfall (45s):**
   > *Navigate to `/pair-analysis` → Click 'Date 1: Alert Day'.*
   > *"Here is an ALERT session. But an anomaly score alone NEVER triggers an alert. We evaluate 12 gates simultaneously: contract specs, data quality, expiry gap, history, z-score, 4 liquidity gates, tender expiry windows, and an economic hurdle. After deducting itemized brokerage, CTT, stamp duty, GST, and Corwin-Schultz slippage, we only alert when positive edge remains."*

4. **The Discipline: Anomaly Blocked (45s):**
   > *Click 'Date 3: Blocked Day'.*
   > *"Now look at this date. The z-score is massive at +2.85! A naive trading bot would buy aggressively. But AurumLens immediately flags it QUIET. Why? Leg A traded only 4 lots that day, and it sits just 3 days from physical tender. We protected the desk from an illiquid trap."*

5. **The Utility: Cheapest-to-Hedge (30s):**
   > *Navigate to `/hedge-tools` → Cheapest-to-Hedge.*
   > *"Finally, for physical gold businesses: enter '500 grams'. AurumLens instantly calculates the optimal vehicle. GOLDM offers the lowest friction at ₹22.40/10g, while GOLDPETAL suffers an 800% fee penalty due to flat ticket fee dominance. AurumLens is institutional relative-value intelligence for Indian gold."*

---

## 9. Regulatory Compliance & Facts Register

| Contract | Trading Unit | Quote Basis | Purity | Status | Note |
|---|---|---|---|---|---|
| **GOLDM** | 100g | 10g | 0.995 (995) | `VERIFIED_OFFICIAL` | High liquidity benchmark |
| **GOLDTEN** | 10g | 10g | 0.999 (999) | `VERIFIED_OFFICIAL` | 10g fine gold standard |
| **GOLDGUINEA** | 8g | 8g | 0.999 (999) | `DISPUTED` | Candidates: 0.995 vs 0.999; falls back to candidate in research mode |
| **GOLDPETAL** | 1g | 1g | 0.999 (999) | `VERIFIED_OFFICIAL` | 1g micro-lot; severe flat-brokerage drag |

**Compliance Disclaimer:**  
*AurumLens provides quantitative analytics only and does not constitute financial, investment, or legal advice. All derived calculations and backtests are simulated models subject to market risks.*
