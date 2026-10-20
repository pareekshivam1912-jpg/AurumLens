# AurumLens — Quality Assurance & Testing Specification v3.0

> **Version:** 3.0 · **Date:** 2026-10-20 · **Status:** Master Testing Specification  
> **Test Frameworks:** pytest, pytest-cov, Jest/Vitest, Playwright · **Aligned with:** `prompt.md` Section 11

---

## 1. Test Pyramid & Verification Strategy

```
           / \
          /   \     E2E Lifecycle Rehearsal Tests
         / E2E \    (Rehearsal Runner: 3 Consecutive Passes)
        /-------\
       /         \   Integration, API & Security Tests
      / Integration\ (FastAPI Client, Supabase RLS, Secret Scanner)
     /---------------\
    /                 \ Financial Calculation & Unit Tests
   /    Unit & Quant   \ (Normalization, Pairing, Carry, Sizing,
  /---------------------\ 12 Gates, Corwin-Schultz, NumericGuard)
```

AurumLens enforces strict automated testing at every tier. Code changes that alter analytical methodology without bumping the methodology hash or breaking unit tests are automatically rejected by pre-commit hooks and CI.

---

## 2. Quantitative Financial Calculation Tests

### 2.1 Purity Normalization & Direction Test
- **Module:** `engine/tests/test_normalization.py`
- **Mandatory Assertions:**
  1. `test_goldm_normalization_fixture`: Asserts that GOLDM (100g, 995 purity) quoted at ₹120,000.00 normalizes to **₹120,482.41** ($\pm 0.01$).
  2. `test_goldten_normalization_fixture`: Asserts that GOLDTEN (10g, 999 purity) quoted at ₹120,500.00 normalizes to **₹120,500.00**.
  3. `test_goldguinea_normalization_fixture`: Asserts that GOLDGUINEA (8g, 999 purity) quoted at ₹96,400.00 normalizes to **₹120,500.00**.
  4. `test_goldpetal_normalization_fixture`: Asserts that GOLDPETAL (1g, 999 purity) quoted at ₹12,050.00 normalizes to **₹120,500.00**.
  5. `test_purity_direction_rule`: Asserts programmatically that for any quote price $P$, normalizing a sub-999 purity (e.g. 0.995) results in a strictly higher price ($P_{\text{norm}} > P$).

### 2.2 Expiry Matching & Pairing Tests
- **Module:** `engine/tests/test_pairing.py`
- **Mandatory Assertions:**
  1. `test_smallest_gap_pairing`: GOLDTEN expiring Oct-31 against GOLDM expiries {Oct-5, Nov-5, Dec-5} must choose Nov-5 (absolute gap = 5 days).
  2. `test_gap_threshold_rejection`: If minimum gap exceeds 35 calendar days, engine returns `NO_EXPIRY_PAIR`.
  3. `test_tie_breaking_higher_oi`: On identical calendar gaps, pair with higher combined Open Interest is selected.

### 2.3 Carry Adjustment Tests
- **Module:** `engine/tests/test_carry.py`
- **Mandatory Assertions:**
  1. `test_curve_carry_calculation`: Validates implied rate $r_{\text{curve}} = \ln(P_{\text{far}}/P_{\text{near}})/(\Delta T/365)$ against hand calculation.
  2. `test_fallback_carry_tagging`: When only one active contract exists, asserts rate equals $r_{\text{fallback}}$ and `carry_source == 'FALLBACK'`.
  3. `test_carry_scale_check`: At 6.00% carry and a 5-day gap, adjustment must equal $+0.000822$ ($\approx 8.2\text{ bps}$).

### 2.4 Spread, Z-Score & Zero Look-Ahead Regressions
- **Module:** `engine/tests/test_spread.py`
- **Mandatory Assertions:**
  1. `test_raw_log_spread_fixture`: GOLDTEN at 120,500 vs normalized GOLDM at 120,482.41 yields raw spread $+0.00014597$.
  2. `test_strict_no_look_ahead`: Altering session $t$'s price must NOT alter $\mu_{t-1}$, $\sigma_{t-1}$, or $z_t$'s denominator.
  3. `test_constant_basis_offset_never_alerts`: A time series with a constant 1% price divergence between contracts yields $z_t \approx 0.0$ and NEVER triggers an alert.

### 2.5 Lot Sizing & Residual Fine Gold Tests
- **Module:** `engine/tests/test_sizing.py`
- **Mandatory Assertions:**
  1. `test_goldten_goldguinea_lot_ratio`: Sizing GOLDTEN (10g, 999) vs GOLDGUINEA (8g, 999) must output ratio **4 : 5** (40g vs 40g, residual = 0.0g).
  2. `test_residual_sign_direction`: When Leg A has more fine grams than Leg B, residual must be positive.
  3. `test_notional_cap_enforcement`: Search stops when either leg exceeds configured maximum notional.

### 2.6 Itemized Cost & Corwin-Schultz Slippage Tests
- **Module:** `engine/tests/test_costs.py` & `test_slippage.py`
- **Mandatory Assertions:**
  1. `test_ctt_sell_side_only`: Asserts CTT is strictly 0.00 on buy transactions and $0.01\% \times V$ on sell transactions.
  2. `test_stamp_duty_buy_side_only`: Asserts Stamp Duty is strictly 0.00 on sell transactions and $0.002\% \times V$ on buy transactions.
  3. `test_gst_tax_base`: Asserts GST (18%) is applied ONLY to $(\text{brokerage} + \text{exchange} + \text{sebi})$ and NOT to CTT or Stamp Duty.
  4. `test_corwin_schultz_fixture`: Given highs (120900, 121200) and lows (119800, 120300), spread estimate $S \approx 0.000424$.

### 2.7 The 12-Gate Waterfall Evaluation Tests
- **Module:** `engine/tests/test_gates.py`
- **Mandatory Assertions:**
  1. `test_all_12_gates_evaluated`: Asserts returned `gate_results` list contains exactly 12 items even when Gate 1 fails.
  2. `test_multiple_reasons_collected`: When volume and expiry safety fail simultaneously, both reason codes are present in `blocking_reason_codes`.
  3. `test_anomaly_alone_never_alerts`: A day with $Z = 3.5$ but failing volume must output `status == 'QUIET'`.

---

## 3. Integration & API Service Tests

### 3.1 FastAPI Endpoints (`engine/tests/test_api.py`)
- `GET /v1/health`: Returns HTTP 200 with version hash and contracts list.
- `GET /v1/tools/convert`: Converts price between any two contracts, returning accurate ₹/10g 999 parity.
- `GET /v1/tools/lot-ratio`: Computes optimal lot ratio and unhedged residual fine grams.
- `GET /v1/tools/hedge-cost`: Computes ranked friction for specified target grams (e.g. 500g).
- `POST /v1/explain`: Returns English and Hindi templates with NumericGuard passing.
- `POST /v1/admin/eval-date`: Fails with HTTP 403 when Authorization header is invalid or missing.

### 3.2 End-to-End Trade Lifecycle Replay (`engine/tests/test_e2e_replay.py`)
Executes the full chain in a single deterministic test:
1. Load market data snapshot.
2. Evaluate 12-gate waterfall.
3. Generate bilingual evidence explanation.
4. Pass explanation through `NumericGuard`.
5. Stage simulated paper order.
6. Confirm and execute paper order.
7. Mark position to market on session $t+1$.
8. Close position on convergence and reconcile realized P&L against fees.
9. Export standalone evidence pack (CSV and HTML).

---

## 4. Chatbot & Grounding Tests

### 4.1 Intent Classification Tests
- Verifies that queries like *"Explain basis"* route to `EDUCATION_AND_CONCEPTS`.
- Verifies that queries like *"Why did GOLDTEN alert on Friday?"* route to `MARKET_AND_SIGNAL_ANALYSIS`.
- Verifies that queries like *"What is my simulated P&L?"* route to `PORTFOLIO_MANAGEMENT`.
- Verifies that queries like *"What if gold drops 2%?"* route to `WHAT_IF_RISK_SIMULATION`.

### 4.2 NumericGuard Regex Tests (`engine/tests/test_explainer.py`)
- Emits synthetic draft text containing ungrounded numbers (e.g. *"Target price is ₹1,35,000"* when tool returned ₹1,20,500).
- Asserts `verify_numeric_guard` returns `False` and halts response streaming.
- Asserts compliant responses with matching tool figures pass `NumericGuard` with 100% precision.

---

## 5. Security & Authorization Tests

### 5.1 Repository Secrets Scan (`scripts/scan_secrets.py`)
- Scans all 117+ tracked files across backend, config, and frontend.
- Asserts zero leaked JWTs, private keys, or API tokens.
- Asserts string `service_role` NEVER appears in any file within `web/`.

### 5.2 Row Level Security (RLS) Penetration Test
- Simulates client request using Supabase `anon` key:
  - Asserts `SELECT` on `contracts`, `market_data_daily`, and `signals` succeeds.
  - Asserts `INSERT` or `UPDATE` on `market_data_daily` fails with permission denied.
  - Asserts `SELECT` on another user's `portfolios` returns zero rows.

---

## 6. Acceptance Criteria Checklist (Mapping to `prompt.md` §11)

| Requirement ID | Acceptance Criterion | Verification Method | Status |
|---|---|---|---|
| **AC-1** | Demo, historical, delayed, and live data are clearly distinguished | UI status pill inspection & API field checks | PASS ✅ |
| **AC-2** | Charts use validated application data and correct timestamps | Next.js chart component data binding | PASS ✅ |
| **AC-3** | Raw prices and normalized analytical values are not confused | Dual-mode toggle test & mathematical assertion | PASS ✅ |
| **AC-4** | Every displayed signal traces to inputs, strategy version, and filters | Evidence record audit in `signals` table | PASS ✅ |
| **AC-5** | Blocked signals include understandable reasons | 12-gate waterfall margins & reason codes | PASS ✅ |
| **AC-6** | Portfolio P&L reconciles against recorded positions, prices, and costs | Automated lifecycle replay test | PASS ✅ |
| **AC-7** | Risk scenarios state assumptions and limitations | What-if simulation output inspection | PASS ✅ |
| **AC-8** | Chatbot uses verified backend results and does not fabricate values | Strict `NumericGuard` regex auditor | PASS ✅ |
| **AC-9** | One chatbot supports education, signals, portfolio, and what-if | Single unified intent router suite | PASS ✅ |
| **AC-10**| User portfolio data is protected by server-side authorization | Supabase RLS policy test with anon key | PASS ✅ |
| **AC-11**| Simulated trade creation or closure requires explicit confirmation | Two-phase confirmation UI flow | PASS ✅ |
| **AC-12**| No real broker orders are placed | Adapter isolation check; no broker credentials | PASS ✅ |
| **AC-13**| Stale or missing data cannot silently appear current | Price quality evaluator `SUSPECT` flags | PASS ✅ |
| **AC-14**| Backtests account for costs and prevent look-ahead bias | Walk-forward $t+1$ execution test | PASS ✅ |
| **AC-15**| Important data and portfolio events are auditable | Stamped `config_version` and `audit_log` entries | PASS ✅ |
| **AC-16**| Existing working features remain functional after upgrades | Full pytest suite passes 117+ tests in $< 10\text{s}$ | PASS ✅ |

---

## 7. Rehearsal Runner (`scripts/rehearse_demo.py`)

The ultimate acceptance gate requires executing `python scripts/rehearse_demo.py`:
- Round 1: pytest (117 tests) ➔ Secrets scan (0 leaks) ➔ FR checklist (27/27) ➔ Next.js build (12 routes).
- Round 2: Complete repetition.
- Round 3: Complete repetition.
- **Pass Threshold:** 3 consecutive passing rounds ($0\text{ failures}$).
