# Field 10 Rank Table, Lunch Sync, and Database Migration

Build: `2026-07-03`

## Completed changes

- Added **Transition Risk 24H** to the single authoritative **Today First — Ranked Multi-Symbol Decision Table**.
- Added **Expected Return 12H (%)** to the same table.
- Transition Risk 24H is calculated causally from the exact symbol's completed H1 regime hazard.
- Expected Return 12H is calculated from strictly historical, same-symbol H1 analogues whose 12-hour outcomes are already known. It is a signed percentage estimate, not a guaranteed target.
- Added both values to Field 10 daily snapshot, hourly quality, daily higher-standard lock, integrated evidence history, Field 3/Field 10 overlay, child publication, CSV loading, and UI metrics.
- Removed the two duplicate ranked surfaces:
  - `Multi-Symbol Run and Rank Summary`
  - `Today — Locked Higher-Standard Regime, Rank, Data Quality and Less-Risky Bias`
- Consolidated their useful non-ranking information into one collapsed section:
  - `Legacy / Diagnostics — Previous Field 10 Surfaces`
- Removed the second Field 10 symbol selectbox. Field 10 now consumes the symbol selected by the top Lunch Symbol Connector.
- Kept one active symbol contract for Lunch Fields 1–3 and Fields 10–11 while Fields 4–9 + AI remain attached to the Settings main symbol.
- Added an idempotent unified migration invoked after the Settings multi-symbol publication and on the first Lunch render.

## Synchronization contract

1. Settings ordered multi-symbol selection defines the main and comparison universe.
2. Settings calculation publishes completed child snapshots into one Field 10 SQLite database.
3. Unified migration verifies all Field 10 tables and requested columns.
4. Lunch Symbol Connector activates one saved child generation.
5. Field 10 reads that same active symbol; it does not maintain another selector or reconnect an API.
6. The Today First table is the only authoritative Field 10 rank table.

## Data integrity behavior

The migration backfills only evidence that already exists. It never writes a fake zero expected return. Older locked rows with a saved six-hour transition risk can receive a mathematically compounded 24-hour probability. Older rows without genuine 12-hour forward evidence remain null until a completed run computes and persists the new metric.
