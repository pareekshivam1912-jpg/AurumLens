# AurumLens — Facts & Verification Checklist (F1–F16)

> **Document Status:** Active Tracking Register  
> **Rule Enforcement:**  
> - `spec_mode: strict` -> Any spec that is not `VERIFIED_OFFICIAL` halts signal generation (`SPEC_UNVERIFIED`).  
> - `spec_mode: research` -> Analytics calculate with an explicit "Unverified Specs" watermark.  
> - `DISPUTED` facts must never be arbitrarily resolved without primary regulatory documentation.

---

## Facts Register Summary Table

| ID | Fact / Parameter | Current Value | Status | Source / Reference | Verification Plan & Notes |
|:---|:---|:---|:---:|:---|:---|
| **F1** | GOLDM trading unit & quote basis | 100 g / ₹ per 10 g | **SECONDARY** | [MCX Gold Mini Specification](https://www.mcxindia.com/products/bullion/gold-mini) | Confirm with official MCX contract specification PDF. |
| **F2** | GOLDM expiry rule | 5th calendar day of contract month | **SECONDARY** | [MCX Gold Mini Specification](https://www.mcxindia.com/products/bullion/gold-mini) | Verify holiday preponement rule (if 5th is holiday, preceding trading day). |
| **F3** | GOLDTEN trading unit & quote basis | 10 g / ₹ per 10 g | **SECONDARY** | MCX Circular on Launch of GOLDTEN Futures | Verify against exchange circular and first trade records. |
| **F4** | GOLDTEN launch date | April 2025 | **SECONDARY** | MCX Product Launch Circulars | Identify exact trade date of first Bhavcopy appearance. |
| **F5** | GOLDGUINEA trading unit & quote basis | 8 g / ₹ per 8 g | **SECONDARY** | [MCX Gold Guinea Specification](https://www.mcxindia.com/products/bullion/gold-guinea) | Verify standard 1 sovereign (8g) contract specification. |
| **F6** | GOLDPETAL trading unit & quote basis | 1 g / ₹ per 1 g | **SECONDARY** | [MCX Gold Petal Specification](https://www.mcxindia.com/products/bullion/gold-petal) | Verify 1g quote basis and micro-contract delivery details. |
| **F7** | GUINEA / PETAL / TEN expiry rule | Last calendar day of contract month | **SECONDARY** | Circular MCX/TRD/456/2025 | Retrieve circular MCX/TRD/456/2025 regarding launch calendar modifications. |
| **F8** | Purity: GOLDM | 0.995 (995 fineness) | **SECONDARY** | MCX Gold Mini Delivery Specifications | Confirm physical delivery purity standard (995). |
| **F9** | Purity: GOLDGUINEA | `null` (candidates: 0.995, 0.999) | **DISPUTED** | Conflicting broker tables vs mint coin specs | **CRITICAL DISPUTE:** Normalization differs by ~0.402%. Kept `null` in strict mode; requires physical contract circular. |
| **F10** | Purity: GOLDTEN, GOLDPETAL | 0.999 (999 fineness) | **SECONDARY** | MCX Contract Specifications | Confirm whether London Good Delivery / BIS 999 applies. |
| **F11** | Delivery premium (999 against 995 contract) | Rate × (0.999 / 0.995) | **SECONDARY** | MCX Delivery & Settlement By-laws | Confirm settlement premium formula for higher purity delivery. |
| **F12** | Staggered delivery / tender period | Last 3 trading days (was 5 prior to Jan 2025) | **SECONDARY** | SEBI Commodity Derivatives Staggered Delivery Circular | Retrieve SEBI notification and MCX enforcement circular. |
| **F13** | Bhavcopy schema migration date & structure | October 16, 2023 (TCS CDP migration) | **SECONDARY** | MCX CDP Migration Circulars & Sample Files | Confirm schema difference: legacy CSV structure vs CDP pipe/comma delimited layout. |
| **F14** | Settlement price field in Bhavcopy | Unknown / Era-dependent | **TO_VERIFY** | Bhavcopy sample files (both eras) | Determine if official Bhavcopy provides daily settlement price or close only. |
| **F15** | Coin making-charge premium in GUINEA/PETAL | Structural / Absorbed in rolling mean | **TO_VERIFY** | Historical basis studies | Invariant R21 ensures stable structural coin fabrication markup is absorbed by $\mu_{t-1}$. |
| **F16** | Transaction cost schedule & default broker | Brokerage, CTT, Exchange, SEBI, Stamp, GST | **SECONDARY** | Finance Act, MCX Tariffs, Discount Broker schedules | Sourced standard candidate schedule in `costs.yaml`; broker-specific brokerage mode (`min_flat_pct`). |

---

## Status Breakdown

- **VERIFIED_OFFICIAL:** 0 (Primary circulars pending official document archiving)
- **SECONDARY:** 12 (Sourced from broker circulars, exchange web specifications, and research reports)
- **DISPUTED:** 1 (F9: GOLDGUINEA purity basis between 995 and 999)
- **TO_VERIFY / TO_VALIDATE:** 3 (F14 settlement price presence, F15 coin premium empirical distribution, F16 safety buffer parameter)

---

## Resolution Directives

1. **GOLDGUINEA Purity (F9):**
   - Retrieve MCX contract specification circular for Gold Guinea from the MCX Circular Archives.
   - If contract delivers 8g coin of 999 purity with 995 underlying base rate, check whether quotation reflects 995 or 999.
   - Until verified, remain `DISPUTED`.

2. **Bhavcopy Formats (F13, F14):**
   - Ingest real raw sample files from pre-Oct 2023 (e.g. September 2023) and post-Oct 2023 (e.g. November 2023 / 2024 / 2025).
   - Document canonical mapping in `engine/src/aurumlens/ingest/adapters/`.
