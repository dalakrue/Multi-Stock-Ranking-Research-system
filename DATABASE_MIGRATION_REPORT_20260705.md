# Database Migration Report — 2026-07-05

## Result
- Main database: **MIGRATED**
- Main schema version: **20260705**
- Field 11 database: **MIGRATED**
- Field 11 schema version: **1**
- Idempotent second run: **PASS**
- Main integrity check: **ok**
- Field 11 integrity check: **ok**
- Existing main rows preserved: **True**
- Existing Field 11 rows preserved: **True**
- Backup created: `/mnt/data/adx_work/ADX_QUANT_PRO_FIELD10_CROWD_FINAL_20260704/data/backups/multi_symbol_field10_20260701.pre_20260705_20260705T081618Z.sqlite3`

## Added or validated tables
- `canonical_runs_20260705`
- `canonical_symbol_results_20260705`
- `field10_rankings_20260705`
- `field11_results_20260705`
- `provider_status_20260705`
- `data_quality_metadata_20260705`
- `missing_data_fallback_20260705`
- `timeframe_results_20260705`
- `calculation_progress_20260705`
- `calculation_failures_20260705`
- `prediction_outcomes`

## Existing evidence retained
- Field 10 daily snapshots before/after: **2 / 2**
- Field 10 daily safety events before/after: **74 / 74**
- Research validation rows before/after: **72 / 72**
- Publication diagnostics before/after: **100 / 100**

The migration is additive. No existing table was dropped and no historical row count decreased.
