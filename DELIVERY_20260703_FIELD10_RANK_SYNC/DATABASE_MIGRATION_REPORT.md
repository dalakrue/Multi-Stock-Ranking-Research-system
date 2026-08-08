# Database Migration Report

Database: `data/multi_symbol_field10_20260701.sqlite3`

Migration: `field10-unified-rank-columns-20260703-v1`

Final result:

- Status: **PASS**
- SQLite integrity check: **ok**
- Foreign-key issues: **0**
- Missing requested columns: **none**

Verified tables and columns:

- `field10_hourly_quality`
  - `transition_risk_24h`
  - `expected_return_12h`
- `field10_daily_higher_lock`
  - `transition_risk_24h`
  - `expected_return_12h`
- `field10_daily_snapshot_symbol`
  - `transition_risk_24h`
  - `expected_return_12h`
- `field10_integrated_evidence_history`
  - `transition_risk_24h`
  - `expected_return_12h`

The migration is additive and repeat-safe. An audit record is saved in `field10_schema_migration_audit_20260703`.
