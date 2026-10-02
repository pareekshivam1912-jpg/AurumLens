# AurumLens Docs — CHANGELOG

## v2.1 — 2026-10-01 (build stack for Google Antigravity)
- **Decision (user):** build in Google Antigravity with **Stitch MCP** (UI design) and **Supabase MCP** (database).
- **Storage:**
  - Supabase Postgres becomes the system of record, replacing DuckDB.
  - Supabase Storage holds raw Bhavcopy files (bucket `bhavcopy-raw`).
  - Parquet stays for dataset versioning and the offline demo.
- **UI:** screens are designed in Stitch and built in Next.js (TypeScript, Tailwind), replacing Streamlit.
- **API:**
  - Reads come from Supabase through RLS, which allows SELECT only.
  - A thin FastAPI service handles hedge tools, the explainer and admin actions.
  - The Python engine is the only writer, using the service-role key.
- **Unchanged:** all analytical rules R1–R25, FR1–FR32, gates, tests and exit gates. Formulas still live only in the Python engine, never in SQL views or the UI.
- **New document:** `ANTIGRAVITY_BUILD_PLAN.md` (phases A0–A10, MCP config, initial migrations, Stitch prompts).
- **Safety:**
  - The Supabase MCP is read-only by default and scoped to one dev project.
  - A separate write server is enabled only while migrations are applied.

## v2.0 — 2026-10-01 (MVP revision)

**Inputs:**
- v1 docs (PRD, Design, Phase, System_architecture, phase_wiseprompt, .cursorrules);
- a Gemini research report (https://share.gemini.google/gt6qFoJbQB2K);
- a quick check of public sources.

### Corrections
| # | Issue | v2 resolution |
|---|---|---|
| C1 | The research report's purity formula is written inverted, giving ×0.996 for GOLDM, while it quotes the correct factor 1.00402 | R16: `× (0.999 / purity)`; lower purity normalizes up; a direction test is mandatory |
| C2 | The research example paired GOLDM Oct-5 with GOLDTEN Oct-31 (26-day gap) | R17: smallest gap, so Nov-5 (5 days) |
| C3 | The research example's carry (0.000451 for 26 days) implies ~0.6% a year, which contradicts its own ~6% assumption | Worked carry values in Design §6.5 |
| C4 | GOLDGUINEA purity conflicts between sources (995 base + 999/995 premium vs 999) | Marked `DISPUTED` (F9); `spec_mode` strict/research (R24) |
| C5 | v1 left the normalization target ambiguous ("fine gold") | Fixed as ₹ per 10 g of **999** |

### Decisions (where the research conflicted with v1)
| Topic | Decision | Reason |
|---|---|---|
| Storage / UI | Keep DuckDB + Parquet + Streamlit (not Postgres + React) | Offline demo, speed of build |
| Validation | Walk-forward stays primary; Deflated Sharpe Ratio added as a reported metric; CPCV future-only | Short GOLDTEN history (~18 months) |
| Carry | Same-symbol curve first, repo-style fallback second, `carry_source` recorded | Carry error can exceed the anomaly |
| ADF / cointegration | Diagnostic only, never a gate | Noisy on short windows; look-ahead risk |
| Spread form | Log spread | Symmetric and scale-free |
| Gate evaluation | All gates evaluated every time | Complete evidence and the waterfall UI |

### New rules
R16–R25:
- normalization basis and direction;
- smallest-gap pairing;
- carry hierarchy;
- price source and freshness;
- all-gate evaluation;
- convergence to the rolling mean;
- lot ratio and residual exposure;
- statistical tests as diagnostics only;
- spec strictness mode;
- explanations never compute numbers.

### New features (PRD §13)
- **MVP+:**
  - FR16 gate waterfall;
  - FR17 nearest miss;
  - FR18 data-quality flags;
  - FR19 cost breakdown;
  - FR20 spec trust panel;
  - FR21 baselines;
  - FR22 converter;
  - FR23 cheapest-to-hedge;
  - FR24 lot sizer;
  - FR25 event markers;
  - FR26 English/Hindi explanations;
  - FR27 evidence export.
- **Stretch:**
  - FR28 replay player;
  - FR29 sensitivity heatmap;
  - FR30 daily digest;
  - FR31 paper journal;
  - FR32 spot premium.

### New artifacts
- Facts register (PRD §5, F1–F16).
- `events.yaml`.
- Trial registry.
- Source adapters for before and after the October 2023 format change.
- Nine-screen UI plan.
- Worked hand fixtures (Design §6).
- Expanded test plan.

### Still open
F9 GUINEA purity, F14 settlement field, F15 coin premium, F13 schema details, F7 circular MCX/TRD/456/2025, F16 default brokerage profile. All of these are Phase 0 tasks.
