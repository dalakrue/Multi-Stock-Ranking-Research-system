# Implementation Report

## Scope completed

- Field 1 Table 5 remains sourced by `build_integrated_decision_collection()` and is enriched only on a deep copy.
- The exact existing Field 1 Table 4 calculation was extracted into `build_field1_table4_publication()` and is called by both Field 1 rendering and the Field 10 bridge.
- Every completed symbol generation attempts one identity-verified Table 4 publication after its frozen runtime snapshot is saved.
- Main symbol remains first. Secondary symbols retain `LUNCH_CORE` scope (Fields 1–3 plus Field 10); Fields 4–9 and AI are not executed for secondaries.
- Field 10 includes the requested current integrated evidence table, a persistent combined 25-broker-day history, full filtered CSV export, and exactly one new Plotly evidence-alignment heatmap.
- Research values are shadow-only. Existing Combined Evidence Bias and Protected Final Action are persisted separately and never replaced.
- Field 10 rendering now reads persisted research results; it does not run heavy research calculations when opened or filtered.

## Canonical and broker-time integrity

Rows require symbol, timeframe, canonical run ID, source ID, snapshot hash and completed broker candle identity. Table 4 rows are matched to the active frozen completed H1 candle. Identity failures are returned as explicit failed publication reports; no empty successful row is written.

## Missing-data behavior

Missing component evidence remains SQL `NULL`/display `UNAVAILABLE`. Missing evidence is excluded from the shadow-fusion denominator and is never converted to WAIT. Unsettled outcomes are masked from correctness, actual direction, Brier score and conditional-accuracy fields.

## Persistence behavior

SQLite WAL mode and migration-safe `CREATE TABLE/INDEX IF NOT EXISTS` statements are used. `INSERT OR IGNORE` enforces the requested composite uniqueness identity. A pruning statement retains at most 600 completed H1 rows per symbol. History queries are paginated and bounded; complete filtered CSV export is capped by the persisted 600-row-per-symbol store.

## API router behavior

The new router wraps the existing connector and existing composite profile signature. Its request key contains provider, canonical symbol, provider alias, timeframe, candle count, completed H1 identity and profile signature. It uses one sequential shared provider session policy, bounded temporary-error retry, exact-candle frame reuse, isolated per-symbol failure reports and no persisted credentials/endpoints.
