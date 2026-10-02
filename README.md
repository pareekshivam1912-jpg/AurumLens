# AurumLens

**MCX Gold Cross-Contract Relative-Value Intelligence & Hedging-Cost Analytics**

AurumLens compares MCX gold futures contracts (`GOLDM`, `GOLDTEN`, `GOLDGUINEA`, `GOLDPETAL`) on a normalized fine-gold price basis (₹ per 10 g of 999 fine gold), adjusting for contract specifications, expiry differences, and implied carry. It evaluates cross-contract pricing through a strict 11-gate waterfall to produce actionable `ALERT` or transparent `QUIET` decisions with nearest-miss telemetry.

> **Disclaimer:** Analytics only — not investment advice.

---

## Repository Structure

```text
aurumlens/
├── AGENTS.md                  # Operational rules for AI agents and Cursor
├── docs/                      # PRD, Design, Phase, Architecture, Antigravity Plan
├── config/                    # contracts.yaml, costs.yaml, strategy.yaml, events.yaml
├── engine/                    # Python analytics engine (pure functions, no I/O mixed)
│   ├── src/aurumlens/
│   │   ├── config/            # Pydantic schemas, version hash loader
│   │   ├── ingest/            # Downloader, format adapters (legacy, CDP), quality checks
│   │   ├── core/              # Normalization, pairing, carry, spreads, sizing, costs
│   │   ├── signals/           # Scoring, all-gate evaluator, nearest miss, evidence builder
│   │   ├── backtest/          # Walk-forward engine, trial registry, baselines, DSR
│   │   ├── tools/             # Converter, cheapest-to-hedge, lot-ratio sizer
│   │   └── explain/           # Bilingual templates (EN/HI) and numeric guard
│   └── tests/                 # Unit and regression test suite
├── api/                       # Thin FastAPI service for tools, explainer, admin
├── web/                       # Next.js frontend built from Stitch designs
├── supabase/                  # Database migrations, seed data, configuration
└── data/                      # Raw cache, processed Parquet snapshots, fixtures
```

---

## Setup & Testing

```bash
# Install package and test dependencies
pip install -e ".[dev]"

# Run tests
pytest
```
