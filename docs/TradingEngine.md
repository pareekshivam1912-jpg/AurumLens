# AurumLens — Quantitative Trading Engine & Analytics Specification v3.0

> **Version:** 3.0 · **Date:** 2026-10-20 · **Status:** Master Quant Specification  
> **Supersedes:** Engine Design v2.0 · **Aligned with:** `prompt.md` Section 5 & 6

---

## 1. Mathematical Normalization (Rule R16)

Raw quoted prices across MCX gold derivatives cannot be compared directly due to differing delivery purities and contract quote conventions.

Every contract price is standardized to **₹ per 10 grams of 999 fine gold**:

$$P_{\text{norm}} = P_{\text{quoted}} \times \left( \frac{10}{\text{quote\_basis\_g}} \right) \times \left( \frac{0.999}{\text{purity}} \right)$$

### 1.1 The Purity Direction Rule
Lower purity must always normalize **UPWARD**. Because 995 gold contains less gold per gram than 999 gold, buying 10g of 999 gold requires paying more than 10g of 995 gold by a factor of $\frac{0.999}{0.995} \approx 1.0040201$.

### 1.2 Canonical Normalization Fixtures (Verified)
| Contract | Quoted Price ($P$) | Quote Basis | Purity | Multiplier Formula | Normalized Price ($P_{\text{norm}}$) |
|---|---|---|---|---|---|
| **GOLDM** | ₹1,20,000.00 | 10g | 0.995 | $1.0 \times \frac{0.999}{0.995}$ | **₹1,20,482.41** |
| **GOLDTEN** | ₹120,500.00 | 10g | 0.999 | $1.0 \times \frac{0.999}{0.999}$ | **₹1,20,500.00** |
| **GOLDGUINEA** | ₹96,400.00 | 8g | 0.999 | $\frac{10}{8} \times 1.0 = 1.25$ | **₹1,20,500.00** |
| **GOLDPETAL** | ₹12,050.00 | 1g | 0.999 | $\frac{10}{1} \times 1.0 = 10.0$ | **₹1,20,500.00** |

---

## 2. Expiry Pairing & Calendar Gap Minimization (Rule R17)

For any contract pair $(A, B)$ on session $t$:
1. Identify all active, valid contracts for $A$ and $B$ trading on day $t$.
2. For every combination, compute the absolute calendar gap in days:
   $$\Delta T = |T_A - T_B|$$
3. Filter combinations where $\Delta T \le \text{max\_expiry\_gap\_days}$ (default 35 days).
4. Select the pair with the **smallest calendar gap** $\Delta T$.
5. **Tie-Breaking Rule:** In the event of equal gaps, prioritize the pair with the nearer expiry date $T_A$. If still tied, prioritize higher combined Open Interest ($\text{OI}_A + \text{OI}_B$).
6. If no active pair satisfies $\Delta T \le 35\text{ days}$, the engine outputs `NO_EXPIRY_PAIR`.

*Worked Example:* GOLDTEN (Oct-31) against GOLDM active contracts {Oct-5, Nov-5, Dec-5}.
- Oct-31 vs Oct-5: Gap = 26 days.
- Oct-31 vs Nov-5: Gap = **5 days** (Selected).
- Oct-31 vs Dec-5: Gap = 35 days.

---

## 3. Carry Structure & Source Hierarchy (Rule R18)

Because paired contracts typically expire on different calendar dates, the natural contango or backwardation of the futures curve creates an apparent price wedge. AurumLens accounts for this carry friction:

### 3.1 Curve Carry Rate
If contract symbol $S$ has two active liquid expiries on date $t$ ($T_{\text{near}}$ and $T_{\text{far}}$):
$$r_{\text{curve}} = \frac{\ln(P_{\text{far}} / P_{\text{near}})}{(T_{\text{far}} - T_{\text{near}}) / 365}$$

### 3.2 Carry Source Hierarchy
1. Same-symbol curve rate $r_{\text{curve}}$ (Preferred, labeled `CURVE`).
2. If two active expiries are unavailable or illiquid, use the versioned config rate $r_{\text{fallback}}$ (e.g. 6.50% annualized, labeled `FALLBACK`).

### 3.3 Carry Adjustment Term
$$\text{carry\_adj} = r \times \frac{T_B - T_A}{365}$$
*Scale Check:* At $r = 6.00\%$ and a 5-day calendar gap, $\text{carry\_adj} = 0.06 \times (5/365) = +0.0008219$ (+8.22 bps).

---

## 4. Adjusted Log Spread & Rolling Deviation (Rule R18–R21)

### 4.1 Raw and Adjusted Log Spread
$$\text{Raw Spread: } s_{\text{raw}, t} = \ln(P_{A,\text{norm}, t}) - \ln(P_{B,\text{norm}, t})$$
$$\text{Adjusted Spread: } s_t = s_{\text{raw}, t} + \text{carry\_adj}$$

*Fixture Verification:* GOLDTEN at ₹120,500.00 vs normalized GOLDM at ₹120,482.41:
$$s_{\text{raw}} = \ln(120,500) - \ln(120,482.41) = \ln(1.00014600) \approx +0.00014597$$

### 4.2 Rolling Statistical Scoring (Strictly No Look-Ahead Bias)
The rolling distribution is computed over a lookback window of $L=60$ sessions strictly through $t-1$:
$$\mu_{t-1} = \frac{1}{N} \sum_{i=1}^{N} s_{t-i}, \quad \sigma_{t-1} = \sqrt{\frac{1}{N-1} \sum_{i=1}^{N} (s_{t-i} - \mu_{t-1})^2}$$
Requirement: $N \ge \text{min\_history\_obs}$ (default 30 sessions).

$$z_t = \frac{s_t - \mu_{t-1}}{\sigma_{t-1}}$$

### 4.3 Robust MAD Score Variant
To resist outlier price spikes, the Median Absolute Deviation (MAD) is computed:
$$\text{MAD}_{t-1} = \text{median}(|s_{t-i} - \text{median}(s_{t-1 \dots t-L})|)$$
$$\text{MAD Score: } z_{\text{mad}, t} = \frac{s_t - \text{median}_{t-1}}{1.4826 \times \text{MAD}_{t-1}}$$

### 4.4 Rich / Cheap Determination & Convergence Baseline
- If $s_t > \mu_{t-1}$: Leg A is rich, Leg B is cheap (Sell A, Buy B).
- If $s_t < \mu_{t-1}$: Leg A is cheap, Leg B is rich (Buy A, Sell B).
- **Rule R21 (Convergence to Mean):** Expected convergence is measured toward the rolling mean $\mu_{t-1}$, NEVER toward zero. A constant basis offset between contracts never alerts.

---

## 5. Integer Lot Sizing & Residual Gold Reconciliation (Rule R22)

Because contract trading units are discrete integers, hedging legs creates leftover fine gold:

$$\text{Fine Grams per Lot: } g_i = \text{trading\_unit\_g}_i \times \frac{\text{purity}_i}{0.999}$$

The engine searches all integer lot combinations $1 \le n_A, n_B \le \text{max\_lots}$ (default 50) minimizing unhedged fine gold:
$$\min_{n_A, n_B} |n_A g_A - n_B g_B|$$

Subject to minimum total turnover and notional caps.
$$\text{Residual Fine Grams: } \Delta g = n_A g_A - n_B g_B$$
The sign of $\Delta g$ indicates which leg carries unhedged directional gold exposure.

*Canonical Lot Ratio Fixture:* GOLDTEN (10g, 999) vs GOLDGUINEA (8g, 999):
$$g_A = 10.0\text{g}, \quad g_B = 8.0\text{g}$$
Optimal ratio: $n_A = 4, n_B = 5 \implies 4 \times 10.0\text{g} = 40.0\text{g}, \quad 5 \times 8.0\text{g} = 40.0\text{g}$
$$\text{Residual Fine Gold} = 0.0\text{g} \text{ (Exact Zero Delta)}$$

---

## 6. Execution Friction & Market Microstructure (Rule R9, R10)

An opportunity is only actionable if expected convergence exceeds round-trip execution drag:

### 6.1 Itemized Indian Statutory Friction Schedule
For turnover $V = \text{Lots} \times \text{Unit} \times P$:
| Cost Component | Applicable Leg & Side | Rate Formula |
|---|---|---|
| **Brokerage** | Both Legs, Both Sides | $\min(\text{flat\_fee}, \text{pct} \times V)$ (default ₹20 flat or 0.03%) |
| **Exchange Turnover** | Both Legs, Both Sides | $0.0021\% \times V$ |
| **SEBI Turnover Fee** | Both Legs, Both Sides | $0.0001\% \times V$ |
| **CTT** | **Sell Side Only** | $0.01\% \times V_{\text{sell}}$ |
| **Stamp Duty** | **Buy Side Only** | $0.002\% \times V_{\text{buy}}$ |
| **GST** | Both Legs, Both Sides | $18\% \times (\text{Brokerage} + \text{Exchange} + \text{SEBI})$ |

*Key Accounting Mandate:* GST applies exclusively to service fees (broker, exchange, SEBI). GST is NEVER charged on statutory taxes (CTT or Stamp Duty).

### 6.2 Corwin-Schultz (2012) High-Low Bid-Ask Spread Estimator
Using 2-day daily High ($H$) and Low ($L$) prices:
$$\beta = \left[ \ln\left( \frac{H_t}{L_t} \right) \right]^2 + \left[ \ln\left( \frac{H_{t-1}}{L_{t-1}} \right) \right]^2$$
$$\gamma = \left[ \ln\left( \frac{\max(H_t, H_{t-1})}{\min(L_t, L_{t-1})} \right) \right]^2$$
$$\alpha = \frac{\sqrt{2\beta} - \sqrt{\beta}}{3 - 2\sqrt{2}} - \sqrt{\frac{\gamma}{3 - 2\sqrt{2}}}$$
$$S = \frac{2(e^\alpha - 1)}{1 + e^\alpha}$$

Averaged over a 5-day rolling window through $t-1$. If $S \le 0$ or data is suspect, use contract fallback spread bps.

---

## 7. The 12-Gate Waterfall Evaluator (Rule R20)

Every gate is evaluated on every session. All 12 gates must pass for an **ALERT** decision.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   THE 12-GATE WATERFALL EVALUATION                     │
├────┬─────────────────────────┬───────────────────────────┬─────────────┤
│ #  │ Gate Name               │ Passing Condition         │ Reason Code │
├────┼─────────────────────────┼───────────────────────────┼─────────────┤
│ 1  │ `SPEC_OK`               │ Spec mode compliance      │ SPEC_UNVERIF│
│ 2  │ `DATA_QUALITY`          │ Prices not marked SUSPECT │ PRICE_SUSPEC│
│ 3  │ `EXPIRY_PAIR_VALID`     │ Calendar gap <= 35 days   │ NO_PAIR_GAP │
│ 4  │ `HISTORY_SUFFICIENT`    │ Valid observations >= 30  │ INSUFF_HIST │
│ 5  │ `Z_SCORE_THRESHOLD`     │ |Z| >= entry_z (2.0)      │ Z_BELOW_THR │
│ 6  │ `LIQUIDITY_VOLUME_A`    │ Leg A volume >= 10 lots   │ LIQ_VOL_A   │
│ 7  │ `LIQUIDITY_VOLUME_B`    │ Leg B volume >= 10 lots   │ LIQ_VOL_B   │
│ 8  │ `LIQUIDITY_OI_A`        │ Leg A OI >= 50 lots       │ LIQ_OI_A    │
│ 9  │ `LIQUIDITY_OI_B`        │ Leg B OI >= 50 lots       │ LIQ_OI_B    │
│ 10 │ `EXPIRY_SAFETY`         │ Days to tender > 5 days   │ EXP_UNSAFE  │
│ 11 │ `COST_HURDLE`           │ Gross Edge > Costs+Slip   │ COST_FAIL   │
│ 12 │ `DUPLICATE_CHECK`       │ No active duplicate trade │ DUPLICATE   │
└────┴─────────────────────────┴───────────────────────────┴─────────────┘
```

---

## 8. Nearest-Miss Service (FR17)

When a pair is `QUIET`, AurumLens calculates proximity metrics:
$$\text{Ratio}_i = \min\left(1.0, \frac{\text{Value}_i}{\text{Threshold}_i}\right)$$

Pairs are ranked lexicographically:
$$\text{Score} = (\text{Gates Passed} \downarrow, \quad \min_{\text{failing}} \text{Ratio} \downarrow)$$

---

## 9. Walk-Forward Backtesting & Attribution Methodology

1. **Expanding Window Folds:** In-sample training window expands chronologically, followed by out-of-sample test blocks.
2. **Next-Day Adverse Execution:** Trades generated on close of $t$ execute at open/settlement of $t+1$ with simulated adverse half-spread penalty:
   $$\text{Fill}_{\text{buy}} = P_{t+1} \times (1 + S/2), \quad \text{Fill}_{\text{sell}} = P_{t+1} \times (1 - S/2)$$
3. **P&L Attribution Formula:**
   $$\text{Gross P\&L} = \text{Spread Reversion Return} \times \text{Notional}$$
   $$\text{Net P\&L} = \text{Gross P\&L} - \text{Itemized Taxes} - \text{Slippage Drag} + \text{Residual Gold Delta P\&L}$$
4. **Deflated Sharpe Ratio (DSR):**
   Adjusts observed Sharpe ratio for skewness, kurtosis, and the total number of trial parameter combinations tested ($N_{\text{trials}}$):
   $$\text{DSR} = \Phi\left( \frac{(\widehat{SR} - SR^*) \sqrt{T-1}}{\sqrt{1 - \gamma_3 \widehat{SR} + \frac{\gamma_4 - 1}{4} \widehat{SR}^2}} \right)$$
