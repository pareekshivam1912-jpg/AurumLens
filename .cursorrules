# AurumLens Cursor Rules v2.1 (also use as AGENTS.md for Antigravity)

You are working on AurumLens, an MCX gold cross-contract relative-value intelligence project.
It also provides hedging-cost analytics. It is analytics only, not investment advice.

## Source of Truth
Read before changing implementation:
1. docs/PRD.md (v2)
2. docs/Design.md (v2)
3. docs/Phase.md (v2)
4. docs/System_architecture.md (v2)
5. CHANGELOG.md

Never change the analytical methodology silently. If documents conflict, stop and report the conflict.

## Product Boundaries
- AurumLens does NOT predict gold direction.
- MVP universe: GOLDM, GOLDTEN, GOLDGUINEA, GOLDPETAL.
- Core output: QUIET or ALERT, plus a full evidence record and the nearest miss.
- No real-money broker execution in the MVP. Paper execution sits behind an adapter.
- Never present synthetic fixtures as real-market results.
- Stack (v2.1): Python 3.12 engine (pandas, pure functions) + Parquet snapshots; Supabase (Postgres, Storage, Realtime, Auth); thin FastAPI for tools, explainer and admin; Next.js (TypeScript, Tailwind) built from Stitch designs. See docs/ANTIGRAVITY_BUILD_PLAN.md.
- Only the Python engine writes to Supabase, using the service-role key from the environment. The browser uses only the publishable key; RLS allows SELECT only.
- No formulas in SQL views, edge functions or UI. Views only select and join.
- The Supabase MCP stays read-only. Apply schema changes only as reviewed migrations, through the separately enabled write server.

## Facts & Specs
- Every external fact has a status: VERIFIED_OFFICIAL | SECONDARY | DISPUTED | TO_VERIFY.
- Never invent MCX/SEBI facts, file formats, costs or thresholds.
- spec_mode=strict: any spec that is not VERIFIED_OFFICIAL forces QUIET (SPEC_UNVERIFIED).
- spec_mode=research: computation is allowed, but every output is watermarked.
- GOLDGUINEA purity is DISPUTED until it is officially resolved.

## Mandatory Quant Rules
- Never compare raw contract prices.
- Normalize to Rs per 10 g of 999: P x (10/quote_basis_g) x (0.999/purity). Lower purity normalizes UP.
- Track actual contracts by symbol + expiry. No stitched continuous series.
- Pair expiries by the SMALLEST gap, within max_expiry_gap_days.
- Carry: same-symbol curve first, fallback rate second. Always record carry_source.
- Spread = log spread plus the carry adjustment.
- Scoring at t uses history through t-1 only.
- Expected convergence is measured to the rolling mean, not to zero.
- Use settlement (if available) or close per config. Flag SUSPECT prices (low volume, close/settlement gap).
- Evaluate ALL gates. Store pass/fail, value, threshold, margin and reason code for each.
- An anomaly score alone never triggers an alert.
- Default to QUIET when any input or gate is missing or failing.
- Size with integer lot ratios that minimize residual fine grams. Report the residual.
- ADF/cointegration tests are diagnostics only, never gates.
- Backtests are walk-forward with t+1 execution and adverse slippage. Log every config tried in the trial registry.
- The final holdout stays untouched until the methodology is frozen.
- Report gross, itemized costs, slippage, net, strategy P&L and residual gold P&L separately, plus baselines and the Deflated Sharpe Ratio.
- "No edge after costs" is a valid result.

## No Magic Numbers
All strategy values live in versioned config (config_version hash), including:
lookback, min history, entry/exit z, max expiry gap, carry fallback, price source, stale thresholds, volume/OI minimums, unsafe expiry window, cost rates, safety buffer, slippage model and fallback bps, convergence capture ratio, holding period, lot caps, walk-forward windows.
Unknown values are null with status TO_VERIFY/TO_VALIDATE. Never use a fabricated "reasonable" default.

## Data Rules
- Raw source snapshots are immutable, with a sha256.
- Era-specific parsing lives only in source adapters (legacy / cdp).
- Validate requested date vs returned date. Parse dates explicitly.
- Strip and standardize symbols, with an allow-list.
- Reject invalid records; never repair them silently. Conflicting duplicates are rejected and logged.
- Enforce uniqueness on contract + trade date.
- Every derived row carries config_version and dataset_version and traces back to a source file hash.
- Fixtures live under data/fixtures and are marked synthetic=true (real samples are labeled real).

## Coding Rules
- Python typing for public functions. Pydantic at config and API boundaries.
- Quant code is small pure functions; separate I/O from analytics.
- The UI contains no analytical formulas. Hedge tools reuse core functions and add none.
- Broker/paper adapters contain no signal logic.
- The explainer uses templates over evidence JSON. Any LLM output must pass the numeric guard.
- Dependency injection for external services (source, Telegram, LLM).
- Docstrings for non-obvious financial or statistical calculations. No premature abstractions.

## Testing Rules
Every analytical feature needs tests. Mandatory:
- normalization fixtures, plus the purity DIRECTION test;
- parser/date tests for BOTH formats;
- price-quality (SUSPECT) tests;
- smallest-gap expiry matching;
- carry curve vs fallback;
- all-gate evaluation (multiple reason codes);
- convergence-to-mean (a constant offset never alerts);
- cost tests (CTT sell-only, stamp buy-only, GST base);
- Corwin-Schultz fixture and fallback;
- lot-ratio and residual sign;
- strict spec mode;
- no-look-ahead regression;
- walk-forward isolation;
- deterministic seeded baselines;
- DSR responds to n_trials;
- explainer numeric guard and Hindi template coverage;
- duplicate prevention;
- API validation/auth/bounds;
- planted synthetic anomaly detection.

Changing future data must never change previously generated historical signals.

## Security
- No secrets in source. Use environment variables. .env.example has no values.
- Validate and bound all API and tool inputs.
- Admin actions require a token and are rate-limited.
- Never execute arbitrary code or SQL from user input.
- An LLM never determines numbers and never receives free user text.
- Show the "Analytics only — not investment advice" disclaimer on every screen.

## Workflow
Work one phase at a time. Before coding a phase:
1. State the phase objective and which [CORE] / [MVP+] / [STRETCH] items are in scope.
2. List the files to create or change.
3. List assumptions and TO_VERIFY items.
4. Implement the smallest end-to-end vertical slice.
5. Run the tests.
6. Report results.
7. Stop at the phase exit gate unless explicitly asked to continue.

Do not build UI before the core data pipeline produces verified real output.

## Change Discipline
When changing an analytical formula:
- explain why;
- update the docs and CHANGELOG;
- update the tests;
- bump the config/methodology version;
- preserve reproducibility.

Never improve reported performance by leaking test or holdout information into parameter selection.
