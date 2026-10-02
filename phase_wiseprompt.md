# AurumLens — Phase-wise Coding Prompts v2.1

> **Version:** 2.1 · **Date:** 2026-10-01 · **Supersedes:** v2.0
>
> Use these prompts in order, one phase per session. Never ask the coding agent to "build the whole project" in one pass.
>
> **v2.1 (Antigravity build):** the stack is Supabase + Stitch-designed Next.js + thin FastAPI + Python engine. Use Phases 0–8 below for the analytics. Then use the **Antigravity add-on prompts (A0–A10)** at the end of this file for MCP setup, the Supabase schema, the **Stitch design prompts**, and the frontend build.
>
> Where Phases 0–6 mention DuckDB, Parquet-only storage, Streamlit, or FastAPI for every read, the A-prompts override them. Background is in `ANTIGRAVITY_BUILD_PLAN.md`.

**Phase order in Antigravity:**

| Step | Use |
|---|---|
| 1 | A0 setup |
| 2 | Phase 0 (= A1) |
| 3 | A2 Supabase schema |
| 4 | Phase 1 + A3 notes |
| 5 | Phases 2–4 + A4–A6 notes |
| 6 | A7 Stitch (in parallel from step 4) |
| 7 | A8 frontend |
| 8 | Phase 6 + A9 notes |
| 9 | Phase 7 + A10 |

---

## MASTER PROMPT (prefix to every phase)
You are the senior engineer and quantitative software architect for AurumLens.

Before doing any work, read:
- `docs/PRD.md` (v2)
- `docs/Design.md` (v2)
- `docs/Phase.md` (v2)
- `docs/System_architecture.md` (v2)
- `CHANGELOG.md`
- `.cursorrules` (also used as `AGENTS.md`)
- `docs/ANTIGRAVITY_BUILD_PLAN.md`

These documents are the source of truth. If two of them conflict, stop and report the conflict. Do not pick one silently.

Rules:
- Never invent MCX/SEBI facts, file formats, costs or thresholds. Unknowns go into config with status `TO_VERIFY` or `TO_VALIDATE`.
- Normalize to ₹/10 g of 999, with lower purity normalizing **upward** (R16).
- Pair expiries by the **smallest gap** (R17). Record `carry_source` (R18).
- Never use future data. Never tune on test or holdout data.
- Evaluate **all** gates and store every reason code and margin (R20).
- Keep every calculation pure, reproducible, versioned and tested.
- Build only the requested phase, and only the [CORE] / [MVP+] / [STRETCH] items asked for.
- At the end, report:
  - files changed;
  - tests run, with results;
  - unresolved `TO_VERIFY` items;
  - whether the exit gate is met.

---

## PHASE 0 PROMPT — Source Verification & Skeleton
Implement Phase 0 only.

1. Create the repository structure from Design §3.
2. Create Pydantic config models for `contracts.yaml` (a value plus status, source and verified_at **per field**), `costs.yaml`, `strategy.yaml` and `events.yaml`. Include a `config_version` hash function.
3. Fill the YAML templates **only** with values you can cite. Everything else is `null` with a status. GOLDGUINEA purity stays `DISPUTED` until an official document resolves it.
4. Add `.env.example` (no values), pytest configuration and a CI workflow (tests plus secret scan).
5. Write `docs/VERIFICATION_CHECKLIST.md`, mirroring the PRD facts register F1–F16 with links to sources.
6. Create a `SourceAdapter` interface and one-day ingestion spikes for **both** the pre-October 2023 and the CDP format. Keep era-specific assumptions inside the adapters.

Do not implement signal logic or UI.

Exit report:
- Was one real day from each era downloaded, parsed and hand-checkable? If not, list the blockers and stop.
- Facts register status counts.

---

## PHASE 1 PROMPT — Historical Data Engine
Implement Phase 1 only, after the Phase 0 exit gate.

Build:
- downloader with polite caching;
- immutable raw store with sha256;
- `legacy` and `cdp` adapters producing the canonical schema;
- requested-date and schema validation;
- symbol cleanup and allow-list;
- expiry parsing;
- DuckDB tables `source_file`, `contract`, `daily_price`;
- Parquet dataset snapshots with `dataset_version`;
- reject log and ingestion report;
- the price-quality stage (`price_source`, `SUSPECT` with `quality_reason`).

Tests:
- date mismatch;
- holiday or missing file;
- malformed schema;
- symbol padding;
- expiry parsing in both eras;
- duplicate prevention (a conflicting duplicate is rejected, not overwritten);
- supported-symbol filter;
- SUSPECT flags for low volume and close/settlement divergence.

Do not implement normalization.

Report:
- rows by symbol and era;
- date range;
- rejected dates with reasons;
- duplicates;
- missing fields;
- SUSPECT counts;
- GOLDTEN's first observed date.

---

## PHASE 2 PROMPT — Normalization, Pairing, Carry & Sizing
Implement Phase 2 only. First confirm the facts-register status of every field used. If `spec_mode: strict` and a required field is not `VERIFIED_OFFICIAL`, stop.

Build pure functions:
- `normalize(price, spec, target) -> float` (R16; lower purity normalizes upward);
- `days_to_expiry`;
- `match_expiries(...)`: smallest gap within `max_expiry_gap_days`, with tie-breaks as in Design §6.4;
- `implied_carry_from_curve(...)`, with fallback, returning `(rate, carry_source)`;
- `log_spread(norm_a, norm_b, carry_rate, T_a, T_b)`, exposing raw, adjustment and adjusted values;
- `lot_ratio(spec_a, spec_b, caps) -> (n_a, n_b, residual_fine_g)`;
- `convert(price, from_symbol) -> dict`, for the converter tool.

Requirements:
- actual contract IDs travel with every derived row;
- no future data;
- no continuous series;
- intermediate values are exposed.

Synthetic fixtures (`synthetic: true`) must reproduce Design §6 exactly:
- 120,482.41;
- 120,500 for TEN, GUINEA and PETAL;
- the Nov-5 pairing;
- the 0.00014597 raw spread;
- the 4:5 ratio.

Also generate a research output: normalized prices for all four contracts, plus one pair's adjusted spread with carry-source shading. Stop once the fixtures match the engine output.

---

## PHASE 3 PROMPT — Signal Engine
Implement Phase 3 only.

Build:
- rolling z-score using data through `t−1`, plus the optional MAD score;
- history sufficiency;
- itemized cost model (Design §6.9) writing `cost_line`;
- Corwin-Schultz slippage with fallback (Design §6.10; the fixture gives ≈ 0.000424);
- expected convergence to the rolling mean (R21);
- an `evaluate_gates()` that returns **all 11** `GateResult`s with value, threshold, margin and reason code;
- spec-mode gate;
- duplicate suppression;
- evidence record builder;
- nearest-miss ranking (Design §6.12).

Keep all parameters in versioned config. Never choose thresholds by looking at profitability.

Tests must prove:
- a planted anomaly triggers;
- ordinary days stay quiet;
- each of these alone blocks an alert: cost, liquidity, expiry and SUSPECT price;
- multiple failures are all reported;
- a constant offset never alerts;
- strict mode with a DISPUTED spec forces QUIET;
- future-data changes leave past signals unchanged.

Return real-data examples of an ALERT, a QUIET with its nearest miss, and a blocked tempting anomaly, each with full gate evidence.

---

## PHASE 4 PROMPT — Walk-forward Backtesting
Implement Phase 4 only.

Build:
- chronological fold builder;
- train-only parameter selection, logging **every** tried config in the trial registry;
- frozen parameters per test fold;
- a final untouched holdout;
- signal on `t`, execution on `t+1` at `execution_price` with adverse slippage;
- actual contracts and integer lots from the sizer;
- itemized costs;
- exits: reversion, time stop, unsafe window;
- trade ledger;
- attribution (`residual_gold_pnl = residual_fine_g/10 × ΔP_norm(ref)`, strategy = gross − residual);
- baselines: always-quiet, and seeded random entry;
- metrics: Sharpe, max drawdown, hit rate, Deflated Sharpe Ratio using `n_trials`.

Report:
- gross P&L, itemized costs, slippage, net P&L;
- strategy and residual P&L;
- trade count;
- fold metrics;
- baseline comparison;
- DSR;
- the holdout, separately.

Add regression tests proving there is no train/test leakage and that the DSR responds to `n_trials`.

Do not change the methodology to improve results. A negative or no-edge result is acceptable and must be reported plainly.

---

## PHASE 5 PROMPT — API & Dashboard
Implement Phase 5 only.

- FastAPI endpoints per Design §7: bounded inputs, symbol allow-list, admin token, read-only database connection for public routes.
- Streamlit screens per Design §8:
  - [CORE] Overview, Pair Analysis (with gate waterfall), Backtest, Calendar, Alert Log;
  - [MVP+] Hedge Tools, Data Health & Spec Trust, Methodology.

Requirements:
- No formulas in the UI. Every number comes from the API, service or repository.
- Show data freshness, config version, dataset version and the spec-mode watermark.
- Show QUIET vs ALERT unmistakably. Show the nearest-miss card on quiet days.
- Every alert has an evidence panel and a cost breakdown.
- Event markers on charts and the calendar.
- Replay-date selection.
- Fully offline from cache.
- Disclaimer on every screen.

Add API tests (validation, auth, bounds) and UI error states (no data, stale data, rejected date).

---

## PHASE 6 PROMPT — Explanations, Alerts & Paper Trading
Implement Phase 6 only.

Build:
- English/Hindi template explainer keyed by status and reason codes;
- `numeric_guard`, with fallback to the template;
- an optional LLM rewrite adapter, disabled by default, that receives evidence JSON only;
- evidence pack export as CSV and HTML;
- Telegram adapter behind an interface;
- `PaperExecutionAdapter`: two-leg order object, simulated fills using the configured assumptions, position state, exits, paper P&L;
- duplicate-execution protection;
- audit log;
- representable partial or failed legs.

Rules:
- Do not connect to a real broker.
- Signal generation stays independent of execution.
- Paper execution consumes an already validated Signal.

Replay demo: historical day → signal → explanation (EN/HI) → paper pair trade → monitored position → exit → stored P&L → evidence pack.

---

## PHASE 7 PROMPT — Hardening & Demo
Implement Phase 7 only.

Perform:
- the FR1–FR27 checklist;
- the full test suite;
- a secret scan;
- an input-bound review;
- an offline-mode check;
- performance measurement (backtest under 60 s);
- a lineage spot-check on three numbers;
- a reproducibility check;
- an error-state review.

Prepare three deterministic demo scenarios from **real** historical data, never altered:
1. a clear gated alert;
2. a quiet day with a meaningful nearest miss;
3. a tempting anomaly blocked by liquidity, expiry or a stale price.

Add one hedge-tool scenario.

Write a demo README covering:
- setup;
- offline start;
- data refresh;
- running a backtest;
- replaying a date;
- reading an alert and its gate waterfall;
- using the hedge tools;
- known limitations;
- the facts-register status.

[STRETCH] only if everything above is green: replay player, sensitivity heatmap (train folds only), daily digest.

---

## PHASE 8 PROMPT — Future Live Execution (design only)
Do not implement live trading unless explicitly authorized after the MVP.

Design interfaces and tests for:
- an independent RiskManager;
- BrokerExecutionAdapter;
- pair-order orchestration;
- partial fills;
- cancellation;
- reconciliation;
- maximum slippage;
- exposure limits;
- daily loss limit;
- kill switch;
- idempotency;
- audit trail;
- failure recovery.

The quant engine never calls a broker.

Produce a readiness checklist before any real-money use, covering:
- broker API behavior;
- paper evidence;
- execution quality;
- risk limits;
- reconciliation;
- legal and compliance requirements;
- an explicit live-mode flag.

---
---

# ANTIGRAVITY ADD-ON PROMPTS (v2.1): Supabase MCP + Stitch MCP

> Paste the MASTER PROMPT first, then the A-prompt. Run each phase in a new agent conversation. Ask for the implementation plan first (Planning mode) and review it before execution.
>
> **MCP safety:**
> - `supabase` = read-only, scoped to the dev project.
> - `supabase-write` = disabled except during A2 and later reviewed migrations.
> - `stitch` = used only in A7 and A8.
>
> Never paste keys into chat.

---

## A0 PROMPT — Workspace & MCP Check
Do not write code yet. Verify the MCP setup:
1. Using the **stitch** MCP, list my Stitch projects (an empty list is fine).
2. Using the **supabase** MCP, list the tables in the `public` schema and show the project URL (`get_project_url`).
3. Using the **supabase** MCP, try to create a table named `mcp_write_test`. This **must fail**, because the server is read-only. Report the error.
4. Confirm that `AGENTS.md` exists at the repo root and summarize its 10 most important rules.

Report each step as PASS or FAIL. If step 3 succeeds, stop immediately and tell me: the read-only setting is wrong.

---

## A2 PROMPT — Supabase Schema, RLS & Storage
**Precondition:** I have enabled `supabase-write` for this phase only.

Use the **supabase-write** MCP:
1. Create migrations with `apply_migration`, one per logical step, and also save each under `supabase/migrations/`. Start from the SQL in `docs/ANTIGRAVITY_BUILD_PLAN.md` §5.1:
   - `001_core`: contract_spec, source_file, contract, daily_price;
   - `002_analytics`: pair_daily, gate_result, signal, cost_line, market_event;
   - `003_backtest_paper`: backtest_run, trial, trade, paper_position, audit_log;
   - `004_rls_and_views`: RLS on every table, SELECT-only policies, `v_latest_status`, Realtime on `signal`.
2. Keep every primary key, unique constraint and CHECK constraint in that SQL. In particular:
   - `daily_price (contract_id, trade_date)`;
   - `gate_result` with 11 gates;
   - `signal` unique on `(pair_id, trade_date, config_version)`;
   - `paper_position.signal_id` unique (duplicate-execution guard).
3. Create **no** insert, update or delete policies for anon or authenticated. Only the service role (the Python engine) writes.
4. Create the private Storage bucket `bhavcopy-raw`, with no public policies.
5. Run the security and performance advisors and fix every warning.
6. Generate TypeScript types into `web/lib/database.types.ts`.
7. **Do not put any formula in SQL.** Views only select and join.

Report:
- tables;
- policies per table;
- advisor results;
- migration file list.

Then remind me to **disable `supabase-write`**.

---

## A3 NOTES — add to the PHASE 1 PROMPT
- The raw store is the Supabase Storage bucket `bhavcopy-raw`, at path `{era}/{yyyy}/{yyyy-mm-dd}_{sha256[:12]}.csv`. Never overwrite a file. Also keep a local cache in `data/cache/`.
- Insert a `source_file` row for every file, OK or REJECTED.
- Write `contract` and `daily_price` through a repository layer that uses `SUPABASE_SERVICE_ROLE_KEY` from the environment. That key never goes in code or in `web/`.
- Keep Parquet snapshots with `dataset_version` for reproducibility and the offline demo.
- At the end, use the read-only **supabase** MCP (`execute_sql`) to report:
  - rows per symbol;
  - min/max trade_date;
  - REJECTED count;
  - SUSPECT count;
  - a duplicate check (`... group by contract_id, trade_date having count(*) > 1`, which must return 0 rows).

---

## A4–A6 NOTES — add to the PHASE 2, 3 and 4 PROMPTS
- Write results to `pair_daily`, `gate_result` (all 11 rows per pair-day), `signal` (full evidence JSON per PRD §11), `cost_line`, `backtest_run`, `trial` and `trade`.
- Stamp every row with `config_version` and `dataset_version`.
- At the end of each phase, use the read-only **supabase** MCP to spot-check 3 random rows against the Python output. Paste both side by side. Any mismatch fails the phase.

---

## A7 PROMPT — UI Design in Stitch
Use the **stitch** MCP.

**Step 1.** Create a Stitch project named **"AurumLens"**.

**Step 2.** Generate the first screen with the design-system prompt below. It defines the visual language for every screen.

**Step 3.** Generate screens 1–9 one at a time with `generate_screen_from_text`, using the prompts below **verbatim**. Use realistic sample data, labelled "Sample data".

**Step 4.** After each screen:
- fetch it with `get_screen`;
- save the HTML and screenshot to `web/design/stitch/<nn>-<slug>/`;
- check it against the PRD. Report any formula shown as UI logic, a missing disclaimer, a missing QUIET/ALERT clarity cue, or a missing gate evidence item.

**Step 5.** Extract the design tokens (colours, type scale, spacing, radii) into `web/design/tokens.json`.

**Step 6.** Stop and wait for my approval of each screen. Do not write frontend code in this phase.

### STITCH PROMPT 0 — Design system
```text
AurumLens: an analytics dashboard for Indian MCX gold futures (GOLDM, GOLDTEN, GOLDGUINEA, GOLDPETAL).
It compares the four contracts on one price basis (₹ per 10 g of 999 gold) and shows QUIET or ALERT.
Style: calm, professional, trustworthy fintech. Lots of white space, no clutter, no neon, no gradients on data.
Colours: ink #1E1E1E (text), slate #4B5563 (secondary text), deep gold #B7862C (brand accent, active nav,
key numbers), gold tint #FBF3E0 (highlight panels), panel #F7F5F0 (cards), border #E5E0D5,
QUIET green #2E7D32 with tint #E6F4EA, ALERT red #C62828 with tint #FDECEA.
Typography: Inter (or a similar clean sans-serif); tabular figures for all numbers; rupees in Indian grouping
(₹1,20,482); headings bold; body 14–16 px.
Layout: desktop 1440 px. Left sidebar navigation with logo "AurumLens" ("Lens" in gold) and 9 items:
Overview, Pair Analysis, Backtest, Calendar, Alerts, Hedge Tools, Data Health, Methodology, Paper Trading.
Top bar: replay date picker, data-freshness chip ("Data as of 30 Sep 2026"), config version chip.
Persistent footer: "Analytics only — not investment advice".
Status language: QUIET = green pill, ALERT = red pill. A non-trader must read the status within 3 seconds.
Components: cards with 12 px radius, PASS/FAIL pills, data tables with zebra rows, charts with thin lines.
Generate this as the Overview screen shell with empty content areas.
```

### STITCH PROMPT 1 — Overview
```text
AurumLens Overview screen using the established design system.
Top: a large market status hero: "Market status: QUIET", with the subtitle "No pair passed all 11 gates today"
(also design an ALERT variant: red, "1 active alert").
Below: 6 pair cards in a 3×2 grid (GOLDM/GOLDTEN, GOLDM/GOLDGUINEA, GOLDM/GOLDPETAL, GOLDTEN/GOLDGUINEA,
GOLDTEN/GOLDPETAL, GOLDGUINEA/GOLDPETAL). Each shows a status pill, the contracts with expiries, the z-score,
"Net edge vs hurdle" as a small bar (₹410 of ₹520), and gates passed "10 / 11".
Right column: a "Nearest miss" card, "GOLDM Nov / GOLDTEN Oct: blocked by cost hurdle, ₹110 short",
with a "View evidence" link.
Bottom strip: data health (last file, rejected dates 0, suspect prices 2) and "Specs: research mode",
shown as an amber banner variant reading "Some contract specs are unverified".
Label all numbers "Sample data".
```

### STITCH PROMPT 2 — Pair Analysis
```text
AurumLens Pair Analysis screen.
Header: the pair selector "GOLDM (exp 05 Nov 2026) vs GOLDTEN (exp 31 Oct 2026)", expiry gap "5 days",
carry source chip "Own curve", and a status pill.
Section 1: a line chart of the normalized prices of both legs (₹ per 10 g of 999), with event markers as small
pins on the x-axis.
Section 2: the adjusted log spread chart, and below it the z-score chart with shaded entry bands (±2.0) and an
exit band (±0.5).
Section 3: the "Gate waterfall", a vertical list of 11 rows: gate number, gate name, measured value,
threshold, margin, and a PASS/FAIL pill.
Rows: Spec status, Data validity, Price quality, Expiry pair, Carry, History, Anomaly, Liquidity,
Expiry safety, Cost hurdle (FAIL, highlighted red tint), Duplicate. Final result bar: "QUIET · blocked by the
cost hurdle · nearest miss ₹110".
Section 4: a cost breakdown table per leg and side: brokerage, exchange fee, SEBI fee, CTT (sell only),
stamp duty (buy only), GST, slippage, safety buffer, and total, against expected convergence.
Top-right: a "Replay date" picker and an "Export evidence" button.
```

### STITCH PROMPT 3 — Backtest & Attribution
```text
AurumLens Backtest screen.
Top KPI tiles: Net P&L, Trades, Hit rate, Max drawdown, Deflated Sharpe (with an info tooltip),
plus a badge "Config v2.1 · Dataset 2026-09-30".
Chart 1: an equity curve of the strategy vs two baselines ("Always quiet" as a flat line, and "Random entry"
as a shaded band).
Chart 2: a waterfall bar from Gross P&L → Costs → Slippage → Net P&L.
Chart 3: a stacked bar of Strategy (spread) P&L vs Residual gold P&L.
A walk-forward fold table: fold, train period, test period, frozen parameters, trades, net P&L.
A separate highlighted card: "Final holdout (run once)".
Trade ledger table: entry, exit, pair, actual contracts and lots, gross, costs, slippage, net, exit reason.
Include an honest empty-state variant: "No persistent edge after costs. This is a valid result."
```

### STITCH PROMPT 4 — Contract Calendar
```text
AurumLens Contract Calendar screen.
A horizontal timeline (Gantt style) covering 6 months, with one row per contract expiry
(GOLDM Oct/Nov/Dec, GOLDTEN Oct/Nov, GOLDGUINEA Oct/Nov, GOLDPETAL Oct/Nov).
Each bar shows the liquid trading window (gold tint), the unsafe window before expiry (red hatched,
"No new signals: 5 days"), and the expiry day marker.
A "Today" vertical line. Event pins above the timeline (for example "GOLDTEN launch", "Delivery period
change"), each with a "verified / unverified" tag.
A legend, and a side panel listing the next 5 expiries with days remaining.
```

### STITCH PROMPT 5 — Alert Log / Evidence
```text
AurumLens Alerts screen.
Filters: date range, pair, status (ALERT / QUIET), reason code.
Table: date, pair, status pill, direction ("GOLDPETAL rich vs GOLDM"), z-score, net edge, gates passed.
Clicking a row opens a right-side drawer "Evidence":
- the plain-language explanation with an EN / हिंदी toggle;
- a gate summary (11 compact pills);
- normalized prices of both legs;
- the cost breakdown;
- volume and OI for both legs;
- config and dataset version;
- source file hashes (shortened);
- buttons "Export CSV" and "Export HTML".
Show one ALERT example and one QUIET example.
```

### STITCH PROMPT 6 — Hedge Tools
```text
AurumLens Hedge Tools screen with 3 tabs.
Tab 1, Converter: one input "Price" plus a contract dropdown, then 4 result cards showing the equivalent price
in each contract's own quote basis and in ₹ per 10 g of 999.
Tab 2, Cheapest to hedge: input "Gold to hedge (grams)" = 500, then a ranked table with these columns:
contract, lots, effective grams, residual grams, normalized price, round-trip cost (₹), cost per 10 g,
orders needed, liquidity (OK / thin). Top row highlighted "Lowest cost".
Tab 3, Lot-ratio sizer: choose two contracts, then show the best integer lot ratio (for example 4 : 5),
residual fine grams 0, and a small comparison of alternatives.
Footer note: "Analytics only — not investment advice. Costs use the configured broker profile."
```

### STITCH PROMPT 7 — Data Health & Spec Trust
```text
AurumLens Data Health screen.
Top: freshness status, last successful file date, total files, rejected files, suspect prices.
Table 1, Ingestion log: requested date, returned date, format era (legacy / CDP), status, reason, file hash.
Table 2, Suspect prices: contract, date, reason ("volume below minimum", "close vs settlement gap").
Table 3, Facts register: fact, value, status badge (VERIFIED_OFFICIAL green, SECONDARY blue,
DISPUTED amber, TO_VERIFY grey), source link, verified date.
Example row: "GOLDGUINEA purity: DISPUTED".
A banner explaining strict vs research spec mode.
```

### STITCH PROMPT 8 — Methodology
```text
AurumLens Methodology screen: a clean, readable long-form page for judges and students.
Sections: 1) The idea ("same gold, different contract designs"), 2) Pipeline diagram (8 layers: sources,
ingestion, storage, quant core, decision engine, validation, service, experience), 3) Formulas shown as
readable math, not code (normalization, log spread with carry, z-score using history up to yesterday),
4) The 11 gates with one line each, 5) Validation (walk-forward, next-day execution, baselines, Deflated Sharpe,
untouched holdout), 6) Known limitations (daily data only, estimated slippage, unverified specs),
7) Disclaimer. Use a sticky table of contents on the left.
```

### STITCH PROMPT 9 — Paper Trading
```text
AurumLens Paper Trading screen, with a top banner always visible:
"Simulated: no real orders are placed".
KPI tiles: open positions, closed positions, paper P&L, last action.
Open positions table: signal date, pair, legs (contract, side, lots, entry price), mark-to-market P&L,
days held, exit rule status (reversion / time stop / expiry window).
Closed positions table with exit reason and net P&L.
An audit log timeline on the right (signal → order simulated → filled → monitored → exited).
A state example for a failed or partial leg, shown in amber.
```

---

## A8 PROMPT — Frontend Build (Next.js from Stitch)
**Precondition:** I have approved all 9 Stitch screens.

Build `web/` as a Next.js app (App Router, TypeScript, Tailwind), using `web/design/tokens.json` and the approved screens in `web/design/stitch/`. Use the **stitch** MCP (`get_screen`) whenever you need the latest version of a screen.

Rules:
- **Data access:**
  - Use `@supabase/supabase-js` with the **publishable key only** (get it with the supabase MCP's `get_publishable_keys`).
  - Use the generated `web/lib/database.types.ts`.
  - Read only the tables and views that RLS allows.
- **No formulas in the UI.** Hedge tools, explanations and evidence exports call the FastAPI service (`/v1/tools/*`, `/v1/signals/{id}/explain`, `/v1/signals/{id}/evidence.*`).
- **Live alerts:** subscribe to Supabase Realtime on `signal` and show a toast when a new ALERT arrives.
- **Replay:** the replay date picker queries `signal`, `gate_result` and `pair_daily` for the chosen date only.
- **States:** every screen has loading, empty, stale-data and error states, the disclaimer footer, and the research-mode banner when specs are unverified.
- **Offline:** configure through `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, so the app runs against a local Supabase for the offline demo.
- **Visual check:** use the built-in browser to screenshot each page beside its Stitch design. List the differences and fix them.

Exit report:
- screens done;
- screenshots;
- Lighthouse accessibility score for Overview and Pair Analysis (target ≥ 90);
- confirmation that `grep -r service_role web/` returns nothing.

---

## A9 NOTES — add to the PHASE 6 PROMPT
- **FastAPI routes:**
  - `/v1/tools/convert`, `/v1/tools/hedge-cost`, `/v1/tools/lot-ratio` (reuse the engine's functions; no new formulas);
  - `/v1/signals/{id}/explain?lang=en|hi`;
  - `/v1/signals/{id}/evidence.csv|html`;
  - `/v1/admin/*` behind the admin token.
- **Telegram:** after the engine writes an `ALERT` row, send it through the Telegram adapter, deduplicated by `signal_id`.
- **Paper trading:** paper positions are written to `paper_position`. The unique `signal_id` constraint is the duplicate-execution guard. Every action writes an `audit_log` row.
- **Demo:** replay a historical ALERT end to end. Show it arriving live in the UI through Realtime.

---

## A10 NOTES — add to the PHASE 7 PROMPT
- **Offline demo:**
  - `supabase start` (Docker);
  - `supabase db reset` (migrations + a seed built from the Parquet snapshot);
  - local FastAPI;
  - `next build && next start` against local URLs.
- **RLS checks with the anon key:**
  - inserts, updates and deletes must fail on every table;
  - `source_file`, `paper_position` and `audit_log` must not be readable while signed out.
- **Advisors:** run the Supabase security and performance advisors through the read-only MCP, and report results.
- **Secrets:** confirm there is no service-role key in `web/`, the build output or the git history.
- **Rehearsals:** three consecutive clean offline rehearsals.
