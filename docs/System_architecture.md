# AurumLens — System Architecture v2.0

> **Version:** 2.0 · **Date:** 2026-10-01 · **Supersedes:** v1
>
> **What v2 adds:**
> - source-format adapters for before and after the October 2023 migration;
> - a price-quality stage;
> - a carry source hierarchy;
> - a sizing engine;
> - a gate evaluator that runs every gate;
> - a nearest-miss service;
> - hedge tools;
> - a deterministic explainer;
> - an events config;
> - a trial registry.
>
> **Storage stays DuckDB + Parquet.**

## 1. High-Level Architecture

```mermaid
flowchart LR
    MCX[MCX Bhavcopy Archives] --> ADP{Format Adapter}
    ADP -->|pre Oct-2023| A1[Legacy Adapter]
    ADP -->|post Oct-2023 CDP| A2[CDP Adapter]
    A1 --> ING[Ingestion Service]
    A2 --> ING
    SPEC[Contract Config + Facts Register] --> ING
    ING --> RAW[(Raw Snapshots + file hash)]
    RAW --> VAL[Validation: date, schema, dedupe]
    VAL --> DQ[Price Quality: source + stale flags]
    DQ --> DB[(DuckDB)]
    DB --> NORM[Normalization: 10g of 999]
    NORM --> PAIR[Smallest-gap Expiry Matching]
    PAIR --> CARRY[Carry: curve, else fallback]
    CARRY --> SPREAD[Log Spread]
    SPREAD --> SCORE[Z-score / MAD, history through t-1]
    SCORE --> SIZE[Lot-ratio Sizer]
    SIZE --> COST[Costs + Slippage]
    COST --> GATE[Gate Evaluator: all gates]
    GATE --> SIG[(Evidence Records: QUIET/ALERT)]
    GATE --> NM[Nearest-miss Service]
    SIG --> BT[Walk-forward Backtester + Baselines]
    BT --> TR[(Trial Registry)]
    BT --> DB
    SIG --> EXP[Explainer EN/HI: templates]
    SIG --> API[FastAPI]
    NM --> API
    EXP --> API
    DB --> API
    HT[Hedge Tools: converter, hedge cost, sizer] --> API
    EVT[Events Config] --> API
    API --> UI[Dashboard]
    SIG --> TG[Telegram Alerts / Digest]
    SIG --> PAPER[Paper Execution Adapter]
    PAPER --> POS[(Paper Positions / P&L)]
```

## 2. Daily / Replay Workflow

```mermaid
flowchart TD
    A[Start: daily run or historical replay date] --> B[Download or load cached Bhavcopy]
    B --> C{Requested date == returned date and schema valid?}
    C -- No --> X[Reject + log to Data Health]
    C -- Yes --> D[Pick adapter by file era; filter 4 gold symbols]
    D --> E[Store raw snapshot + hash]
    E --> F[Parse expiries; upsert contract-level rows]
    F --> G[Price quality: choose price_source; flag SUSPECT]
    G --> H[Normalize to rupees per 10g of 999]
    H --> I[Pair contracts by smallest expiry gap]
    I --> J[Carry from same-symbol curve, else fallback]
    J --> K[Log spread; z-score using data through t-1]
    K --> L[Lot ratio + residual grams]
    L --> M[Costs + slippage + buffer vs expected convergence to mean]
    M --> N[Evaluate ALL gates; record margins + reason codes]
    N --> O{All gates pass?}
    O -- Yes --> P[ALERT]
    O -- No --> Q[QUIET + nearest-miss metrics]
    P --> R[Store evidence record]
    Q --> R
    R --> S[Explainer EN/HI]
    P --> T[Telegram / Dashboard]
    P --> U[Optional paper trade]
```

Gate evaluation order is fixed for display. All gates are always evaluated:

| # | Gate | Fail reason code(s) |
|---|---|---|
| 1 | Spec status (per `spec_mode`) | `SPEC_UNVERIFIED` |
| 2 | Data validity | `DATA_INVALID` |
| 3 | Price quality | `PRICE_SUSPECT_A`, `PRICE_SUSPECT_B` |
| 4 | Expiry pair | `NO_EXPIRY_PAIR`, `EXPIRY_GAP_TOO_WIDE` |
| 5 | Carry | `CARRY_FALLBACK` (warning, or a fail if `block_on_carry_fallback`) |
| 6 | History sufficiency | `INSUFFICIENT_HISTORY` |
| 7 | Anomaly threshold | `BELOW_THRESHOLD` |
| 8 | Liquidity | `LIQUIDITY_VOL_A/B`, `LIQUIDITY_OI_A/B` |
| 9 | Expiry/tender safety | `EXPIRY_UNSAFE_A/B` |
| 10 | Cost hurdle | `COST_HURDLE_FAIL` |
| 11 | Duplicate suppression | `DUPLICATE_SUPPRESSED` |

## 3. Backtesting Architecture

```mermaid
flowchart LR
    DATA[(Versioned Dataset)] --> SPLIT[Chronological Fold Builder]
    SPLIT --> HOLD[(Final Holdout: locked)]
    CFG[Strategy Config] --> TRAIN[Train-only Parameter Selection]
    SPLIT --> TRAIN
    TRAIN --> TRIAL[(Trial Registry: every config tried)]
    TRAIN --> FREEZE[Freeze Fold Parameters]
    FREEZE --> TEST[Test on Unseen Fold]
    TEST --> EXEC[Simulated t+1 Execution + Slippage]
    EXEC --> COST[Itemized Costs]
    COST --> EXIT[Exit: reversion / time stop / expiry window]
    EXIT --> LEDGER[(Trade Ledger: actual contracts + lots)]
    LEDGER --> ATTR[Attribution: strategy vs residual gold]
    BASE[Baselines: always-quiet, random entry] --> REPORT
    ATTR --> REPORT[Fold + Overall Report + DSR]
    TRIAL --> REPORT
    HOLD -. run once after methodology freeze .-> REPORT
```

## 4. Layer Responsibilities

| Layer | Responsibility |
|---|---|
| Data source | Public daily contract-level Bhavcopy archives |
| Format adapters | Isolate era-specific file names, columns and date formats (legacy and CDP). Each outputs one canonical schema |
| Ingestion | Download, cache, hash, parse, validate, reject and log. Raw evidence is never mutated |
| Price quality | Choose the price source and flag stale or suspect prices |
| Storage | DuckDB for analytics; Parquet for immutable snapshots and versioned datasets |
| Quant | Normalization, pairing, carry, log spread, score, sizing, costs, slippage. All pure functions |
| Decision | Gate evaluator (all gates), dedupe, nearest miss, evidence records |
| Validation | Walk-forward backtest, baselines, attribution, Deflated Sharpe Ratio, trial registry |
| Tools | Converter, cheapest-to-hedge and lot sizer. Each reuses the quant functions with no new formulas |
| Explanation | Deterministic English/Hindi templates over evidence JSON; optional LLM rewrite behind a numeric guard |
| Service | FastAPI: versioned read endpoints plus token-protected admin actions |
| Presentation | Dashboard with nine screens, replay, watermark and disclaimer |
| Alerts | Telegram alerts (and an optional daily digest) behind an interface |
| Paper execution | Simulates the two-leg lifecycle and never calls a broker |

## 5. Data Lineage
Every displayed number resolves along this chain:

`source file (hash) → raw row → canonical daily_price row → normalized row → pair_daily row → gate_result rows → evidence record (config_version, dataset_version)`

The Evidence export (FR27) prints this chain.

## 6. Deployment

```mermaid
flowchart TB
    REPO[Git Repository] --> CI[CI: tests + secret scan + lint]
    CI --> APP[Docker / small VM]
    APP --> API[FastAPI]
    APP --> UI[Streamlit dashboard]
    APP --> JOB[Scheduled ingestion]
    APP --> VOL[(DuckDB + Parquet)]
    API --> UI
    JOB --> VOL
    LAPTOP[Presenter Laptop] -. offline cached dataset .-> DEMO[Offline Demo]
```

UI default: **Streamlit**. It is fastest to build for nine screens. Next.js is an alternative only if the team is already strong in React; the API contract is the same either way.

## 7. Security Boundary
- Public clients receive read-only analytical data.
- Refresh and backtest admin actions require a secret token from an environment variable, and are rate-limited.
- Secrets stay in environment variables, never in the repo.
- Symbols come from an allow-list. Date ranges and tool inputs (grams, lots) are bounded.
- No raw SQL or code is built from user input.
- The explainer receives structured evidence JSON only, never free user prompts. LLM output must pass the numeric guard.

## 8. Future Live-Execution Architecture (post-MVP)

```mermaid
flowchart LR
    SIG[Validated Signal] --> RM[Independent Risk Manager]
    RM -->|Approved| EX[Execution Orchestrator]
    RM -->|Rejected| LOG[Audit Log]
    EX --> BROKER[Broker Adapter]
    BROKER --> ORD[Pair Order Manager]
    ORD --> REC[Fill / Position Reconciliation]
    REC --> MON[Position Monitor]
    MON --> EXIT[Exit Engine]
    EXIT --> BROKER
    KILL[Kill Switch] --> EX
    LIMITS[Position / Loss / Slippage Limits] --> RM
```

The analytical engine must never call a broker directly.
