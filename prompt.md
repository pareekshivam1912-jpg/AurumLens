# AurumLens --- Implementation Idea Prompt

## Project Objective

Upgrade **AurumLens** into a reliable, explainable commodity-market
intelligence platform focused initially on MCX gold contracts and
related gold instruments.

AurumLens should help users understand market conditions, inspect
quantitative signals, evaluate hypothetical trades, and monitor
portfolio risk through one integrated dashboard and **one unified AI
chatbot**. The product must prioritize transparent calculations,
reliable data, risk controls, and clear explanations over unsupported
predictions or aggressive buy/sell claims.

This document defines the product direction and implementation
requirements. The implementation team should inspect the existing
repository and preserve working functionality before making changes. Do
not rebuild working modules unnecessarily.

------------------------------------------------------------------------

## 1. Product Principles

1.  **Data-backed, not hallucinated:** Prices, indicators, signals,
    positions, P&L, and risk metrics must come from verified application
    data or deterministic calculations.
2.  **Explainable decisions:** Every signal should show the evidence,
    assumptions, thresholds, timestamp, and filters that produced it.
3.  **Risk-first design:** A statistically unusual spread is not
    automatically a profitable trade. Liquidity, transaction costs,
    expiry, slippage, contract specifications, and market risks must be
    considered.
4.  **Clear data status:** Label information as live, delayed,
    historical, simulated, or unavailable. Never present demo data as
    live market data.
5.  **Paper trading first:** The initial implementation must not place
    real broker orders.
6.  **One assistant:** Trading education, signal explanation, market
    analysis, portfolio management, and hypothetical risk simulation
    must all be accessible through the same chatbot interface.
7.  **Auditable behavior:** Important calculations, signal decisions,
    data-quality events, and simulated portfolio changes should be
    traceable.
8.  **No guaranteed outcomes:** Avoid claims of guaranteed profit,
    certain reversals, or risk-free strategies.

------------------------------------------------------------------------

## 2. Core Dashboard

Create a clear, responsive dashboard with the following sections:

### A. Market Overview

-   Current market-data status and last successful update time.
-   Supported contract list and contract metadata.
-   Available prices and changes, with units and timestamps.
-   Market session status when reliable session information is
    available.
-   Volatility and liquidity summaries.
-   Warnings for stale, missing, inconsistent, or unavailable data.

### B. Interactive Chart

-   Candlestick chart and volume visualization where data is available.
-   Historical range and timeframe selection.
-   Crosshair, price scale, time scale, and readable tooltips.
-   Strategy signal markers and simulated entry/exit markers.
-   Entry, stop-loss, and target reference lines when applicable.
-   Optional indicator overlays with visible definitions and settings.
-   Separate views for raw contract prices and normalized analytical
    prices.
-   A spread chart for comparing two eligible contracts.
-   A Z-score or deviation panel for statistical spread analysis.
-   Loading, empty, error, stale-data, and unavailable-data states.

Use an embeddable chart widget only as a quick visual component when its
limitations fit the requirement. For charts that must display
AurumLens-specific data, normalized prices, spread calculations, and
custom signal overlays, use a charting component that accepts
application-supplied data. Charting software does not itself provide
permission to access or redistribute exchange market data.

### C. Signal Monitor

For each signal, display: - Instrument or contract pair. - Signal
direction or classification. - Signal timestamp and data timestamp. -
Spread value and normalized value where relevant. - Z-score and
configured threshold. - Strategy version and parameter set. - Entry
logic and invalidation conditions. - Liquidity, expiry,
transaction-cost, and risk-filter results. - Reasons a signal was
accepted, rejected, or blocked. - Clear distinction between an
analytical signal and an executable trade instruction.

### D. Portfolio Snapshot

-   Available simulated cash and portfolio value.
-   Open and closed paper positions.
-   Realized and unrealized P&L, with calculation basis.
-   Exposure by contract and strategy.
-   Position concentration and correlated exposure.
-   Estimated risk under stated assumptions.
-   Drawdown and performance history.
-   Trade history and audit trail.

All portfolio metrics must be calculated from validated position, price,
fee, and transaction records. If required inputs are missing, show the
metric as unavailable rather than fabricating a value.

------------------------------------------------------------------------

## 3. Unified AurumLens AI Chatbot

Build one conversational assistant called **AurumLens AI**. Do not
create separate Trading Guide and Portfolio Manager bots or force users
to switch between different chat experiences.

The chatbot should identify user intent and use the appropriate approved
application tools while maintaining relevant conversation context.

### Supported Capabilities

#### A. Trading Guide and Education

-   Explain trading and quantitative-analysis concepts in simple
    language.
-   Explain spreads, Z-scores, volatility, liquidity, expiry, slippage,
    and transaction costs.
-   Explain what a displayed signal means and what it does not mean.
-   Explain the assumptions and limitations of a strategy.
-   Provide educational examples and hypothetical scenarios.
-   Clarify the difference between correlation, statistical deviation,
    and a reliable trading opportunity.

#### B. Market and Signal Analysis

-   Summarize available market conditions using timestamped data.
-   Explain why a signal was generated, filtered, or blocked.
-   Compare eligible contracts using normalized values and matching
    rules.
-   Explain recent changes in a spread or indicator when sufficient
    historical data exists.
-   Identify missing data or conflicting evidence.
-   Provide a concise evidence summary and list important risks.

#### C. Portfolio Manager

-   Answer questions about the user's saved paper portfolio.
-   Summarize holdings, open positions, exposure, P&L, and drawdown.
-   Identify concentration and correlated-position risks.
-   Calculate hypothetical position sizing from user-defined risk limits
    and validated contract specifications.
-   Compare a proposed hypothetical position with the existing
    portfolio.
-   Run what-if scenarios, such as a specified adverse price move.
-   Explain how assumptions, fees, slippage, or missing prices affect
    the result.

#### D. Conversational Context

-   Remember relevant details within the current conversation, such as
    the selected contract, timeframe, signal, or portfolio under
    discussion.
-   Ask a concise follow-up question when a necessary input is missing.
-   Allow users to correct assumptions or change scenario parameters.
-   Avoid assuming a user's holdings, capital, risk tolerance, or
    trading experience without a reliable source.

### Chatbot Tool and Data Rules

-   The AI must retrieve data through controlled application tools
    rather than directly modifying databases.
-   Financial calculations must be performed by deterministic
    application services, not estimated by the language model.
-   Every response involving market data must include the relevant
    timestamp and data status.
-   Portfolio answers must be scoped to the authenticated user's own
    records.
-   The chatbot must not invent live prices, market events, signal
    values, holdings, fees, margins, or P&L.
-   If a requested capability or data source is unavailable, state that
    clearly and provide a useful alternative.
-   The initial chatbot must be read-only for portfolio records, with
    separate, explicitly confirmed actions for creating or closing
    simulated positions.
-   No real-money order placement in the initial release.

### Suggested Conversation Examples

-   "Why did this spread signal appear?"
-   "Explain the current Z-score in simple terms."
-   "Why was this opportunity blocked?"
-   "Compare these two contracts after normalization."
-   "What is my simulated portfolio's current exposure?"
-   "What happens to my portfolio if gold falls by 2%?"
-   "Show the assumptions used in this risk estimate."
-   "Explain the difference between this analytical price and the actual
    contract price."

------------------------------------------------------------------------

## 4. Market Data and Data Quality

Design a clear data pipeline that can support demo/historical data
initially and an authorized market-data provider later.

### Requirements

-   Store source, instrument identifier, timestamp, price units, and
    data status.
-   Validate required fields, numeric ranges, timestamps, duplicate
    records, missing intervals, and inconsistent OHLC values.
-   Detect stale feeds and prevent stale data from silently producing
    fresh-looking signals.
-   Handle time zones and trading sessions consistently.
-   Preserve raw source data separately from transformed or normalized
    analytical data when appropriate.
-   Record data-quality warnings and their impact on calculations.
-   Support retry and recovery behavior without duplicating records.
-   Display the difference between historical, delayed, simulated, and
    live information.
-   Do not scrape or redistribute market data without appropriate
    authorization.

### Data-Source Independence

The application should isolate its chart and analytics layers from any
one market-data provider. A provider can be changed without rewriting
portfolio calculations or the chatbot experience.

------------------------------------------------------------------------

## 5. Contract Normalization and Relative-Value Analytics

The initial analytical focus is cross-contract gold relative-value
analysis.

### Required Logic

-   Maintain verified contract metadata, including lot size, units,
    purity or fineness where applicable, expiry, and other relevant
    specifications.
-   Normalize contracts to a clearly defined comparable basis only when
    the necessary metadata is available and validated.
-   Keep raw tradable contract prices separate from normalized
    analytical values.
-   Match expiries and contract pairs according to documented rules.
-   Account for carry, expiry effects, transaction costs, liquidity,
    slippage, and contract-specific risks where the required inputs
    exist.
-   Calculate spread values, historical distributions, and Z-scores
    using documented windows and formulas.
-   Make thresholds and strategy parameters explicit, versioned, and
    auditable.
-   Apply risk and quality gates before classifying a candidate
    opportunity.
-   Do not treat a high absolute Z-score as sufficient evidence for a
    trade.
-   Display the reasons a candidate was rejected or blocked.

### Signal Output

Each signal record should contain, at minimum: - Instrument or contract
pair. - Calculation timestamp and underlying data timestamps. - Strategy
and parameter version. - Input values and calculated spread metrics. -
Thresholds evaluated. - Data-quality, liquidity, expiry, and risk-filter
results. - Final classification and human-readable explanation.

------------------------------------------------------------------------

## 6. Paper Trading and Portfolio Risk

Provide a simulated trading environment to validate the complete
workflow without sending orders to a broker.

### Paper Trading

-   Create a simulated position only after the user explicitly confirms
    the action.
-   Record the signal or rationale associated with the simulated trade.
-   Store simulated entry, quantity, fees, slippage assumptions, and
    stop/invalidation conditions.
-   Update unrealized P&L only when a valid price is available.
-   Record exits, fees, realized P&L, and the reason for closing.
-   Maintain an immutable or auditable event history for important
    portfolio changes.
-   Clearly label all positions and performance as simulated.

### Risk Controls

-   Configurable maximum risk per hypothetical trade.
-   Maximum exposure by contract and overall portfolio.
-   Concentration and correlated-position checks.
-   Drawdown monitoring.
-   Liquidity and expiry restrictions.
-   Scenario analysis with explicit assumptions.
-   Warnings when market data is stale or a risk calculation cannot be
    completed.

### Performance Evaluation

-   Include transaction costs and slippage assumptions in backtests.
-   Use chronological train/validation/holdout separation where
    applicable.
-   Support walk-forward evaluation.
-   Avoid look-ahead bias and data leakage.
-   Compare against a documented baseline.
-   Report sample size, drawdown, risk-adjusted performance, hit rate,
    and other metrics with clear definitions.
-   Do not present a small backtest or demo result as proof of future
    profitability.

------------------------------------------------------------------------

## 7. Chart and Analytics Integration

The chart should be a visualization layer for verified AurumLens data,
not the source of truth for calculations.

### Requirements

-   Create a consistent chart-data contract for candles, volume,
    indicators, signals, and simulated trade markers.
-   Keep timestamps, units, contract identifiers, and data status
    explicit.
-   Support historical loading and, when an authorized feed is
    available, incremental updates.
-   Ensure chart markers correspond to persisted signal and paper-trade
    records.
-   Allow the chatbot to query the same underlying analytics records
    shown on the chart.
-   Provide a way to select a signal or time range and ask AurumLens AI
    to explain it.
-   Clearly distinguish normalized spread charts from raw exchange-price
    charts.
-   Never infer exact values from rendered pixels when the source
    records are available.

------------------------------------------------------------------------

## 8. User Experience and Accessibility

-   Use one consistent, uncluttered interface.
-   Keep the main market overview, chart, signals, portfolio summary,
    and chatbot easy to discover.
-   Make complex financial concepts understandable without hiding
    technical details.
-   Show units, timestamps, assumptions, and definitions near relevant
    metrics.
-   Provide clear empty, loading, error, stale-data, and
    unavailable-data states.
-   Use responsive layouts for desktop and mobile.
-   Support keyboard navigation, readable contrast, and accessible
    labels.
-   Make warning states distinguishable without relying on color alone.
-   Let users inspect the calculation or evidence behind an important
    metric.
-   Avoid excessive alerts and unexplained indicators.

------------------------------------------------------------------------

## 9. Security, Privacy, and Auditability

-   Require authentication for personal portfolio data.
-   Enforce server-side authorization on every portfolio operation.
-   Prevent users from reading or modifying other users' records.
-   Validate all input parameters and restrict tool calls to approved
    operations.
-   Keep credentials and provider secrets out of source code and
    client-visible configuration.
-   Avoid logging secrets or unnecessary personal information.
-   Record important signal-generation events, portfolio mutations,
    administrative changes, and AI tool invocations.
-   Apply rate limits and abuse controls to chatbot endpoints.
-   Treat external content and retrieved data as untrusted input.
-   Require explicit confirmation for simulated portfolio mutations.
-   Do not permit the AI to bypass application permissions or risk
    gates.
-   Define retention and deletion behavior for chat history and
    portfolio records.

------------------------------------------------------------------------

## 10. Implementation Sequence

### Phase 0 --- Repository and Product Audit

-   Inspect the existing application, modules, data structures, routes,
    and current behavior.
-   Identify working features, incomplete areas, known defects, and
    duplicated logic.
-   Preserve working functionality.
-   Produce a gap analysis and implementation checklist before making
    broad changes.

### Phase 1 --- Reliable Market Data and Charts

-   Standardize market-data records and data-quality states.
-   Implement historical/demo data loading.
-   Build the interactive chart and timeframe controls.
-   Add signal markers only when they correspond to valid records.
-   Label demo and historical data clearly.

### Phase 2 --- Analytics and Explainable Signals

-   Verify contract metadata and normalization rules.
-   Implement or validate spread, Z-score, and filtering logic.
-   Version strategy parameters.
-   Add signal explanations and blocked-signal reasons.
-   Test calculations against known examples.

### Phase 3 --- Portfolio and Paper Trading

-   Add simulated cash, positions, trade history, and P&L
    reconciliation.
-   Implement exposure, drawdown, and scenario analysis.
-   Add position and portfolio risk limits.
-   Validate all calculations with test cases.

### Phase 4 --- Unified AurumLens AI

-   Build a single chat interface.
-   Define approved tools for market analysis, signal lookup,
    educational retrieval, portfolio summaries, and risk simulation.
-   Connect the assistant to verified records and deterministic
    calculations.
-   Add contextual follow-ups, source timestamps, and clear failure
    responses.
-   Enforce authentication and authorization on every tool.

### Phase 5 --- Integration and Validation

-   Ensure chart, signal engine, portfolio, and chatbot use consistent
    underlying records.
-   Test stale data, missing data, invalid contracts, and provider
    outages.
-   Verify that AI responses match backend calculations.
-   Test permissions, rate limits, audit records, and confirmation
    flows.
-   Run backtests with realistic costs and leakage controls.
-   Conduct usability and accessibility checks.

### Phase 6 --- Live-Data Readiness

-   Select a provider with appropriate permissions for the intended use.
-   Verify coverage, latency, reliability, redistribution rights, and
    costs.
-   Implement monitoring and feed-health alerts.
-   Validate the live feed against trusted reference data.
-   Keep live trading execution out of scope unless separately reviewed
    and explicitly authorized.

------------------------------------------------------------------------

## 11. Acceptance Criteria

The implementation is not complete until all applicable criteria pass:

-   [ ] Demo, historical, delayed, and live data are clearly
    distinguished.
-   [ ] Charts use validated application data and correct timestamps.
-   [ ] Raw prices and normalized analytical values are not confused.
-   [ ] Every displayed signal can be traced to its inputs, strategy
    version, and filters.
-   [ ] Blocked signals include understandable reasons.
-   [ ] Portfolio P&L reconciles against recorded positions, prices, and
    costs.
-   [ ] Risk scenarios state their assumptions and limitations.
-   [ ] The chatbot uses verified backend results and does not fabricate
    financial values.
-   [ ] One chatbot supports education, market analysis, signal
    explanations, portfolio management, and hypothetical scenarios.
-   [ ] User-specific portfolio data is protected by server-side
    authorization.
-   [ ] Simulated trade creation or closure requires explicit user
    confirmation.
-   [ ] No real broker orders are placed.
-   [ ] Stale or missing data cannot silently appear current.
-   [ ] Backtests account for costs and prevent look-ahead bias.
-   [ ] Important data and portfolio events are auditable.
-   [ ] Existing working features remain functional after the upgrade.

------------------------------------------------------------------------

## 12. Instructions to the Implementation Agent

Treat this document as the product and implementation brief.

1.  First inspect the existing repository and summarize its current
    structure and functionality.
2.  Map existing modules to the requirements in this document.
3.  Identify the highest-priority gaps and propose a phased execution
    plan.
4.  Implement in small, testable increments, preserving existing working
    behavior.
5.  Reuse established project conventions rather than introducing
    unnecessary dependencies or duplicating services.
6.  Before changing a financial formula, document its intended behavior
    and validate it against explicit test cases.
7.  Do not invent market data, credentials, exchange permissions, user
    holdings, or performance results.
8.  Do not claim that a feature is complete unless it has been
    implemented and tested.
9.  Report completed work, changed files, tests performed, known
    limitations, and next steps after each phase.
10. Keep real-money execution out of scope for this implementation.

**Final product vision:** AurumLens should make quantitative commodity
analysis understandable and actionable through transparent charts,
explainable signals, realistic paper trading, portfolio risk
intelligence, and one unified AI assistant---without compromising data
integrity or overstating what the system knows.
