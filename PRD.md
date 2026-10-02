# AurumLens — Product Requirements Document (PRD) v2.0

> **Version:** 2.0 (MVP revision) · **Date:** 2026-10-01 · **Supersedes:** PRD v1
> **What changed:** see `CHANGELOG.md`. In short, v2:
> - fixes the normalization direction and expiry pairing;
> - adds a facts register and data-quality rules;
> - makes all gates evaluate fully;
> - adds hedging tools and an explainability layer;
> - keeps walk-forward validation, adding the Deflated Sharpe Ratio as a reported metric.

---

## 1. Product Summary
**AurumLens** is an MCX gold relative-value intelligence platform. It compares GOLDM, GOLDTEN, GOLDGUINEA and GOLDPETAL on a common fine-gold price basis. Before comparing, it adjusts for contract specifications, expiry differences and carry. It flags cross-contract pricing as unusual only when the apparent edge survives modeled costs, slippage, liquidity filters and expiry/tender safety rules.

There is a secondary MVP use case: **hedging-cost analytics**. A jeweller or bullion participant can see what it costs to hedge a given quantity of gold through each contract, and how much gold would be left unhedged.

AurumLens is **not a gold-direction prediction system**. It never claims that gold will rise or fall. It is analytics, not investment advice.

## 2. Product Objective
Build a reproducible system that:
1. Ingests and validates MCX Bhavcopy data, both before and after the October 2023 platform migration.
2. Stores data by `(symbol, expiry_date, trade_date)`.
3. Normalizes every contract to **₹ per 10 g of 999 fine gold**.
4. Pairs contracts with the **smallest expiry gap** and adjusts for carry.
5. Calculates the log basis/spread and an anomaly score using history through `t-1` only.
6. Evaluates **every** gate and produces a `QUIET` or `ALERT` decision with full evidence.
7. Explains quiet days through a "nearest miss" view, not only alert days.
8. Validates the method with walk-forward backtesting net of costs, against simple baselines.
9. Explains every signal with traceable evidence, in plain English and Hindi.
10. Provides hedging tools: a contract converter, a cheapest-to-hedge calculator and a lot-ratio sizer.
11. Presents results in a judge-friendly dashboard with replay.
12. Supports paper-trade simulation. Real broker execution remains a post-MVP extension.

## 3. Target Users
| User | Primary need | Main screens |
|---|---|---|
| Retail MCX gold traders | Is any contract unusually rich or cheap after costs? | Overview, Pair Analysis, Alerts |
| Small prop/arbitrage desks | Evidence, backtest, cost realism | Backtest, Evidence export |
| Jewellers / bullion hedgers | Cheapest and most precise way to hedge N grams | Hedge Tools |
| Finance students / researchers | Transparent, reproducible methodology | Methodology, Backtest |

## 4. MVP Contract Universe
GOLDM, GOLDTEN, GOLDGUINEA, GOLDPETAL.

Contract specifications are configuration-driven. Each must be verified against official MCX material before it is used for analysis (see §5).

## 5. Facts Register (status as of v2)
Every external fact the analytics depend on is tracked with one of these statuses:
- `VERIFIED_OFFICIAL`: confirmed from an MCX or SEBI document.
- `SECONDARY`: from a broker or research source.
- `DISPUTED`: sources disagree.
- `TO_VERIFY`: unknown.

Only `VERIFIED_OFFICIAL` facts may drive results shown as real. The other statuses are allowed in research mode, with a watermark (see R24).

| ID | Fact | Current value (unconfirmed unless stated) | Status | Notes |
|---|---|---|---|---|
| F1 | GOLDM trading unit / quote basis | 100 g / ₹ per 10 g | SECONDARY | Broker sources agree |
| F2 | GOLDM expiry | 5th of contract month | SECONDARY | |
| F3 | GOLDTEN unit / quote basis | 10 g / ₹ per 10 g | SECONDARY | |
| F4 | GOLDTEN launch date | April 2025 | SECONDARY | Confirm from MCX circular and first Bhavcopy appearance |
| F5 | GOLDGUINEA unit / quote basis | 8 g / ₹ per 8 g | SECONDARY | |
| F6 | GOLDPETAL unit / quote basis | 1 g / ₹ per 1 g | SECONDARY | |
| F7 | GUINEA / PETAL / TEN expiry | Last day of contract month | SECONDARY | Check circular MCX/TRD/456/2025 (launch calendar modification) |
| F8 | Purity: GOLDM | 995 | SECONDARY | |
| F9 | Purity: GOLDGUINEA | 995 base with 999/995 premium **or** 999 | **DISPUTED** | Changes normalization by about 0.4% |
| F10 | Purity: GOLDTEN, GOLDPETAL | 999 | SECONDARY | |
| F11 | Delivery premium for 999 delivered against a 995 contract | Rate × 999/995 | SECONDARY | |
| F12 | Staggered delivery / tender period | Last 3 trading days (from Jan 2025 expiries; previously 5) | SECONDARY | SEBI circular to be located |
| F13 | Bhavcopy schema change | MCX moved to the TCS CDP platform in October 2023 | SECONDARY | Exact date and columns from real files |
| F14 | Settlement price field in Bhavcopy | Unknown | TO_VERIFY | Determines the price source (R19) |
| F15 | Coin making-charge premium in GUINEA/PETAL | Unknown | TO_VERIFY | A stable premium is absorbed by the rolling mean (R21) |
| F16 | Cost schedule (brokerage, CTT, exchange, SEBI, stamp, GST) | See `config/costs.yaml` candidates | SECONDARY | Brokerage is broker-specific |

## 6. Core Product Principle
**Same underlying commodity, different contract designs.**

Raw contract prices must never be compared directly. Every comparison accounts for:
- quote basis
- trading unit
- purity
- expiry date
- carry
- price freshness
- liquidity
- transaction costs
- slippage
- lot-ratio mismatch
- tender/expiry risk

## 7. Locked Analytical Rules

### Carried forward from v1 (unchanged meaning)
- **R1 Gold-only MVP.** Only the four contracts above are analyzed.
- **R2 Contract-level identity.** Store observations by `symbol + expiry_date + trade_date`. Never build the core model on a stitched continuous series.
- **R3 Validate source dates.** The requested date must equal the returned Bhavcopy date. Holiday, invalid or malformed responses are rejected and logged.
- **R4 Normalize before comparison.** See R16 for the exact basis and direction.
- **R5 Expiry-aware matching.** Superseded in detail by R17.
- **R6 Carry adjustment.** Superseded in detail by R18.
- **R7 Historical anomaly score.** Rolling z-score, with an optional robust median/MAD variant, using information through `t-1` only.
- **R8 A statistical anomaly is not sufficient** to produce an actionable alert.
- **R9 Cost hurdle.** Expected convergence must exceed `round-trip costs + slippage + safety buffer`.
- **R10 Liquidity gate.** Both legs must pass the volume and OI requirements. A settlement price is not an executable fill.
- **R11 Expiry/tender safety.** Block signals inside the configured unsafe window.
- **R12 Quiet by default.** If any required gate fails or an input is missing, the status is `QUIET`.
- **R13 No look-ahead.**
- **R14 Walk-forward validation** with rolling train/test folds and a final untouched holdout.
- **R15 Honest results.** Report gross, costs, slippage, net, strategy P&L and residual gold P&L separately. "No persistent edge after costs" is a valid result.

### New in v2
- **R16 Normalization basis and direction.** The common basis is **₹ per 10 g of 999 fine gold**:
  `P_norm = P_quoted × (10 / quote_basis_g) × (0.999 / purity)`.
  A lower-purity contract normalizes **upward**. For example, GOLDM at 995 gives × 0.999/0.995 = × 1.00402. A unit test must assert this direction.
- **R17 Smallest-gap expiry pairing.** For each pair and date, choose the combination of active contracts with the **smallest absolute expiry gap**, subject to a configured `max_expiry_gap_days`. Example: GOLDTEN Oct-31 pairs with GOLDM **Nov-5** (5 days), not Oct-5 (26 days).
- **R18 Carry source hierarchy.**
  1. Implied carry from the same symbol's own term structure on date `t`, when two liquid expiries exist.
  2. Otherwise, a configured fallback rate.

  Every row records `carry_source ∈ {CURVE, FALLBACK}`. Optionally, `FALLBACK` can be configured to block alerts.
- **R19 Price source and freshness.** Use settlement price when the Bhavcopy provides it, otherwise close. The choice is configured and recorded per row. A price is `SUSPECT` (and the pair is `QUIET`) in either case:
  - volume is below `min_volume_for_price`;
  - close and settlement diverge by more than `stale_gap_threshold`.
- **R20 Evaluate every gate.** All gates run on every pair-day, even after one fails. The decision is `ALERT` only if all pass. Every failure is stored as a reason code, and the margin by which each gate passed or failed is also stored.
- **R21 Converge to the rolling mean, not zero.** Expected convergence is measured from the current spread to the rolling mean through `t-1`. A persistent structural premium (for example, coin making charges) is therefore not treated as mispricing.
- **R22 Lot ratio and residual exposure.** Every simulated position uses an integer lot ratio that minimizes the leftover unhedged fine grams. The residual is reported and attributed as residual gold P&L.
- **R23 Stationarity tests are diagnostics, not gates.** ADF and Engle-Granger results may be shown, computed only on training or `≤ t-1` data. They never decide an alert.
- **R24 Spec strictness mode.**
  - `spec_mode: strict`: any contract whose spec status is not `VERIFIED_OFFICIAL` forces `QUIET`, with reason `SPEC_UNVERIFIED`.
  - `spec_mode: research`: computation is allowed, but every output and screen carries a visible "unverified specs" watermark.
- **R25 Explanations never compute numbers.** Plain-language explanations (template-based, optionally rewritten by an LLM) are produced only from the stored signal JSON. Every number in an explanation must appear in that JSON.

## 8. Spread Definition
`s_t = ln(P_norm_A) − ln(P_norm_B) + carry_adj_t`

Here `carry_adj_t = r_t × (T_B − T_A) / 365`, where `T` is the expiry date of each leg and `r_t` comes from R18.

`z_t = (s_t − mean(s_{t−L..t−1})) / std(s_{t−L..t−1})`, where `L = lookback_window`.

## 9. Parameters — Configurable, Not Hard-coded
Every value below lives in versioned config. Values marked `TO_VALIDATE` are placeholders and not business rules.

| Group | Parameters |
|---|---|
| Scoring | `lookback_window`, `min_history_obs`, `entry_z`, `exit_z`, `score_method` (`zscore`/`mad`) |
| Pairing / carry | `max_expiry_gap_days`, `carry_fallback_rate`, `block_on_carry_fallback` |
| Price quality | `price_source` (`settlement`/`close`), `min_volume_for_price`, `stale_gap_threshold` |
| Liquidity | `min_volume` (absolute or percentile), `min_oi`, `volume_sma_days` |
| Expiry | `unsafe_expiry_window_days` (proposed 5 = 3-day tender window + 2-day buffer, `TO_VALIDATE`) |
| Costs | brokerage (flat/percent/cap), CTT, exchange, SEBI, stamp, GST rates; `safety_buffer` |
| Slippage | `slippage_model` (`corwin_schultz`/`fixed_bps`), `fallback_bps` per symbol, `cs_window` |
| Convergence | `convergence_capture_ratio` (share of the gap to the mean expected to close) |
| Holding / backtest | `max_holding_days`, `train_window`, `test_window`, `holdout_start`, `execution_price` |
| Sizing | `max_lots_per_leg`, `max_notional_inr` |
| Modes | `spec_mode` (`strict`/`research`) |

## 10. Signal Decision
```text
spec ok (per spec_mode)
AND valid data AND prices not SUSPECT
AND valid expiry pair (gap ≤ max_expiry_gap_days)
AND sufficient history
AND |z| ≥ entry_z
AND both legs pass liquidity
AND both legs outside the unsafe expiry/tender window
AND expected convergence > costs + slippage + safety buffer
AND not a duplicate of an open alert
=> ALERT, otherwise QUIET
```
All conditions are evaluated (R20). The UI shows them as a **gate waterfall**.

## 11. Signal Output (Evidence Record)
Each pair-day record, whether `ALERT` or `QUIET`, contains:
- **Identity:** pair, trade date, actual contracts and expiries, expiry gap.
- **Prices:** quoted prices, price source and quality flag, normalized prices.
- **Spread and score:** carry value and `carry_source`, unadjusted and adjusted log spread, rolling mean/std, z-score, which leg is rich and which is cheap.
- **Economics:**
  - expected convergence in ₹;
  - cost breakdown per component;
  - slippage estimate and the model used;
  - safety buffer;
  - net expected edge.
- **Liquidity:** volume, volume SMA and OI for both legs.
- **Expiry:** days to expiry for each leg.
- **Sizing:** lot ratio and residual fine grams.
- **Gates:** pass/fail and margin for every gate, plus reason codes.
- **Nearest miss:** how close the pair came to alerting.
- **Versioning:** config version, dataset version, and the source file hash for each leg.

## 12. Backtest Rules
- The signal is calculated from day `t` information. Simulated entry happens at `t+1` using `execution_price` (settlement or close), adjusted adversely by modeled slippage.
- Store the actual contracts held and the integer lot quantities.
- Exit on whichever comes first:
  - reversion (`|z| ≤ exit_z`);
  - time stop (`max_holding_days`);
  - entering the unsafe expiry window.
- Persist every simulated trade.
- Report gross P&L, costs, slippage, net P&L, strategy (spread) P&L and residual gold P&L separately.
- **Baselines (mandatory):**
  - "always quiet" (₹0);
  - "random entry with the same holding rules and costs" (seeded, many runs).
- **Metrics:** net P&L, trade count, hit rate, average net per trade, max drawdown, Sharpe, and the **Deflated Sharpe Ratio**, computed from the number of configurations logged in the trial registry.
- **Sensitivity analysis** (stretch) uses training folds only.
- The final holdout is never used for parameter selection and is reported separately.

## 13. Functional Requirements

### Core (from v1)
- **FR1** Download Bhavcopy for a date or date range, with polite caching.
- **FR2** Validate dates and schema, and normalize source formats (pre- and post-October 2023 adapters).
- **FR3** Store contract-level raw and processed data.
- **FR4** Maintain a configuration-driven contract master with the facts register.
- **FR5** Compute normalized prices.
- **FR6** Perform smallest-gap expiry matching and carry adjustment.
- **FR7** Compute the log spread and anomaly score.
- **FR8** Apply the price-quality, cost, liquidity and expiry gates, evaluating all of them.
- **FR9** Run walk-forward backtests and persist trades and folds.
- **FR10** Produce P&L attribution.
- **FR11** Provide the dashboard screens listed in §15.
- **FR12** Provide replay mode for historical dates.
- **FR13** Provide paper-trade simulation.
- **FR14** Send optional Telegram alerts for newly gated signals.
- **FR15** Expose read-only analytical APIs.

### MVP additions (v2)
- **FR16 Gate waterfall.** Show every gate per pair-day, with pass/fail, margin and reason code.
- **FR17 Nearest-miss meter.** On quiet days, show which pair came closest to alerting and by how much (z vs threshold, edge vs hurdle, liquidity vs minimum).
- **FR18 Data-quality flags.** Flag zero or low-volume prices, close/settlement divergence, missing fields, rejected dates and duplicates, and show them on the Data Health screen.
- **FR19 Cost breakdown panel.** Show every cost component in ₹ for each alert and each trade.
- **FR20 Spec trust panel.** Show each contract spec with its source, verified date and status badge (`VERIFIED_OFFICIAL`, `SECONDARY`, `DISPUTED`, `TO_VERIFY`).
- **FR21 Backtest baselines.** Run "always quiet" and "random entry" baselines with the same costs.
- **FR22 Contract converter.** Enter any contract's quoted price and see its equivalent in ₹/10 g 999 and in each other contract's quote basis.
- **FR23 Cheapest-to-hedge calculator.** For a target quantity of fine grams, show for each contract:
  - lots needed;
  - effective grams and residual grams;
  - normalized price;
  - round-trip costs;
  - cost per 10 g;
  - liquidity status.

  This is analytics only, with a disclaimer.
- **FR24 Lot-ratio sizer.** For a chosen pair, find the integer lot ratio that minimizes residual fine grams within the configured caps.
- **FR25 Event markers.** Read dated market events from config (each with a source and verified flag) and show them on price and spread charts.
- **FR26 Plain-language explanations.** Template-based English and Hindi explanations of each evidence record. An optional LLM rewrite must pass the numeric guard (R25).
- **FR27 Evidence pack export.** Export any alert or pair-day as CSV and printable HTML/PDF, with all inputs, gates, versions and source hashes.

### Stretch (only after FR1–FR27 pass Phase 7 checks)
- **FR28** Replay player that steps through a date range automatically.
- **FR29** Parameter-sensitivity heatmap on training folds only.
- **FR30** Daily Telegram digest (status of all pairs plus the nearest miss).
- **FR31** Paper-trade journal timeline.
- **FR32** Premium over a spot reference (for example, IBJA), only if a reliable historical source is confirmed.

## 14. Non-functional Requirements
- **Reproducible:** the same dataset version and config version give identical results.
- **Traceable:** every number in the UI traces to stored source and derived rows.
- **Offline demo:** works entirely from cached data.
- **Performance:** a full MVP backtest runs in under 60 seconds on a normal laptop.
- **Secrets:** never committed. Read-only public API. Privileged actions require a token.
- **Clarity:** a non-trader can tell `QUIET` from `ALERT`, and understand one signal, within about 30 seconds.
- **Bilingual explanations:** English and Hindi.
- **Disclaimer:** "Analytics only — not investment advice" is visible on every screen.

## 15. MVP Screens
1. **Overview:** market status (`QUIET`/`ALERT`), pair status cards, nearest miss, data freshness, spec-mode watermark.
2. **Pair Analysis:** contracts and expiries, normalized prices, adjusted spread, z-score with entry and exit bands, gate waterfall, cost breakdown, event markers.
3. **Backtest & Attribution:** walk-forward fold table, holdout, baselines, gross/cost/slippage/net, strategy vs residual gold P&L, Deflated Sharpe Ratio, trade ledger.
4. **Contract Calendar:** expiries, unsafe tender windows, liquid windows, events.
5. **Alert Log / Evidence:** alerts, explanations (English and Hindi), evidence export.
6. **Hedge Tools:** converter, cheapest-to-hedge, lot-ratio sizer.
7. **Data Health & Spec Trust:** ingestion log, rejects, quality flags, facts register.
8. **Methodology:** a static explanation of the pipeline, formulas and limitations.
9. **Paper Trade panel** (optional).

## 16. Explicit MVP Exclusions
- Real-money broker order placement.
- Intraday tick or order-book engine.
- Gold-direction prediction of any kind (deep learning or otherwise).
- User payments and accounts.
- Mobile app.
- Commodities other than the four gold contracts.
- Synthetic data presented as real results.
- CPCV as the primary validation method (possible future research; walk-forward stays primary).

## 17. Future Execution Extension
`Signal -> Risk Manager -> Execution Engine -> Broker Adapter -> Order Manager -> Position Monitor -> Exit Engine`.

Before live execution, the following are required:
- paper-trading evidence;
- broker reconciliation;
- partial-fill handling;
- a maximum slippage limit;
- position limits;
- daily loss limits;
- duplicate-order protection;
- a kill switch;
- compliance review.

## 18. MVP Success Criteria
A demo is successful when the team can:
- Load verified real MCX data, and show the facts register with statuses.
- Show the four contracts normalized correctly, with the GOLDM purity direction tested.
- Explain one pair end to end, including the gate waterfall and cost breakdown.
- Show a quiet day **with its nearest miss**.
- Show a historical alert day.
- Show a tempting anomaly correctly blocked by liquidity, expiry or a stale price.
- Run a walk-forward backtest on unseen data, compared with the baselines.
- Show costs and attribution transparently.
- Show the cheapest-to-hedge calculator for a sample quantity.
- Show a Hindi explanation of an alert.
- Run the whole demo offline from cached data.

## 19. Open Questions
1. GOLDGUINEA purity basis (F9).
2. Whether Bhavcopy includes a settlement price (F14).
3. GUINEA/PETAL coin premium (F15).
4. Exact Bhavcopy schema before and after the October 2023 migration (F13).
5. The content of circular MCX/TRD/456/2025 (F7).
6. Which broker's brokerage schedule to use as the default cost profile (F16).
