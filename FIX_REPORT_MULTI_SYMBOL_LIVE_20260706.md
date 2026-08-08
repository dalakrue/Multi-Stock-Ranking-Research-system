# Multi-Symbol Live Repair — 2026-07-06

## Implemented repair

This patch repairs the Settings-owned **Super Quick Calculation + Open Lunch** transaction and the Lunch multi-symbol display path without changing the protected Full Metric formulas, thresholds, scores, ranks, or tradeability logic.

### Field 1 and Field 2 selector

- Field 1 and Field 2 use the same shared completed-symbol selector contract.
- Each field has an explicit **Load Selected Symbol** button.
- A symbol switch first restores the exact persisted child publication.
- When legacy database publication metadata is absent, the selector may restore the exact-symbol runtime cache only after strict child-state validation.
- A rejected or partial cache cannot leave Fields 1 or 2 pointed at mixed-symbol state.
- Selector actions remain read-only: no provider request and no hidden calculation.

### All selected symbols and Field 10

- Every run with more than five selected symbols now enables quota-safe pacing, not only one specific button mode.
- The Settings run uses batches of four, leaving safety capacity for connector validation and concurrent rolling-window usage.
- Before each likely Twelve Data request, the scheduler checks the persistent quota ledger and waits for the next safe request window when necessary.
- Only requests actually sent to Twelve Data count against the scheduler batch.
- Incomplete symbols are retried independently for up to three configured rounds; already-complete symbols are not recalculated.
- The transaction is not marked complete while any selected symbol is unresolved or has fewer candles than the selected-timeframe higher-standard contract.
- One symbol/provider failure is isolated so it cannot abort the other selected symbols.

### H4 data-quality contract

- H4 is no longer incorrectly judged by the H1 600-candle requirement.
- The H4 higher-standard requirement is 150 completed H4 candles.
- Candle spacing validation now follows the selected timeframe.
- Legal FX weekend gaps are not treated as missing provider candles.

### Field 10 Time columns

- Every centrally rendered Field 10 table now includes visible **Time** and **Timeframe** columns.
- The authoritative rank table, research rank candidate, historical tables, crowd-psychology rank, and final multi-symbol rank are covered.
- Time is read only from persisted/canonical completed-candle identity; the display layer does not invent market timestamps.

### Canonical authority error

- The protected `core/full_metric_canonical_adapter_20260618.py` remains byte-for-byte unchanged.
- Multi-symbol child runs satisfy its original EURUSD/H1 operational gate, then use an identity-only adapter to stamp the actual child symbol/timeframe.
- The identity adapter does not recalculate or replace any score, formula, direction, threshold, rank, or tradeability value.
- This removes the erroneous `Operational canonical authority requires EURUSD H1` failure during valid multi-symbol child publication.

## Validation

- Python compilation passed for `core`, `ui`, `tabs`, and `tests`.
- All 506 collected project tests passed when executed in deterministic file batches.
- The protected Full Metric adapter SHA-256 remains:
  `b596a04ff0a1265bf1b64c95e665597e3b0eccc9a22c5b75b7be50fde82e506b`
- Six dedicated regression tests were added for this repair.

## Operational note

The application never fabricates candle history or quantitative estimates. A configured provider still must return valid market data. When rolling quota is temporarily unavailable, the Settings transaction now waits and retries instead of silently leaving the final selected symbols incomplete. Persistent invalid credentials, a provider outage, or exhausted daily account allowance remains an explicit provider failure rather than being displayed as sufficient data.
