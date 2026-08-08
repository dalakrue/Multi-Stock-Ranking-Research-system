# Database Migration Report

Migration ID: `20260706_timeframe_identity_child_publication_v1`

## Backup

Before migration, the SQLite database was copied to:

`backups/multi_symbol_field10_20260701.pre_20260706_timeframe_identity_child_publication_v1.sqlite3`

The backup is included in the delivery package.

## Idempotent migration behavior

The migration runs:

1. at `app.py` startup, before the UI;
2. before the multi-symbol calculation transaction;
3. safely on repeated startup without deleting legacy rows.

## Added canonical identity

Relevant legacy tables receive additive columns where absent:

- `timeframe`
- `completed_candle`
- `parent_run_id`
- `child_run_id`
- `canonical_run_id`
- `generation_id`
- `snapshot_hash`
- `source_id`

Legacy columns remain available for compatibility. Legacy H1 records are not deleted.

## New tables

- `child_snapshot_publication_20260706`
- `field2_powerbi_publication_20260706`
- `multi_symbol_state_machine_20260706`
- `field10_shadow_research_validation_20260706`
- `schema_migrations_20260706`

The primary keys of the child and Field 2 publication tables include symbol, timeframe, completed candle, parent/child/canonical run IDs, generation and snapshot hash. H1 and H4 publications therefore cannot overwrite one another.

## Verification on delivered database

- `PRAGMA integrity_check`: **ok**
- foreign-key violations: **0**
- preserved legacy `field10_daily_snapshot` rows: **2**
- preserved legacy `field10_daily_snapshot_symbol` rows: **5**
- new runtime publication tables are empty in the deployable production database, so deterministic test fixtures were not shipped as real market publications.

Detailed machine-readable evidence: `test_artifacts/database_migration_verification_20260706.json`.

---

## 2026-07-07 repair note

No destructive schema change was required for the API-selector/publication repair. Existing normalized candle, provider-health, fallback-event and child-publication tables are reused. The application continues to execute existing additive/idempotent deployment migrations. The new validation diagnostics are stored in existing JSON/detail fields and runtime status structures.
