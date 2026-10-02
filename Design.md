# AurumLens — Engineering & Product Design v2.0

> **Version:** 2.0 · **Date:** 2026-10-01 · **Supersedes:** v1
>
> **What v2 adds:**
> - exact formulas, with worked fixture values;
> - smallest-gap pairing;
> - a carry source hierarchy;
> - Corwin-Schultz slippage;
> - an itemized cost model;
> - lot sizing;
> - a gate evaluator that runs every gate;
> - nearest miss;
> - hedge tools;
> - a bilingual explainer;
> - an expanded data model and test plan.

## 1. Design Goals
- Data correctness before UI.
- Contract-aware analytics; no continuous-series shortcuts.
- Transparent calculations. Every intermediate value is stored.
- Reproducible research: dataset version plus config version gives identical output.
- A small, modular Python codebase built from pure quant functions.
- A clean path from research to paper trading to future live execution.
- Explainable to a non-trader in about 30 seconds.

## 2. Stack (decided)
| Concern | Choice |
|---|---|
| Language | Python 3.12+ |
| Data | pandas, NumPy |
| Storage | DuckDB (analytics) + Parquet (snapshots, datasets) |
| Statistics | statsmodels (diagnostics only: ADF, Engle-Granger) |
| API | FastAPI + Pydantic |
| UI | Streamlit (default); Next.js only if the team prefers React |
| Charts | Plotly |
| Export | CSV + HTML (print to PDF) |
| Tests | pytest (+ hypothesis for property tests, optional) |
| Packaging | Docker |
| Alerts | Telegram Bot API (optional) |

## 3. Repository Design

```text
aurumlens/
├── README.md
├── CHANGELOG.md
├── docs/                      # PRD, Design, Phase, System_architecture, phase_wiseprompt
├── .cursorrules
├── .env.example
├── config/
│   ├── contracts.yaml         # specs + facts-register status per field
│   ├── costs.yaml             # itemized cost schedule (status per value)
│   ├── strategy.yaml          # scoring, gates, sizing, backtest params
│   └── events.yaml            # dated market events (source, verified flag)
├── data/
│   ├── raw/                   # immutable downloads, named by date + hash
│   ├── processed/             # versioned parquet datasets
│   └── fixtures/              # synthetic=true fixtures ONLY
├── src/aurumlens/
│   ├── config/                # pydantic config models + loader + version hash
│   ├── ingest/
│   │   ├── downloader.py
│   │   ├── adapters/
│   │   │   ├── base.py        # SourceAdapter interface -> canonical schema
│   │   │   ├── legacy.py      # pre Oct-2023 format
│   │   │   └── cdp.py         # post Oct-2023 CDP format
│   │   ├── validator.py
│   │   └── quality.py         # price_source choice, SUSPECT flags
│   ├── core/
│   │   ├── contracts.py
│   │   ├── normalization.py
│   │   ├── expiry_matching.py
│   │   ├── carry.py
│   │   ├── spreads.py
│   │   ├── sizing.py          # lot ratio, residual grams
│   │   ├── costs.py
│   │   └── slippage.py        # Corwin-Schultz + fallback
│   ├── signals/
│   │   ├── scoring.py
│   │   ├── gates.py           # all-gate evaluator, margins, reason codes
│   │   ├── near_miss.py
│   │   └── service.py         # builds evidence records
│   ├── backtest/
│   │   ├── engine.py
│   │   ├── walkforward.py
│   │   ├── baselines.py
│   │   ├── metrics.py         # Sharpe, DSR, drawdown
│   │   ├── trials.py          # trial registry
│   │   └── attribution.py
│   ├── tools/
│   │   ├── converter.py
│   │   └── hedge_cost.py
│   ├── explain/
│   │   ├── templates/         # en.yaml, hi.yaml
│   │   ├── explainer.py
│   │   └── numeric_guard.py
│   ├── export/evidence.py
│   ├── paper/{simulator.py, positions.py}
│   ├── alerts/telegram.py
│   ├── api/{main.py, routes/}
│   └── db/{schema.py, repository.py}
├── ui/                        # streamlit pages (no formulas)
├── tests/
└── scripts/                   # ingest_range, build_dataset, run_backtest, replay
```

## 4. Configuration Schemas (shape only, no authoritative values)

```yaml
# contracts.yaml
spec_mode: research            # strict | research
contracts:
  GOLDM:
    trading_unit_g:  {value: 100,   status: SECONDARY, source: "<url/doc>", verified_at: null}
    quote_basis_g:   {value: 10,    status: SECONDARY, source: "...", verified_at: null}
    purity:          {value: 0.995, status: SECONDARY, source: "...", verified_at: null}
    expiry_rule:     {value: "DAY_5_OF_MONTH", status: SECONDARY, ...}
    tender_days:     {value: 3,     status: SECONDARY, ...}
  GOLDGUINEA:
    purity:          {value: null,  status: DISPUTED, candidates: [0.995, 0.999], ...}
  # ...
target_basis: {grams: 10, purity: 0.999}
```

```yaml
# costs.yaml : candidate values from the research report; ALL need verification
brokerage:   {mode: min_flat_pct, flat_inr: 20, pct: 0.0003, status: SECONDARY, note: "broker-specific"}
ctt_sell:    {rate: 0.0001,   status: SECONDARY}
exchange:    {rate: 0.000021, status: SECONDARY}
sebi:        {rate: 0.000001, status: SECONDARY}
stamp_buy:   {rate: 0.00002,  status: SECONDARY}
gst:         {rate: 0.18, applies_to: [brokerage, exchange, sebi], status: SECONDARY}
safety_buffer_inr_per_10g: {value: null, status: TO_VALIDATE}
```

Every config file is hashed. `config_version = sha256(all config files)[:12]` is stamped on every derived row.

## 5. Data Model (DuckDB)

| Table | Key columns |
|---|---|
| `source_file` | file_id PK, requested_date, returned_date, adapter (`legacy`/`cdp`), sha256, fetched_at, status (`OK`/`REJECTED`), reject_reason |
| `contract_spec` | symbol PK, trading_unit_g, quote_basis_g, purity, expiry_rule, tender_days, tick_size, status per field, source_reference, verified_at |
| `contract` | contract_id PK (`SYMBOL_YYYYMMDD`), symbol FK, expiry_date, first_seen, last_seen |
| `daily_price` | (contract_id, trade_date) UNIQUE, open, high, low, close, settlement NULL, volume, open_interest, price_used, price_source, price_quality (`OK`/`SUSPECT`), quality_reason, normalized_price, file_id FK |
| `pair_daily` | (pair_id, trade_date) UNIQUE, leg_a_contract_id, leg_b_contract_id, expiry_gap_days, norm_a, norm_b, log_spread_raw, carry_rate, carry_source, carry_adj, log_spread_adj, roll_mean, roll_std, zscore, rich_leg, lots_a, lots_b, residual_fine_g, expected_convergence_inr, cost_total_inr, slippage_inr, buffer_inr, net_edge_inr, config_version, dataset_version |
| `gate_result` | (pair_id, trade_date, gate) UNIQUE, passed BOOL, value, threshold, margin, reason_code |
| `signal` | signal_id PK, pair_id, trade_date, status (`QUIET`/`ALERT`), direction, reason_codes[], near_miss_score, config_version, created_at |
| `cost_line` | signal_id/trade_id, leg, side, component, amount_inr |
| `event` | event_date, label, category, source, verified |
| `backtest_run` | run_id, dataset_version, config_version, fold definition, holdout flag, created_at |
| `trial` | trial_id, run_id, params_json, train-period metric (feeds DSR) |
| `trade` | trade_id, run_id, pair_id, entry_date, exit_date, contracts and lots per leg, entry/exit prices, gross_pnl, costs, slippage, net_pnl, strategy_pnl, residual_gold_pnl, exit_reason |
| `paper_order` / `paper_position` / `audit_log` | Phase 6 |

## 6. Processing Design

### 6.1 Ingestion
1. Request the date's file, or load it from cache.
2. Persist the immutable raw file and its sha256.
3. Pick the adapter by era. Map to the canonical schema. Fail loudly on unknown columns.
4. Validate: requested date equals returned date, required columns are present, types parse.
5. Strip and standardize symbols. Keep only the allow-listed four.
6. Parse trade and expiry dates explicitly; no locale guessing.
7. Deduplicate on `(contract_id, trade_date)`. A conflicting duplicate is rejected and logged, never silently overwritten.
8. Upsert, then emit an ingestion report: rows per symbol, rejects, duplicates and missing fields.

### 6.2 Price quality
- `price_used = settlement` if `price_source == settlement` and settlement is non-null; otherwise `close`.
- `SUSPECT` if `volume < min_volume_for_price`, or `|close − settlement| / settlement > stale_gap_threshold`, or the price is ≤ 0.

### 6.3 Normalization (R16)
`P_norm = P_used × (10 / quote_basis_g) × (target_purity / purity)`, where `target_purity = 0.999`.

Hand fixtures (synthetic=true; illustrative prices; assume 999 for GUINEA):

| Contract | Quoted | Factor | Normalized ₹/10 g 999 |
|---|---|---|---|
| GOLDM (995, per 10 g) | 120,000 | 1.0 × 0.999/0.995 = 1.0040201 | **120,482.41** |
| GOLDTEN (999, per 10 g) | 120,500 | 1.0 | **120,500.00** |
| GOLDGUINEA (999, per 8 g) | 96,400 | 1.25 | **120,500.00** |
| GOLDPETAL (999, per 1 g) | 12,050 | 10 | **120,500.00** |

A **direction test** is required: normalizing a 995 contract must produce a value **greater than** its quoted price.

### 6.4 Expiry matching (R17)
For each pair (A, B) and date `t`:
1. List the active contracts of A and B that have rows on `t`.
2. For every combination, compute `gap = |T_A − T_B|` in calendar days.
3. Keep the combinations with `gap ≤ max_expiry_gap_days`.
4. Choose the smallest gap. On a tie, prefer the nearer expiry, then higher combined OI.
5. Record both contract IDs and the gap. If nothing qualifies, return `NO_EXPIRY_PAIR`.

Fixture: GOLDTEN Oct-31 against GOLDM {Oct-5, Nov-5, Dec-5} must choose **Nov-5** (gap 5).

### 6.5 Carry (R18)
- **Curve:** if symbol S has two `OK`-quality expiries on `t` with enough volume, then
  `r_curve = ln(P_far / P_near) / ((T_far − T_near) / 365)`.
  Use the symbol of the **longer-dated leg**, or the average of both if both are available (configurable).
- **Fallback:** `r = carry_fallback_rate` (config, `TO_VALIDATE`). Mark `carry_source = FALLBACK`.
- **Adjustment:** `carry_adj = r × (T_B − T_A) / 365`.
- **Scale check:** at r = 6%, a 5-day gap gives 0.00082 (8.2 bp) and a 26-day gap gives 0.00427 (42.7 bp). This is why smallest-gap pairing matters: an error in carry can exceed the anomaly being measured.

### 6.6 Spread and score
- `s_t = ln(norm_A) − ln(norm_B) + carry_adj`.
  Fixture: GOLDTEN 120,500 vs GOLDM 120,482.41 gives a raw log spread of **0.00014597**.
- `z_t = (s_t − μ_{t−1}) / σ_{t−1}`, with μ and σ taken over `s_{t−L} … s_{t−1}`. Require `count ≥ min_history_obs`.
- MAD variant: `(s_t − median) / (1.4826 × MAD)` over the same window.
- `rich_leg = A if s_t > μ_{t−1} else B`.

### 6.7 Sizing (R22)
- Fine grams per lot: `g_i = trading_unit_g_i × purity_i / 0.999`.
- Search integers `1 ≤ n_A, n_B ≤ max_lots_per_leg` that minimize `|n_A·g_A − n_B·g_B|`, then smallest notional, subject to `max_notional_inr`.
- `residual_fine_g = n_A·g_A − n_B·g_B` (the sign shows which leg is long gold).
- Fixture (assuming 999 for both): GOLDTEN 10 g vs GOLDGUINEA 8 g gives a ratio of **4 : 5** (40 g vs 40 g, residual 0).

### 6.8 Expected convergence (R21)
`expected_convergence_inr = |s_t − μ_{t−1}| × convergence_capture_ratio × V_pair`

Here `V_pair` is the ₹ notional of the smaller leg at normalized prices.

### 6.9 Costs (itemized)
For each leg and each side (entry, exit), with turnover `V`:

| Component | Formula |
|---|---|
| Brokerage | `min(flat_inr, pct × V)` (mode configurable) |
| Exchange | `exchange.rate × V` |
| SEBI fee | `sebi.rate × V` |
| CTT | `ctt_sell.rate × V`, sell side only |
| Stamp duty | `stamp_buy.rate × V`, buy side only |
| GST | `gst.rate × (brokerage + exchange + sebi)` |

Total = the sum over 2 legs × 2 sides. Every component is stored in `cost_line`.

Note: the flat brokerage per order dominates on small contracts. For example, a large PETAL lot count makes brokerage scale with the number of orders. The sizer and the hedge tool must therefore show the per-order count.

### 6.10 Slippage (Corwin-Schultz 2012, with fallback)
With daily highs H and lows L:
- `β = [ln(H_t/L_t)]² + [ln(H_{t−1}/L_{t−1})]²`
- `γ = [ln(max(H_t, H_{t−1}) / min(L_t, L_{t−1}))]²`
- `α = (√(2β) − √β) / (3 − 2√2) − √(γ / (3 − 2√2))`
- `S = 2(e^α − 1) / (1 + e^α)`

Average S over `cs_window` days, using data through `t−1` only.

- **Fallback:** if `S ≤ 0` or the data is missing, use `fallback_bps[symbol]`.
- **Simulated fill:** `price × (1 ± S/2)`, adverse to the trade.
- **Fixture:** H = (120,900; 121,200), L = (119,800; 120,300) gives S ≈ **0.000424**.

### 6.11 Gate evaluator (R20)
`evaluate_gates(pair_day, config) -> list[GateResult]`. It always returns all 11 gates, each with `(passed, value, threshold, margin, reason_code)`. Status is `ALERT` only if all pass. The function is pure, with no I/O.

### 6.12 Nearest miss (FR17)
For a `QUIET` pair-day, compute each numeric gate's ratio, capped at 1:
- `|z| / entry_z`
- `net_edge / hurdle`
- `volume / min_volume`
- `OI / min_oi`

`near_miss_score = (number of gates passed, min ratio over failing gates)`. Rank pairs lexicographically. The UI shows the top pair and its blocking gate(s).

### 6.13 Hedge tools (FR22–FR24)
Hedge tools reuse the functions above and contain no new formulas.
- **Converter:** `P_norm`, then the inverse into the other contracts' quote bases.
- **Cheapest-to-hedge:** for target fine grams G, for each contract compute:
  - `lots = round(G / g_i)`;
  - effective and residual grams;
  - normalized price;
  - round-trip cost (6.9) + slippage (6.10);
  - cost per 10 g;
  - liquidity status.

  Rank by total cost, flag illiquid contracts, and show the disclaimer.
- **Lot sizer:** 6.7, with user caps.

### 6.14 Explainer (FR26, R25)
- Deterministic templates per language (`en.yaml`, `hi.yaml`) are keyed by status and reason codes, and filled from the evidence JSON.
- An optional LLM rewrite takes only the evidence JSON and the template output.
- `numeric_guard` extracts every number from the output and checks that each one exists in the JSON (after formatting normalization). On failure it falls back to the template.

### 6.15 Backtest
- Chronological folds (`train_window`, `test_window`). Parameters are chosen on train only, recorded in `trial`, and frozen per test fold.
- Entry at `t+1` using `execution_price`, plus slippage. Exit on reversion, time stop or unsafe window, whichever comes first.
- **Attribution:**
  - `residual_gold_pnl = residual_fine_g / 10 × ΔP_norm(ref leg)`;
  - `strategy_pnl = gross_pnl − residual_gold_pnl`;
  - `net = gross − costs − slippage`.
- **Baselines:** always-quiet (₹0), and random entry (seeded; N runs; same exits and costs), reported as a distribution.
- **Deflated Sharpe Ratio:** uses `n_trials = count(trial)` and the skew and kurtosis of returns. It is reported, never optimized.
- **Holdout:** runs once, after the methodology is frozen. The results are labeled.

## 7. API Design (`/v1`, read-only unless noted)
| Endpoint | Purpose |
|---|---|
| `GET /contracts`, `GET /specs` | Contract master and facts register |
| `GET /prices?symbol&from&to` | Contract-level prices with quality flags |
| `GET /pairs`, `GET /pairs/{id}/history` | Pair series (spread, z, carry source) |
| `GET /gates/{pair_id}/{date}` | Full gate waterfall |
| `GET /signals?status&from&to`, `GET /signals/{id}` | Evidence records |
| `GET /signals/{id}/explain?lang=en\|hi` | Explanation |
| `GET /signals/{id}/evidence.csv`, `.html` | Evidence pack |
| `GET /near-miss?date` | Nearest-miss ranking |
| `GET /backtests/{run_id}` | Folds, baselines, attribution, DSR, ledger |
| `GET /calendar`, `GET /events` | Expiries, unsafe windows, events |
| `GET /health` | Data freshness, ingestion report, rejects |
| `GET /tools/convert`, `GET /tools/hedge-cost`, `GET /tools/lot-ratio` | Hedge tools (bounded inputs) |
| `GET /paper/positions` | Paper positions |
| `POST /admin/refresh`, `POST /admin/backtests`, `POST /paper/execute` | Token-protected |

## 8. UI Design (Streamlit pages; no formulas in the UI)
| Screen | Contents |
|---|---|
| **Overview** | Big `QUIET`/`ALERT` badge, pair cards, nearest-miss card ("closest: GOLDM/GOLDTEN, z 1.7 of 2.0"), data freshness, spec-mode watermark |
| **Pair Analysis** | Contract IDs and expiries; normalized price chart; adjusted spread; z-score with entry/exit bands; gate waterfall (traffic lights with margins); cost breakdown; event markers; replay date picker |
| **Backtest** | Fold table, holdout (separate), equity curve vs baselines, gross → costs → slippage → net bars, strategy vs residual gold, DSR, trade ledger, config version |
| **Calendar** | Expiries per contract, red unsafe windows, liquid windows, events |
| **Alert Log** | Alerts with direction, explanation (EN/HI toggle) and export buttons |
| **Hedge Tools** | Converter, cheapest-to-hedge table, lot sizer |
| **Data Health** | Ingestion log, rejects, SUSPECT prices, facts register with badges |
| **Methodology** | Pipeline diagram, formulas, limitations, disclaimer |
| **Paper** (optional) | Positions and paper P&L |

## 9. Testing Strategy
**Carried from v1:**
- normalization fixtures;
- date and parser tests;
- duplicate prevention;
- expiry matching;
- carry;
- the look-ahead test (changing future rows cannot change past signals);
- gate tests;
- cost and slippage tests;
- fold isolation;
- API validation and auth;
- offline demo;
- planted-anomaly detection;
- synthetic data never appearing in real results.

**New in v2:**
- Purity **direction** test (995 normalizes up).
- Adapter tests: one legacy and one CDP sample file both map to an identical canonical schema.
- Price-quality tests: low volume and close/settlement divergence each give `SUSPECT`, and the pair is `QUIET`.
- Smallest-gap pairing fixture (must choose Nov-5).
- Carry tests: curve vs fallback, with `carry_source` recorded.
- All-gates test: a pair-day failing 3 gates returns all 3 reason codes and 11 results.
- Convergence-to-mean test: a constant structural offset never triggers an alert.
- Sizing tests: the 4:5 fixture, and residual sign.
- Corwin-Schultz fixture (≈ 0.000424), and fallback when S ≤ 0.
- Cost tests: CTT on sell only, stamp duty on buy only, GST base.
- Strict spec mode: a `DISPUTED` spec forces `SPEC_UNVERIFIED` everywhere.
- Explainer numeric guard: an injected number not in the JSON is rejected.
- Hindi template renders for every reason code.
- Baselines run deterministically with a fixed seed.
- Trial registry: every backtest config is logged, and the DSR changes when `n_trials` changes.

## 10. Security
- Secrets in environment variables. `.env.example` contains no values.
- Symbol allow-list. Bounded dates, grams and lots.
- Admin token and rate limiting. Read-only database connection for public routes.
- No user text reaches an LLM. LLM output is numeric-guarded.
- Disclaimer on every screen: "Analytics only — not investment advice."

## 11. Design Principle for Future Live Trading
```python
class ExecutionAdapter:
    def submit_pair_order(self, signal): ...
    def cancel(self, order_id): ...
    def positions(self): ...
    def reconcile(self): ...
```
`PaperExecutionAdapter` comes first. Any future `BrokerExecutionAdapter` sits behind an independent risk manager. The quant code never calls a broker.
