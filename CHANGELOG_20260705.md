# ADX Quant Pro — Repair Changelog (2026-07-05)

## Canonical state and calculation flow
- Added a shared canonical multi-symbol repair layer with selected-symbol, primary-symbol, timeframe, provider-priority, run, snapshot, candle-time and cache-identity metadata.
- All three Settings run modes now use explicit names and route successful runs to Lunch with Field 10 expanded and anchored at the top.
- Partial multi-symbol runs remain `PARTIAL`/`IN_PROGRESS`; they do not replace the latest complete publication. Per-symbol retries, fallback counts and publication guards were added.

## Data availability and provider handling
- Enforced provider order: Twelve Data, Finnhub, validated provider cache, local database, complete canonical snapshot, safe resampling, then explicitly labelled statistical estimates for derived features only.
- Added provenance fields for source, original timestamp, age, freshness, coverage, data-quality score, reliability and fallback level.
- Raw OHLC prices are never fabricated. Missing raw prices remain explicitly unavailable after validated sources are exhausted.
- Added measured Top 10 Secondary and Top 8 Low-Spread presets. Low-spread membership requires observed spread evidence below 20 points.

## Fields 1, 2, 10 and 11
- Replaced separate selector behavior with one shared read-only selector for Fields 1, 2 and 11, backed by the canonical symbol activation function.
- Field 10 now detects incomplete/constant/stale rows, adds provenance overlays, preserves the previous complete daily publication on partial failure, and uses responsive table/card rendering.
- Field 10 mobile view shows Rank, Symbol, Bias, Reliability, Expected Value and Risk first, with expandable detail; desktop view uses pinned key columns, filtering, sorting, wrapping and horizontal scrolling.
- Field 11 now exposes its enable control, shared symbol selector, selected timeframe, read-only refresh, structured fallback result, copy/AI context and safe M1/H1/H4/D1 OHLCV resampling.

## Refresh, copy and AI
- Lunch Refresh reloads persisted Field 10/11 evidence and invalidates presentation caches without starting a full calculation.
- Copy Short and Copy Full include structured Field 10 and Field 11 content while redacting secrets, credentials, internal paths and stack traces.
- The AI fact pack now includes current Run ID/timeframe, selected symbols, providers, Field 10 rankings and Field 11 status/results.

## Error handling and mobile UI
- Added incident-based internal logging and replaced raw exception text on critical Settings/startup surfaces with user-safe messages.
- Added consistent bias, reliability, data-quality, fallback and ranking visualization while keeping text readable.

## Persistence
- Added idempotent, backup-first migrations for canonical runs, symbol results, Field 10 rankings, Field 11 results, provider status, provenance, fallback records, timeframe results, progress, failures and prediction outcomes.
- Existing database rows were preserved and both migrated databases passed SQLite integrity checks.
