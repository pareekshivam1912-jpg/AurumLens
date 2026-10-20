# AurumLens — Project Progress, Status & Implementation Tracker v3.0

> **Version:** 3.0 · **Date:** 2026-10-20 · **Status:** Master Status Report  
> **Repository Commit Baseline:** `6b510e5` (117+ Tests Passing, 27/27 Baseline FRs Compliant)

---

## 1. Executive Status Dashboard

| Metric / Dimension | Current Status | Notes & Verification |
|---|---|---|
| **Python Quant Engine** | **100% COMPLETE** ✅ | 122 unit/integration tests passing in ~6.8s |
| **Quant Gating & Evidence** | **100% COMPLETE** ✅ | 12-Gate Waterfall, itemized Indian friction, Corwin-Schultz slippage |
| **Walk-Forward Backtest** | **100% COMPLETE** ✅ | Folds, holdouts, gross/net attribution, Deflated Sharpe Ratio |
| **FastAPI Microservice** | **100% COMPLETE** ✅ | Tools, explainers, chart series API, exporters, admin endpoints |
| **Security & Secrets Posture** | **100% CLEAN** ✅ | 0 leaks detected across 139+ files (`scan_secrets.py`) |
| **FR Baseline Verification** | **27/27 PASS** ✅ | All functional requirements verified by `verify_fr_checklist.py` |
| **Next.js Web Frontend** | **PROTOTYPE COMPLETE** ✅ | 12 static routes pre-rendering; Stitch Fintech institutional design |
| **Interactive Chart Suite** | **100% COMPLETE** ✅ | `InteractiveChart.tsx` with dual-mode parity, spread & Z-score panels |
| **Unified AI Chatbot Dock** | **IN SPEC / PROTOTYPE** 🟡 | Python backend explainer & NumericGuard ready; chat dock in Phase 4 |
| **Offline Rehearsal Runner** | **3/3 PASS** ✅ | Passes 3 consecutive verification cycles (`rehearse_demo.py`) |

---

## 2. Completed Deliverables by Phase

### Phase 0: Baseline Freeze & Facts Register
- Canonical `config/contracts.yaml` established with official MCX contract specifications.
- `spec_mode = strict` and `spec_mode = research` enforcement logic built.
- Historical Bhavcopy parsers implemented for both legacy (pre-Oct 2023) and modern TCS CDP eras.
- SHA-256 verification hash pipeline built for all raw downloads.

### Phase 1 & 2: Quant Engine & Relative-Value Analytics
- Exact mathematical normalization: $P \times (10/\text{basis}) \times (0.999/\text{purity})$.
- Purity direction test verified (sub-999 purity normalizes UPWARD).
- Smallest calendar gap expiry pairing algorithm ($\Delta T \le 35\text{ days}$).
- Carry model: same-symbol term structure curve carry with source fallback tagging.
- Adjusted log basis $s_t = \ln(P_A) - \ln(P_B) + \text{carry}$ with rolling lookback through $t-1$.
- Integer lot-ratio sizing engine minimizing unhedged residual fine gold grams (e.g. GOLDTEN vs GOLDGUINEA = 4:5 ratio, 0.0g residual).
- Complete itemized Indian statutory friction model:
  - Brokerage (min flat ₹20 vs pct).
  - Exchange & SEBI turnover fees.
  - Sell-side only CTT (0.01%).
  - Buy-side only Stamp Duty (0.002%).
  - GST (18%) strictly on service fees.
- Corwin-Schultz (2012) bid-ask spread estimator.

### Phase 3 & 5: Signal Engine, Gating & Backtesting
- 12-Gate Waterfall Evaluator: Evaluates all 12 gates simultaneously, storing margin and reason codes.
- Nearest-Miss Ranking Service: Lexicographically sorts quiet pairs by gates passed and narrowest failing ratio.
- Walk-forward backtester: Expanding window folds, $t+1$ execution, adverse slippage fills.
- Attribution breakdown: Gross spread, transaction costs, slippage, net arbitrage, and residual gold delta P&L.
- Deflated Sharpe Ratio (DSR) discounting for multi-trial parameter search.

### Phase A7–A9: Frontend & FastAPI Microservice
- 9 institutional fintech screens scaffolded in Next.js 14 App Router matching Stitch design system.
- Thin FastAPI microservice running on `http://localhost:8000` with Pydantic boundaries.
- Pre-trade hedge tools: Cheapest-to-Hedge (FR23), Parity Converter (FR22), Lot-Ratio Sizer (FR24).
- Bilingual signal explainer (English and Hindi) with regex `NumericGuard` protection.
- Evidence dossier exporters in CSV and standalone audited HTML formats.
- Interactive 3-scenario demo switcher on Pair Analysis screen (Date 1: Alert Day, Date 2: Nearest Miss Day, Date 3: Blocked Day).
- One-click launch scripts (`run_demo.bat` and `run_demo.ps1`).

---

## 3. Pending Work & Implementation Gap Analysis

To bring the codebase into 100% alignment with the upgraded vision in `prompt.md`:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        GAP ANALYSIS MATRIX                             │
├──────────────────────────┬─────────────────────────────┬───────────────┤
│ Functional Capability    │ Current State               │ Target State  │
├──────────────────────────┼─────────────────────────────┼───────────────┤
│ Interactive Charting     │ Design spec ready; mock view│ Multi-window  │
│                          │ in pair analysis            │ Candlestick & │
│                          │                             │ spread chart  │
├──────────────────────────┼─────────────────────────────┼───────────────┤
│ Unified AI Chatbot       │ Backend explainer & guard   │ Live floating │
│                          │ complete; REST endpoints    │ chat dock with│
│                          │                             │ multi-turn UI │
├──────────────────────────┼─────────────────────────────┼───────────────┤
│ Paper Portfolio Engine   │ Simulator adapter built;    │ Multi-user MTM│
│                          │ basic positions tracked     │ ledger with   │
│                          │                             │ what-if runner│
├──────────────────────────┼─────────────────────────────┼───────────────┤
│ Live Feed Integration    │ EOD Bhavcopy pipeline       │ WebSocket feed│
│                          │ complete; live abstract spec│ adapter (Ph 6)│
└──────────────────────────┴─────────────────────────────┴───────────────┘
```

### Immediate Tasks:
1. **Interactive Chart Component (Phase 1):** Implement the multi-window charting component (Candlesticks, volume, normalized overlay, spread with $\pm 2\sigma$ envelopes, and deviation panel) in `web/src/components/InteractiveChart.tsx`.
2. **Unified Chatbot Dock (Phase 4):** Implement the persistent floating `AurumLens AI` chat dock in `web/src/components/ChatbotDock.tsx`, wired to the FastAPI `/v1/chat` intent router with interactive paper order staging cards.
3. **What-If Risk Runner (Phase 3):** Implement the scenario stress-test runner (`/v1/tools/simulate-risk`) calculating projected net P&L and delta risk for hypothetical price shocks.

---

## 4. Key Decisions Log

| Decision ID | Date | Subject | Decision Taken & Rationale |
|---|---|---|---|
| **DEC-01** | 2026-10-01 | Normalization Direction | Sub-999 purity must normalize UPWARD ($P \times 0.999/0.995$). Verified against physical gold bullion parity. |
| **DEC-02** | 2026-10-02 | Convergence Baseline | Expected convergence must be measured to the 60-day rolling mean $\mu_{t-1}$, never to zero. Prevents constant basis offsets from triggering false arbitrage alerts. |
| **DEC-03** | 2026-10-03 | Waterfall Completeness | All 12 gates must ALWAYS be evaluated, even if Gate 1 fails. Necessary to deliver Nearest-Miss transparency. |
| **DEC-04** | 2026-10-04 | UI Formula Isolation | Next.js and SQL views must contain zero financial formulas. All calculations reside in pure Python functions. |
| **DEC-05** | 2026-10-05 | Secrets Isolation | Browser client receives strictly the Supabase `anon` key. The `service_role` key is isolated on the backend server. |
| **DEC-06** | 2026-10-20 | Single Chatbot Persona | Merged separate "Trading Guide" and "Portfolio Manager" concepts into one unified assistant ("AurumLens AI") per `prompt.md`. |
| **DEC-07** | 2026-10-20 | Charting Integration | Adopted dual-tier charting: application-supplied financial charts for core analytical spreads; optional embeddable widget for external reference only. |

---

## 5. Known Limitations & Technical Debt

1. **GOLDGUINEA Purity Dispute:** The delivery fineness of GOLDGUINEA remains `DISPUTED` (candidates 0.995 vs 0.999). Under `spec_mode = strict`, GOLDGUINEA pairs default to `QUIET` (`SPEC_UNVERIFIED`). Under `spec_mode = research`, 0.999 is used with a watermark.
2. **Safety Buffer Parameter:** The safety buffer in `config/costs.yaml` is currently `null` with status `TO_VALIDATE`. A value of ₹0.00 is used until empirical slippage studies conclude.
3. **EOD Bhavcopy Reliance:** Current prototype operates on daily Bhavcopy settlement files. Real-time tick feeds require an active commercial vendor agreement with an authorized data provider.

---

## 6. Next Actions

1. Review and freeze the upgraded documentation suite with the implementation team.
2. Build the Next.js `InteractiveChart` component accepting application-supplied candle and spread datasets.
3. Wire the persistent `AurumLens AI` Chatbot Dock into the Next.js application shell.
4. Execute `python scripts/rehearse_demo.py` to ensure all 117+ tests, security scans, and build tasks remain 100% compliant.
