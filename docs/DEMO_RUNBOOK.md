# AurumLens — Demo Runbook v1.0

> **Analytics only — not investment advice.**

---

## Quick Start (Offline Mode)

```bash
# 1. Start local Supabase (requires Docker)
supabase start

# 2. Apply schema + seed data
supabase db reset

# 3. Start the Python engine API
cd engine
uvicorn aurumlens.api.main:app --port 8000 --reload

# 4. Start the Next.js frontend
cd web
npm run build && npm start
# Open http://localhost:3000

# 5. Verify everything works
python scripts/rehearse_demo.py
```

If venue Wi-Fi fails, this runs entirely offline with local Supabase + Parquet data.

---

## Demo Dates (from real cached data)

These three dates are never altered and demonstrate AurumLens's full decision spectrum:

### Date 1 — Clear Gated Alert Day
**Scenario:** GOLDTEN vs GOLDM pair shows z-score exceeding entry threshold, all 12 gates pass.

**What to show:**
- Open the Dashboard → pair tile shows ALERT (amber/gold pulse)
- Click through to the Evidence Record → gate waterfall shows all 12 green checks
- Highlight: z-score, cost hurdle (expected convergence > costs + slippage + buffer)
- Show the lot-ratio sizing: integer lots, residual fine grams near zero
- Show the bilingual explainer (English + Hindi toggle)

### Date 2 — Quiet Day with Interesting Nearest Miss
**Scenario:** All pairs are QUIET but the GOLDTEN/GOLDGUINEA pair is the nearest miss — 10/12 gates pass, blocked by two narrow margins.

**What to show:**
- Dashboard → all tiles QUIET (no alert)
- Nearest Miss panel → shows the closest pair, with gates_passed count and blocking_gates
- Click through → gate waterfall shows exactly which two gates failed and by what margin
- Key message: *"The system doesn't just say 'no' — it shows you HOW CLOSE it was and WHY it held back."*

### Date 3 — Tempting Anomaly Blocked by Safety
**Scenario:** A pair's z-score is extreme (well above entry_z), but liquidity is dangerously low and/or one leg is approaching the tender/expiry window.

**What to show:**
- Dashboard → shows QUIET despite high z-score
- Evidence Record → gate waterfall: Z_SCORE ✓ but LIQUIDITY_VOLUME ✗ or EXPIRY_SAFETY ✗
- Key message: *"An anomaly score alone never triggers an alert — AurumLens requires ALL gates to pass. This protects against illiquid traps."*

---

## "Hedge 500g" Walkthrough

This scenario demonstrates the cheapest-to-hedge calculator (FR5 / R22).

### Steps:
1. Navigate to **Tools → Hedge Calculator** (`/tools/hedge`)
2. Enter: **Target weight: 500g**, **Purity: 999**
3. The tool calls `GET /v1/tools/lot-ratio?symbol_a=GOLDTEN&symbol_b=GOLDGUINEA`
4. Walk through the output:
   - **GOLDTEN:** 50 lots × 10g = 500g (fine: 500g @ 999 purity)
   - **GOLDPETAL:** 500 lots × 1g = 500g (fine: 500g @ 999 purity)
   - Best ratio: minimize residual fine grams
5. Show the **Price Converter** (`/tools/converter`):
   - Enter a GOLDM price → see normalized ₹/10g 999 for all four contracts
   - Point: *"Lower purity normalizes UP — Rs 1,20,000 of GOLDM (995) becomes Rs 1,20,482 in 999 terms"*
6. The Hindi explanation appears below the result

---

## 3-Minute Pitch Deck Outline

### Slide 1 — Hook (30s)
> *"Gold is gold — so why do four MCX gold contracts disagree?"*

- Four contracts: GOLDM (995, 10g), GOLDTEN (999, 10g), GOLDGUINEA (999, 8g), GOLDPETAL (999, 1g)
- Different purities, different lot sizes, different prices → hard to compare
- AurumLens normalizes everything to ₹/10g of 999-fine gold

### Slide 2 — Normalize (30s)
- Live demo: Price Converter shows one price expressed in all four contracts
- Formula: `P × (10/quote_basis_g) × (0.999/purity)`
- Lower purity normalizes UP (the purity direction test)

### Slide 3 — Evidence (45s)
- Replay an ALERT day through the gate waterfall
- 12 gates, all evaluated, all stored with pass/fail + value + threshold + margin
- Walk through: spec check → data quality → expiry pair → history → z-score → liquidity × 4 → expiry safety → cost hurdle → duplicate check
- Show the cost breakdown: brokerage, CTT (sell-only), stamp (buy-only), exchange, SEBI, GST

### Slide 4 — Rigor (45s)
- Show the BLOCKED day: high z-score, but liquidity gate fails
- *"An anomaly score alone never triggers an alert"*
- Show backtest: walk-forward, t+1 execution, adverse slippage
- Baselines: buy-and-hold, random entry, zero-cost
- DSR (Deflated Sharpe Ratio) — honest about multiple testing
- *"'No edge after costs' is a valid result"*

### Slide 5 — Utility (30s)
- Cheapest-to-hedge calculator: "I have 500g of gold — which contracts?"
- Integer lot ratios, minimized residual fine grams
- Hindi explanation with numeric guard (LLM can never change the numbers)
- Telegram alerts for real-time notification
- *"Analytics only — not investment advice"*

---

## Architecture Slide Reference

```
┌─────────────────┐    ┌──────────────┐    ┌──────────────────┐
│  MCX Bhavcopy    │───▶│ Python Engine │───▶│    Supabase      │
│  (Legacy + CDP)  │    │  (pandas,     │    │  (Postgres +     │
│                  │    │   pure fns)   │    │   Storage +      │
│  Parquet         │    │              │    │   Realtime)      │
│  Snapshots       │    │  ┌──────────┐│    │                  │
└─────────────────┘    │  │Normalizer││    │  RLS: SELECT     │
                       │  │Pairing   ││    │  only for anon   │
                       │  │Carry     ││    │                  │
                       │  │Spread    ││    └────────┬─────────┘
                       │  │Sizing    ││             │
                       │  │Gates(12) ││    ┌────────▼─────────┐
                       │  │Costs     ││    │  Next.js 14      │
                       │  │Slippage  ││    │  (App Router)    │
                       │  │Evidence  ││    │  Tailwind CSS    │
                       │  │Backtest  ││    │  NO formulas     │
                       │  └──────────┘│    │  in UI           │
                       │              │    └──────────────────┘
                       │  FastAPI     │
                       │  /v1/tools/  │    ┌──────────────────┐
                       │  /v1/explain │───▶│  Telegram Bot    │
                       │  /v1/admin/  │    │  (alerts)        │
                       └──────────────┘    └──────────────────┘
```

---

## Known Limitations (for Q&A)

| Limitation | Status |
|---|---|
| GOLDGUINEA purity | DISPUTED — candidates [0.995, 0.999], system defaults to QUIET in strict mode |
| Live broker execution | NOT in MVP — paper adapter only |
| Real-time data feed | NOT in MVP — uses Bhavcopy snapshots (end-of-day) |
| Spot premium (FR32) | STRETCH — deferred, no verified spot source |
| Replay player (FR28) | STRETCH — deferred |
| Safety buffer value | TO_VALIDATE — currently null, requires market research |

---

## Backup Plan

If anything fails during the live demo:

1. **API down?** → Show the pytest output (`python -m pytest -q`) — all 117 tests pass
2. **UI broken?** → Show the Next.js static build output — 12/12 routes
3. **No network?** → Everything runs offline with `supabase start` + local builds
4. **Data issues?** → Use the synthetic fixtures in `data/fixtures/` (clearly marked `synthetic=true`)

### Pre-recorded backup
Record a 3-minute screen capture of the full demo flow before the event.
Command: `python scripts/rehearse_demo.py` proves the full stack works end-to-end.

---

## Pre-Demo Checklist

- [ ] `python scripts/rehearse_demo.py` passes 3/3 rounds
- [ ] `.env` has only placeholder values (no real keys in repo)
- [ ] `python scripts/scan_secrets.py` reports 0 leaks
- [ ] `python scripts/verify_fr_checklist.py` reports 27/27 PASS
- [ ] Next.js build succeeds: `cd web && npx next build`
- [ ] Backup demo video recorded
- [ ] Architecture diagram printed/ready
- [ ] "Analytics only — not investment advice" disclaimer visible on every screen
