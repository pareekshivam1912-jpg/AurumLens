# AurumLens — Phase-wise Execution Plan v2.0

> **Version:** 2.0 · **Date:** 2026-10-01 · **Supersedes:** v1
>
> **Priority labels:**
> - **[CORE]**: required for any demo.
> - **[MVP+]**: v2 additions that are in MVP scope.
> - **[STRETCH]**: only if time allows.
>
> Work one phase at a time and stop at each exit gate.

---

## Phase 0 — Source Verification & Project Freeze
**Goal:** remove factual uncertainty before writing analytics.

### Tasks
- [CORE] Fill the **facts register** (PRD §5) from official MCX/SEBI documents: unit, quote basis, purity, expiry rule, tender days, and tick size for all four contracts.
- [CORE] Resolve **GOLDGUINEA purity** (F9). Until it is resolved, keep it `DISPUTED`.
- [CORE] Read circular **MCX/TRD/456/2025** (launch-calendar change) and record its effect on expiries.
- [CORE] Find the SEBI circular on the staggered delivery period (F12).
- [CORE] Confirm how Bhavcopy is accessed **before and after October 2023**: URLs or methods, file names, columns and date formats. Save one sample file from each era to `data/fixtures/real_samples/` (real data, labeled as such).
- [CORE] Confirm whether a settlement price field exists (F14).
- [CORE] Record GOLDTEN's first appearance date in real data (F4).
- [CORE] Draft the cost schedule (`costs.yaml`) with a status per value. Choose a default broker profile.
- [CORE] Freeze the repo skeleton, config schemas (Pydantic), `.env.example`, pytest and the CI workflow.
- [MVP+] Create `events.yaml` with candidate events (each `verified: false` until sourced).

### Exit Gate
- One real trading day from **each** format era has been downloaded, parsed and checked by hand.
- Every facts-register row has a status. `spec_mode` is set explicitly.

---

## Phase 1 — Historical Data Engine
**Goal:** a clean, versioned, contract-level historical dataset.

### Build
- [CORE] Downloader with polite caching and a raw immutable store with sha256.
- [CORE] `SourceAdapter` interface, with `legacy` and `cdp` adapters mapping to a canonical schema.
- [CORE] Validator: requested date equals returned date, schema, types, symbol allow-list, expiry parsing.
- [CORE] DuckDB schema (`source_file`, `contract`, `daily_price`) and Parquet dataset snapshots with a `dataset_version`.
- [CORE] Reject/error log and ingestion report.
- [MVP+] Price-quality stage: `price_source`, `SUSPECT` flags (FR18).

### Tests
- Date mismatch rejected; holiday or missing file handled.
- Malformed schema rejected.
- Symbol padding and cleanup.
- Expiry parsing for both eras.
- No duplicate `(contract_id, trade_date)`.
- Only supported symbols kept.
- Low-volume and close/settlement-divergence rows are flagged `SUSPECT`.

### Exit Gate
Several years of data for the supported contracts, with a validation report covering:
- rows per symbol;
- date range;
- rejects;
- duplicates (zero allowed silently);
- SUSPECT counts.

---

## Phase 2 — Normalization, Pairing, Carry & Sizing
**Goal:** prove the contracts are compared correctly.

### Build
- [CORE] Contract master loaded from the facts register.
- [CORE] Normalization to ₹/10 g of 999, including the **direction test**.
- [CORE] Smallest-gap expiry matching with `max_expiry_gap_days`.
- [CORE] Carry: implied from the same-symbol curve, else fallback, with `carry_source` recorded.
- [CORE] Log spread (raw and adjusted).
- [MVP+] Lot-ratio sizer and residual fine grams (FR24).
- [MVP+] Converter function (FR22). The UI comes later.

### Demo Artifact
- A chart of normalized prices for all four contracts.
- One pair's adjusted log spread, with carry source shading.

### Exit Gate
- All hand fixtures in Design §6 equal the engine output, including 120,482.41, the Nov-5 pairing, the 0.00014597 spread and the 4:5 ratio.
- The team can explain each step.

---

## Phase 3 — Signal Engine
**Goal:** turn relative pricing into selective, explainable decisions.

### Build
- [CORE] Rolling z-score using data through `t−1`, plus the optional MAD score.
- [CORE] History sufficiency check.
- [CORE] Itemized cost model and Corwin-Schultz slippage with fallback.
- [CORE] Expected convergence to the rolling mean (R21).
- [CORE] Liquidity, expiry/tender and cost-hurdle gates.
- [CORE] **All-gate evaluator** with margins and reason codes (R20).
- [CORE] Spec-mode gate (R24). Duplicate suppression.
- [CORE] Evidence record builder.
- [MVP+] Nearest-miss service (FR17).

### Tests
- A planted anomaly triggers. Ordinary days stay quiet.
- A cost failure, a liquidity failure, an expiry failure and a SUSPECT price each block the alert.
- A pair failing several gates reports all of them.
- A constant structural offset never alerts.
- Strict mode with a `DISPUTED` spec gives `SPEC_UNVERIFIED`.
- Changing future data cannot change past signals.

### Exit Gate
Real examples of an `ALERT`, a `QUIET` with its nearest miss, and a tempting anomaly that was blocked, each with full gate evidence.

---

## Phase 4 — Walk-forward Backtesting
**Goal:** determine whether the method survives unseen data and costs.

### Build
- [CORE] Chronological fold builder. Train-only selection; frozen parameters per fold.
- [CORE] **Trial registry**: every config tried is logged.
- [CORE] `t+1` execution with slippage. Actual contracts and integer lots.
- [CORE] Exits: reversion, time stop, unsafe window.
- [CORE] Itemized costs. Attribution: strategy vs residual gold.
- [CORE] Final untouched holdout, reported separately.
- [MVP+] Baselines: always-quiet, and seeded random entry (FR21).
- [MVP+] Metrics: Sharpe, max drawdown, hit rate and the **Deflated Sharpe Ratio**.
- [STRETCH] Sensitivity heatmap on training folds only (FR29).

### Required Outputs
- Gross P&L, costs (itemized), slippage, net P&L.
- Strategy P&L and residual gold P&L.
- Fold metrics, holdout metrics, baseline comparison and DSR.
- Trade ledger.

### Exit Gate
- No-leakage tests pass.
- Results reproduce exactly from dataset version plus config version.
- A negative result is acceptable and must be shown honestly.

---

## Phase 5 — API & Dashboard
**Goal:** a usable, judge-friendly product.

### Build
- [CORE] FastAPI endpoints (Design §7), with bounded inputs and admin token.
- [CORE] Screens: Overview, Pair Analysis (with **gate waterfall**), Backtest, Calendar, Alert Log.
- [CORE] Replay date selector. Data freshness indicator. Spec-mode watermark. Disclaimer.
- [MVP+] Cost breakdown panel (FR19), spec trust and Data Health screen (FR20, FR18).
- [MVP+] Hedge Tools screen: converter, cheapest-to-hedge, lot sizer (FR22–FR24).
- [MVP+] Event markers on charts and calendar (FR25).
- [MVP+] Methodology page.

### Exit Gate
- A non-trader understands the system status, and one signal, within about 30 seconds.
- Everything works offline from cache.

---

## Phase 6 — Explanations, Alerts & Paper Trading
**Goal:** an operational workflow without real-money execution.

### Build
- [MVP+] Deterministic English/Hindi explainer, plus the numeric guard (FR26).
- [MVP+] Evidence pack export as CSV and HTML (FR27).
- [CORE] Telegram alert adapter behind an interface.
- [CORE] `PaperExecutionAdapter`: two-leg simulated orders, fills, position state, exits, P&L.
- [CORE] Duplicate-execution protection, audit log, and representable partial or failed legs.
- [STRETCH] Daily Telegram digest (FR30), paper journal timeline (FR31).

### Exit Gate
- A replayed historical alert flows through: signal → explanation (EN/HI) → paper position → exit → stored P&L → exported evidence pack.

---

## Phase 7 — Hardening & Demo
**Goal:** make the project safe to judge.

### Tasks
- Full FR checklist (FR1–FR27). Test suite. Secret scan. Input-bound review.
- Performance check (full backtest under 60 s). Offline-mode check. Lineage spot-check. Reproducibility check.
- Pick three **real** demo dates (never altered):
  1. a clear gated alert;
  2. a quiet day with an interesting nearest miss;
  3. a tempting anomaly blocked by liquidity, expiry or a stale price.
- Prepare one hedge-tool scenario (for example, "hedge 500 g").
- Screenshots, backup demo video, methodology slide, architecture diagram, known-limitations slide.
- [STRETCH] Replay player (FR28). Spot premium (FR32), only if a source has been verified.

### Exit Gate
The full demo succeeds offline three times in a row, with no P1 bugs.

### Suggested 3-minute pitch
1. **Hook:** "Gold is gold — so why do four MCX gold contracts disagree?"
2. **Normalize:** the converter shows one price expressed in all four contracts.
3. **Evidence:** replay an alert day and walk through the gate waterfall and costs.
4. **Rigor:** show the blocked day, then the backtest against baselines, including a no-edge result if that is the truth.
5. **Utility:** the cheapest-to-hedge calculator, and the Hindi explanation.

---

## Phase 8 — Post-MVP Live Execution (Future, design only)
**Not part of the hackathon MVP.**

**Prerequisites:**
- stable paper-trading results;
- broker API, legal and compliance checks;
- an execution-quality study;
- a margin model;
- a risk review.

**Components:**
- Risk Manager;
- Broker Adapter;
- Pair Order Manager;
- partial fills;
- reconciliation;
- Exit Engine;
- slippage, position and daily-loss limits;
- kill switch;
- audit log.

**Rule:** never enable live execution just because a backtest is profitable.
