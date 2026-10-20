# AurumLens — Product Requirements Document (PRD) v3.0

> **Version:** 3.0 · **Date:** 2026-10-20 · **Status:** Master Specification  
> **Supersedes:** PRD v2.0 · **Aligned with:** `prompt.md` Master Implementation Vision

---

## 1. Executive Summary & Product Vision

**AurumLens** is an institutional quantitative intelligence, relative-value analytics, and portfolio risk management platform designed for Multi Commodity Exchange (MCX) gold derivatives and related physical gold instruments.

Gold is chemically homogeneous, yet MCX gold contracts trade at divergent prices due to disparate lot sizes, differing delivery purities (995 vs 999), varying quote conventions, differing contract expiry dates, calendar carry structures, and asymmetric Indian statutory transaction taxes. 

AurumLens provides traders, bullion desks, and jewelry manufacturers with a transparent, data-backed platform that:
1. Standardizes all contracts onto a common physical basis (**₹ per 10 grams of 999 fine gold**).
2. Isolates true structural dislocations using an **12-Gate Waterfall Risk & Economic Evaluator**.
3. Delivers an **Interactive Charting Suite** comparing raw contracts, normalized analytical spreads, and Z-score deviation bands.
4. Manages hypothetical simulated portfolios with **Paper Trading and Stress Testing** ("what-if" risk analysis).
5. Provides **One Unified AI Chatbot ("AurumLens AI")** uniting trading education, signal explainability, market diagnostics, and portfolio risk management.

### Foundational Philosophy
- **Analytics Only — Not Investment Advice:** AurumLens does not predict market direction and never guarantees trading outcomes.
- **Paper Trading First:** No real-money broker order placement in initial releases.
- **Zero Hallucination:** Every price, signal, P&L metric, and risk score comes from deterministic backend engines, never from language model guesses.

---

## 2. Core Product Principles (Rule R1–R8)

1. **Data-backed, Not Hallucinated:** Prices, indicators, signals, positions, P&L, and risk metrics must originate exclusively from verified application data or deterministic calculations.
2. **Explainable Decisions:** Every signal record must display its underlying evidence, assumptions, thresholds, timestamps, and filter evaluations.
3. **Risk-First Design:** A high statistical Z-score is not automatically a trading signal. Liquidity, transaction costs, expiry tender rules, slippage, and basis risk must all pass gating thresholds.
4. **Clear Data Status:** All displayed data must be explicitly labeled as **Live**, **Delayed**, **Historical**, **Simulated**, or **Unavailable**. Demo data must never be presented as live market feeds.
5. **Paper Trading First:** All execution workflows operate strictly within a simulated paper-trading environment.
6. **One Assistant:** Trading education, signal explanation, market analysis, portfolio monitoring, and risk simulations must all be accessible through a single unified chatbot interface.
7. **Auditable Behavior:** Every calculation, signal decision, data-quality event, and simulated portfolio mutation must be traceable to versioned configs and immutable audit logs.
8. **No Guaranteed Outcomes:** The system strictly prohibits claims of guaranteed profit, certain reversals, or risk-free arbitrage.

---

## 3. Target Users & Personas

| Persona | Primary Needs & Use Cases | Key Features Used |
|---|---|---|
| **Active Commodity Traders** | Identifies whether cross-contract spread divergence exceeds round-trip friction and slippage; evaluates mean-reversion signals. | Interactive Chart, Signal Monitor, 12-Gate Waterfall, Paper Trading |
| **Jewelers & Physical Bullion Desks** | Seeks the cheapest contract to hedge physical inventory (e.g. 500g); calculates exact lot ratios and unhedged residual gold. | Hedge Tools (Cheapest-to-Hedge, Lot Sizer, Parity Converter) |
| **Prop & Quantitative Desks** | Requires walk-forward backtest integrity, itemized P&L attribution, Deflated Sharpe Ratio (DSR), and leak-free validation. | Backtest Engine, Trial Registry, Evidence Exporter (CSV/HTML) |
| **Market Learners & Analysts** | Desires clear educational explanations of calendar carry, basis, Z-scores, and reasons why candidate signals were rejected. | Unified AurumLens AI Chatbot, Methodology DAG |

---

## 4. Contract Universe & Market Scope

### 4.1 The 4 MCX Gold Futures Contracts
| Contract Symbol | Trading Unit | Quote Basis | Purity / Fineness | Expiry Cycle | Status in Facts Register |
|---|---|---|---|---|---|
| **GOLDM** (Gold Mini) | 100 grams | ₹ per 10 g | 0.995 (995 fineness) | 5th of contract month | `VERIFIED_OFFICIAL` |
| **GOLDTEN** | 10 grams | ₹ per 10 g | 0.999 (999 fineness) | Last trading day of month | `VERIFIED_OFFICIAL` |
| **GOLDGUINEA** | 8 grams | ₹ per 8 g | 0.999 / 0.995 (Disputed) | Last trading day of month | `DISPUTED` (candidates 0.995 / 0.999) |
| **GOLDPETAL** | 1 gram | ₹ per 1 g | 0.999 (999 fineness) | Last trading day of month | `VERIFIED_OFFICIAL` |

### 4.2 Spec Mode Enforcement (Rule R24)
- **`spec_mode = strict`:** Any contract with a non-`VERIFIED_OFFICIAL` spec (e.g. GOLDGUINEA) forces a `QUIET` decision (`SPEC_UNVERIFIED`).
- **`spec_mode = research`:** Calculations proceed using candidate values (e.g. 0.999), but every generated screen, report, and signal is explicitly watermarked as `RESEARCH SIMULATION`.

---

## 5. Core Dashboard Requirements

The dashboard is structured into four primary synchronized workspaces:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AURUM LENS DASHBOARD                            │
├────────────────────────────────────────────────────────────────────────┤
│ A. MARKET OVERVIEW STRIP                                               │
│ [Status: QUIET/ALERT] [Last Update: 15:45 IST] [Feed: Historical/Live] │
│ [Contract Tickers: GOLDM, GOLDTEN, GOLDGUINEA, GOLDPETAL]             │
├──────────────────────────────────┬─────────────────────────────────────┤
│ B. INTERACTIVE CHART COMPONENT   │ C. SIGNAL MONITOR                   │
│ - Candlesticks & Volume          │ - Active Signals & Nearest Misses   │
│ - Raw vs Normalized Toggle       │ - 12-Gate Waterfall Breakdown       │
│ - Spread & Z-Score Overlays      │ - Blocking Reason Codes             │
│ - Entry/Exit & Stop Markers      │ - Economic Hurdle Analysis          │
├──────────────────────────────────┴─────────────────────────────────────┤
│ D. PORTFOLIO SNAPSHOT & RISK RUNNER                                    │
│ [Simulated Cash: ₹10,00,000] [Open Positions: 2] [Unrealized P&L: +₹4,820]│
│ [Risk Stress Test: -2% Gold Drop ➔ Projected Impact: -₹1,240]          │
└────────────────────────────────────────────────────────────────────────┘
```

### 5.1 Section A: Market Overview
- Real-time or snapshot data status indicator (`Historical`, `Delayed 15m`, `Live Authorized`, `Unavailable`).
- Contract metadata badges displaying lot size, quote unit, delivery purity, and days to next expiry.
- Market session status indicators (Normal Trading, Tender Period, Market Closed).
- Stale feed and inconsistent data warning banners.

### 5.2 Section B: Interactive Chart Component
- Candlestick and volume visualization for all four contracts across configurable historical timeframes (1D, 1W, 1M, 6M, 1Y, All).
- Crosshair, dynamic price scales, date-time coordinate tooltips, and responsive zoom/pan.
- Dual-mode visualization:
  - **Raw Tradable Price View:** Quotes exactly as published on exchange.
  - **Normalized Analytical View:** Standardized to ₹/10g 999 fine gold.
- Relative-Value Spread Chart: Visualizing $s_t = \ln(P_A) - \ln(P_B) + \text{carry}$ with rolling mean and $\pm 2\sigma$ Bollinger bands.
- Statistical Deviation Panel: Rolling Z-score with configured entry/exit thresholds.
- Signal event markers matching persisted database signals.
- Comprehensive states: Loading skeletons, empty data states, error alerts, and stale feed notices.

### 5.3 Section C: Signal Monitor
- Live card grid of all 6 eligible cross-contract pairs.
- Decision state: Prominent binary display (`ALERT` or `QUIET`).
- Detailed metrics: Quoted spread, normalized spread, carry adjustment rate, rolling Z-score, expected convergence gross edge.
- **12-Gate Risk Waterfall Modal/Panel:** Full disclosure of all 12 evaluated gates with measured values, thresholds, safety margins, and failure reason codes.
- **Nearest-Miss Card:** Identifies the closest non-alerting pair, displaying how many gates passed and the narrowest failing ratio.

### 5.4 Section D: Portfolio Snapshot & Risk Monitor
- Simulated capital management: Initial cash, available margin, total equity.
- Open paper positions with entry price, mark-to-market valuation, fees deducted, and unrealized P&L.
- Closed trade audit log with entry/exit timestamps, holding period, and realized net P&L.
- Portfolio exposure attribution: Gross notional exposure, contract concentration %, correlated exposure risk.
- Scenario stress tester: User can input hypothetical market shocks (e.g. "Adverse 2% gold move", "Carry rate spike +100bps") to evaluate estimated drawdown.

---

## 6. Unified AurumLens AI Chatbot Requirements

A single, unified conversational intelligence assistant named **AurumLens AI** must be embedded into the platform.

### 6.1 Unified Architecture Mandate
- **No Split Personas:** Users must NOT be forced to switch between separate "Trading Guide" and "Portfolio Manager" bots.
- **Autonomous Intent Routing:** The single assistant dynamically classifies user inquiries into:
  1. *Education & Concepts* (e.g. explaining basis, carry, Z-scores).
  2. *Market & Signal Diagnostics* (e.g. why an alert was triggered or blocked).
  3. *Portfolio Management* (e.g. summarizing holdings, calculating MTM, reviewing trade history).
  4. *What-If Risk Simulation* (e.g. running stress tests on proposed trades).

### 6.2 Chatbot Tool Access & Deterministic Grounding
- The LLM never calculates financial figures or estimates prices. It calls deterministic Python backend tools via structured APIs.
- Every response containing market figures must include an authoritative timestamp and data status label.
- Portfolio queries are strictly scoped to the authenticated user's records.
- **NumericGuard Enforcement:** Text generated by the LLM is programmatically audited to ensure all numbers strictly match evidence JSON values.

### 6.3 Paper Order Confirmation Flow
- The chatbot operates in **read-only** mode by default.
- If a user asks the chatbot to create or close a simulated position (e.g. "Simulate buying 4 lots of GOLDTEN vs 5 lots of GOLDGUINEA"), the chatbot stages a pending order and renders an **explicit UI confirmation card**. No simulated order executes without the user clicking the confirmation button.

---

## 7. Functional Requirements Matrix (FR1 – FR35)

### Data Ingestion & Quality
- **FR1:** Ingest MCX Bhavcopy across legacy (pre-Oct 2023) and modern CDP formats.
- **FR2:** Verify requested vs returned trade dates; reject holiday/empty responses.
- **FR3:** Store raw downloads immutably with SHA-256 verification hashes.
- **FR4:** Flag prices as `SUSPECT` if volume is zero, OI is zero, or close/settlement gap exceeds threshold.
- **FR5:** Standardize contract symbols with strict allowlisting.

### Quant Analytics & Relative Value
- **FR6:** Normalize contract prices to ₹/10g 999 fine gold with programmatic purity direction checks.
- **FR7:** Pair contracts based on smallest calendar expiry gap ($\le 35$ days).
- **FR8:** Compute curve carry from term structure, falling back to configured rate with source labeling.
- **FR9:** Calculate adjusted log spread $s_t = \ln(P_{A,\text{norm}}) - \ln(P_{B,\text{norm}}) + \text{carry}$.
- **FR10:** Compute rolling Z-score and MAD score using history through $t-1$ strictly.
- **FR11:** Evaluate the complete 12-Gate Waterfall simultaneously for every pair on every session.
- **FR12:** Output binary `ALERT` or `QUIET` decisions with zero ambiguous middle states.
- **FR13:** Rank quiet pairs using Nearest-Miss lexicographical scoring.
- **FR14:** Calculate integer lot ratios minimizing unhedged residual fine grams.
- **FR15:** Deduct itemized transaction costs (brokerage, exchange, SEBI, sell-only CTT, buy-only stamp duty, GST).
- **FR16:** Estimate bid-ask spread and adverse slippage using Corwin-Schultz (2012) high-low model.

### Backtesting & Research
- **FR17:** Execute expanding-window walk-forward backtests with $t+1$ execution.
- **FR18:** Benchmark backtest returns against Buy-and-Hold and Seeded Random Entry baselines.
- **FR19:** Compute Deflated Sharpe Ratio (DSR) discounting for multiple trials.
- **FR20:** Log all backtest configurations in an immutable Trial Registry.

### Pre-Trade Tools & Explainability
- **FR21:** Provide interactive Contract Parity Converter (₹/10g 999).
- **FR22:** Provide Cheapest-to-Hedge Calculator ranking friction for any target gram input.
- **FR23:** Generate bilingual plain English and Hindi signal explanations.
- **FR24:** Enforce strict regex NumericGuard auditing all generated text.
- **FR25:** Export evidence dossiers in CSV and standalone HTML formats.

### Dashboard & Charting
- **FR26:** Render interactive candlestick and volume charts across selectable timeframes.
- **FR27:** Provide toggle between raw exchange prices and normalized ₹/10g 999 prices.
- **FR28:** Render relative spread charts with rolling mean and $\pm 2\sigma$ deviation bands.
- **FR29:** Display historical strategy entry/exit markers corresponding to verified database signals.
- **FR30:** Render market overview status strip with data quality warning indicators.

### Paper Trading & Portfolio Risk
- **FR31:** Maintain simulated user portfolios with cash, open positions, and realized/unrealized P&L.
- **FR32:** Enforce portfolio risk limits (max risk per trade, max portfolio exposure).
- **FR33:** Provide "what-if" risk scenario stress testing (e.g. price drop, volatility surge).
- **FR34:** Require explicit two-step user confirmation before creating or closing paper trades.

### Unified AI Chatbot
- **FR35:** Provide single conversational AI assistant ("AurumLens AI") with intent detection, tool execution, multi-turn memory, timestamped citations, and zero number fabrication.

---

## 8. Non-Functional Requirements

- **Calculation Determinism:** The Python quant engine must produce 100% reproducible results given identical config and dataset versions.
- **Zero Client-Side Math:** Next.js and SQL views must only display, filter, and join. Financial math is forbidden in the UI layer.
- **Latency & Performance:** 
  - FastAPI tool endpoints: $< 150\text{ ms}$.
  - Full historical daily evaluation across all pairs: $< 3\text{ seconds}$.
  - Walk-forward backtest (5-year history): $< 60\text{ seconds}$.
- **Security & Authorization:** Server-side Row Level Security (RLS) guaranteeing users can only read their own portfolio and simulated trade records.
- **Accessibility:** WCAG 2.1 Level AA compliance, color-independent alert states, keyboard navigable.

---

## 9. Success Metrics & Quality Gates

- **Zero Hallucination:** 100% of numerical figures emitted by the chatbot match backend tool responses verified by NumericGuard.
- **Quant Integrity:** 100% pass rate on normalization direction tests, cost asymmetry tests, and no-look-ahead regressions.
- **System Stability:** Rehearsal runner passes 3 consecutive cycles of unit tests (117+ tests), secrets scan (0 leaks), and frontend production builds.
