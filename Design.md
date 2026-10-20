# AurumLens — Product & UX Design Specification v3.0

> **Version:** 3.0 · **Date:** 2026-10-20 · **Status:** Master Design Document  
> **Supersedes:** Design v2.0 · **Aligned with:** `prompt.md` Section 2, 7 & 8

---

## 1. Design Principles & Institutional Philosophy

1. **Information Density with Absolute Clarity:** High-signal fintech layout modeled after institutional terminals (Bloomberg, Refinitiv) without clutter.
2. **Transparent Derivations:** Every metric, price, and indicator displays its inputs, assumptions, and units. If an input is unavailable, it renders as `Unavailable` rather than fabricating zero.
3. **Color with Semantic Meaning:**
   - **Alert / Divergence:** Crimson/Amber (`#C62828` / `#D97706`)
   - **Quiet / Compliant / In-Bounds:** Emerald (`#2E7D32`)
   - **Institutional Primary / Gold:** Warm Ochre/Gold (`#B7862C`)
   - **Neutral Backgrounds & Borders:** Off-white/slate paneling (`#F9FAFB` / `#E5E7EB`)
4. **Zero Reliance on Color Alone:** Accessible icon pairing (`CheckCircle2`, `XCircle`, `AlertTriangle`) alongside text badges for color-blind accessibility (WCAG AA).
5. **Unified Conversation Layer:** One persistent chatbot dock with deep awareness of the active dashboard state.

---

## 2. Institutional Design System Tokens

### 2.1 Color Palette
```css
:root {
  /* Brand Primary */
  --color-gold-primary: #B7862C;
  --color-gold-hover:   #9A6F22;
  --color-gold-tint:    #FDF8EC;
  --color-gold-border:  #E8D4A2;

  /* State Tints */
  --color-quiet:        #2E7D32;
  --color-quiet-bg:     #E8F5E9;
  --color-quiet-border: #C8E6C9;

  --color-alert:        #C62828;
  --color-alert-bg:     #FFEBEE;
  --color-alert-border: #FFCDD2;

  --color-warning:      #D97706;
  --color-warning-bg:   #FEF3C7;
  --color-warning-border:#FDE68A;

  /* Neutrals */
  --color-ink:          #111827;
  --color-slate-dark:   #374151;
  --color-slate-medium: #4B5563;
  --color-slate-light:  #9CA3AF;
  --color-panel-bg:     #F9FAFB;
  --color-card-bg:      #FFFFFF;
  --color-border-subtle:#E5E7EB;
}
```

### 2.2 Typography & Numerical Formatting
- **Font Family:** `Inter`, system sans-serif.
- **Tabular Figures:** All prices, timestamps, lot numbers, and statistical scores must use `font-variant-numeric: tabular-nums` (Tailwind: `font-mono` / `tabular-nums`) to prevent alignment jitter during real-time updates.
- **Currency & Units:** Standard Indian grouping (`₹1,20,482.41`), always explicit (`₹`, `g`, `lots`, `bps`).

---

## 3. Core Dashboard Layout & Workspace Grid

The unified dashboard arranges the 4 core sections requested by `prompt.md` into an ergonomic, responsive layout:

```
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│ TOP NAVIGATION & BRAND BAR                                                                 │
│ AurumLens [Logo] | MCX Gold Terminal | Status: LIVE-DEMO | Search / Command | User Profile │
├────────────────────────────────────────────────────────────────────────────────────────────┤
│ SECTION A: MARKET OVERVIEW STRIP                                                           │
│ [State: QUIET ●] [Update: 15:45:00 IST] [GOLDM: ₹120,000] [GOLDTEN: ₹120,500] ...        │
├─────────────────────────────────────────────────────────────┬──────────────────────────────┤
│ SECTION B: INTERACTIVE CHART SUITE                          │ SECTION C: SIGNAL MONITOR    │
│ ┌─────────────────────────────────────────────────────────┐ │ ┌──────────────────────────┐ │
│ │ Controls: [1D|1W|1M|1Y] [Candles] [Raw|Norm] [Pair Sel]│ │ │ Pair: GOLDTEN-GOLDM      │ │
│ ├─────────────────────────────────────────────────────────┤ │ │ Status: QUIET (11/12)   │ │
│ │ Candlestick Chart / Volume                              │ │ │ Z-Score: +1.67 (H: 2.00) │ │
│ ├─────────────────────────────────────────────────────────┤ │ ├──────────────────────────┤ │
│ │ Carry-Adjusted Spread Chart (s_t with ±2σ bands)       │ │ │ 12-Gate Waterfall Table  │ │
│ ├─────────────────────────────────────────────────────────┤ │ │ [Gate] [Val] [Thresh][Res│ │
│ │ Statistical Deviation Panel (Z-Score & Entry Threshold) │ │ │ Near-Miss Ratio: 83.5%   │ │
│ └─────────────────────────────────────────────────────────┘ │ └──────────────────────────┘ │
├─────────────────────────────────────────────────────────────┴──────────────────────────────┤
│ SECTION D: PORTFOLIO SNAPSHOT & RISK RUNNER                                                │
│ ┌─────────────────────────┬──────────────────────────┬───────────────────────────────────┐ │
│ │ Cash & Equity Balance   │ Open Paper Positions     │ What-If Scenario Stress Tester    │ │
│ │ Cash: ₹10,00,000        │ 1. Short GOLDTEN 4 lots  │ Shock: [ -2% Gold Drop          ] │ │
│ │ MTM P&L: +₹4,820        │ 2. Long GOLDGUINEA 5 lots│ Projected Net Impact: -₹1,240     │ │
│ │ Exposure: ₹48,20,000    │ Unrealized: +₹2,100      │ Delta Risk: 0.0g fine gold        │ │
│ └─────────────────────────┴──────────────────────────┴───────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────────────┘
│ FLOATING DOCK: UNIFIED AURUM LENS AI CHATBOT (Expandable Drawer / Slide-Over)             │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Section Deep-Dives & Interaction Design

### 4.1 Section A: Market Overview Strip
- **Status Indicator:** High-visibility pill:
  - `QUIET` with steady green pulse: No anomalies exceeding all 12 gates.
  - `ALERT` with pulsing amber/crimson ping: Verified structural opportunity open.
- **Contract Ticker Cards (4 items):**
  - Contract Symbol & Expiry Date (e.g. `GOLDM (05-Nov-2026)`).
  - Quoted Price & Daily % Change.
  - Delivery Basis (`100g / 995`).
  - Data Freshness Tag (`Realtime`, `15m Delayed`, `EOD Snapshot`).
- **Data Quality Alerts:** If an exchange feed is delayed or suspect, a banner appears with an orange warning: `[!] Warning: Bhavcopy settlement data delayed. Using close prices with SUSPECT filter enabled.`

### 4.2 Section B: Interactive Chart Component
The charting suite accepts application-supplied datasets and features:
1. **Primary Candlestick & Volume Window:**
   - Visualizes OHLC bars with volume histogram.
   - Dual-Mode Toggle:
     - `Raw Exchange Price`: Plots raw prices as quoted on MCX.
     - `Normalized Analytical Price`: Standardizes prices to ₹/10g 999 equivalent.
   - Signal Overlays: Entry triangles, stop-loss reference dashes, target mean lines.
2. **Relative-Value Spread Window:**
   - Displays the carry-adjusted log basis: $s_t = \ln(P_A) - \ln(P_B) + r \cdot (\Delta T/365)$.
   - Centerline: 60-day rolling mean $\mu_{t-1}$.
   - Outer Bands: Rolling $\pm 2\sigma_{t-1}$ volatility envelopes.
3. **Z-Score Deviation Window:**
   - Plots normalized deviation $z_t$.
   - Horizontal threshold lines at $+2.0$ (Short Spread) and $-2.0$ (Long Spread).
   - Zero-reversion benchmark line.
4. **State Machine States:**
   - `Loading Skeleton`: Shimmering gradient matching chart dimensions.
   - `Empty State`: "No historical data available for selected contract in this date range."
   - `Stale Warning`: Translucent overlay indicating feed lag.

### 4.3 Section C: Signal Monitor & Waterfall Drawer
- **Pair Selection Tabs:** Fast switching between all 6 pairs:
  - `GOLDTEN - GOLDM` (Gap: 5 days)
  - `GOLDTEN - GOLDGUINEA` (Gap: 0 days)
  - `GOLDM - GOLDGUINEA` (Gap: 5 days)
  - `GOLDM - GOLDPETAL` (Gap: 5 days)
  - `GOLDTEN - GOLDPETAL` (Gap: 0 days)
  - `GOLDGUINEA - GOLDPETAL` (Gap: 0 days)
- **12-Gate Waterfall Table:**
  - Displays each gate in sequence:
    1. Spec Verification (`SPEC_OK`)
    2. Data Quality & Non-Suspect (`DATA_QUALITY`)
    3. Expiry Calendar Gap ($\le 35\text{d}$) (`EXPIRY_PAIR_VALID`)
    4. Historical Window ($\ge 30\text{ obs}$) (`HISTORY_SUFFICIENT`)
    5. Z-Score Hurdle ($|z| \ge 2.0$) (`Z_SCORE_THRESHOLD`)
    6. Leg A Volume Liquidity (`LIQUIDITY_VOLUME_A`)
    7. Leg B Volume Liquidity (`LIQUIDITY_VOLUME_B`)
    8. Leg A Open Interest (`LIQUIDITY_OI_A`)
    9. Leg B Open Interest (`LIQUIDITY_OI_B`)
    10. Physical Tender Window Safety ($> 5\text{d}$) (`EXPIRY_SAFETY`)
    11. Economic Friction Hurdle ($\text{Edge} > \text{Costs} + \text{Slippage}$) (`COST_HURDLE`)
    12. Duplicate Suppression (`DUPLICATE_CHECK`)
  - Columns: Gate Name, Status Badge (`PASS` / `FAIL`), Actual Value, Required Threshold, Safety Margin, Audit Reason Code.
- **Nearest-Miss Proximity Card:** Displays why an opportunity was rejected, the percentage margin to passing, and how many gates held it back.

### 4.4 Section D: Portfolio Snapshot & Risk Stress Tester
- **Portfolio Summary Pod:**
  - Simulated Cash Balance, Margin Utilization, Unrealized MTM, Realized P&L.
- **Active Paper Positions Table:**
  - Pair, Entry Date, Leg A Contract/Lots, Leg B Contract/Lots, Net Residual Gold Grams, MTM P&L, Action Buttons (`Inspect In Chart`, `Close Position`).
- **Interactive Scenario Stress Tester:**
  - Sliders & Presets:
    - Gold Price Shock: `[-5%, -2%, -1%, +1%, +2%, +5%]`
    - Carry Rate Shock: `[-100bps, 0, +100bps]`
  - Real-Time Simulation Output:
    - Projected Net P&L impact on active paper portfolio.
    - Highlight of unhedged residual fine gold exposure.

---

## 5. Unified AurumLens AI Chatbot UX Specification

### 5.1 Chatbot Surface & Placement
- **Dockable Drawer:** Positioned in the bottom-right corner as a persistent floating assistant badge (`AurumLens AI`).
- **Expandable Modes:**
  - *Compact Slide-Over:* 420px sidebar dock that sits alongside dashboard components.
  - *Full Inspector Drawer:* 720px expanded overlay for detailed evidence audits or multi-step risk simulations.

### 5.2 Context Awareness & State Injection
The chatbot automatically receives the current UI state without the user needing to type it:
- `active_pair`: e.g. "GOLDTEN_GOLDGUINEA"
- `active_timeframe`: e.g. "1M"
- `active_date`: e.g. "2026-10-01"
- `user_portfolio_id`: authenticated user's active simulated account

### 5.3 Message Layout & Grounding Citations
1. **User Message:** Clean slate bubble right-aligned.
2. **AI Response:** Left-aligned card containing:
   - **Data Status Pill:** `[Historical: 2026-10-01 15:45 IST • Verified Tool Output]`
   - **Formatted Explanation:** Rendered markdown with clean tabular figures.
   - **Evidence Tag:** Tool citation pill showing exact deterministic tool used (e.g. `via get_signal_evidence`).
   - **Follow-up Prompt Pills:** 2–3 suggested next queries (e.g. *"What happens if carry increases?"*, *"Compare with GOLDM"*).

### 5.4 Interactive Two-Step Order Confirmation Card
If the user instructs: *"Simulate buying 4 lots of GOLDTEN and selling 5 lots of GOLDGUINEA"*:
- The bot replies with a formatted **Staged Paper Order Card**:
  ```text
  ┌────────────────────────────────────────────────────────┐
  │ 📋 PROPOSED SIMULATED PAPER ORDER                      │
  │ • Leg A: BUY 4 Lots GOLDTEN (31-Oct-2026) @ ₹1,20,500   │
  │ • Leg B: SELL 5 Lots GOLDGUINEA (31-Oct-2026) @ ₹96,400 │
  │ • Residual Gold Exposure: 0.0g (Exact Zero Delta)      │
  │ • Est. Round-Trip Costs: ₹138.42                       │
  │ • Est. Margin Required: ₹48,200.00                     │
  │                                                        │
  │ [ Cancel ]                   [ ✔ Confirm Paper Trade ] │
  └────────────────────────────────────────────────────────┘
  ```
- **The trade is NOT executed until the user clicks `Confirm Paper Trade`**.

---

## 6. Responsive & Accessibility Specifications

### 6.1 Breakpoint Behaviors
- **Desktop ($\ge 1280\text{px}$):** Full multi-pane dashboard (Overview top, Chart and Signal Monitor side-by-side, Portfolio bottom, Chat slide-over).
- **Tablet ($768\text{px} - 1279\text{px}$):** Stacked view with tabbed switcher between Chart Suite and Signal Waterfall.
- **Mobile ($< 768\text{px}$):** Single-column stacked stream with collapsible drawer sections and full-screen modal chat.

### 6.2 Accessibility Standards (WCAG 2.1 AA)
- Contrast ratio $\ge 4.5:1$ on all body text and data labels.
- Keyboard navigation: Full focus trapping for modals and drawer widgets; skip navigation links.
- Screen readers: ARIA live regions for realtime alert toasts and chat responses.
