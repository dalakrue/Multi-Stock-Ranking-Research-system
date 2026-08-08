# Database Migration Report

- Migration: `field10-crowd-final-unified-migration-20260704-v1`
- Status: **PASS**
- Tables: 31 before, 37 after
- Integrity: `ok`
- Foreign-key issues: 0
- Missing tables/indexes/PKs: 0
- Secret-like columns: 0
- Duplicate production rank tables: 0

## Added tables

- `field10_daily_session_entry_map` — PK `(daily_snapshot_id, symbol, session_name)`.
- `field10_daily_crowd_psychology_rank` — 114 columns, PK `(daily_snapshot_id, symbol)`.
- `field10_daily_final_multi_symbol_rank` — 123 columns, PK `(daily_snapshot_id, symbol)`.
- `field10_crowd_psychology_outcome` — immutable outcome ledger.
- `field10_final_multi_symbol_outcome` — immutable outcome ledger.

Indexes cover broker day, snapshot, symbol, rank, publication, lock, and completed candle. Child tables reference the existing daily snapshot parent.

## Backup and commands

Migrated DB SHA-256: `6a9318814226e2e60bd74f3fb5b35154f90d29b9ace091932d2acdc0abacdb02`  
Verified pre-migration backup SHA-256: `47a1b1209cda053fdd178c4ed0ce2d3f2848f46625685ea2f8506cbe5b34e41e`

```bash
python scripts/migrate_field10_crowd_final_20260704.py \
  --database data/multi_symbol_field10_20260701.sqlite3 \
  --backup backups/multi_symbol_field10_20260701.pre_crowd_final_20260704_verified.sqlite3
python scripts/migrate_field10_crowd_final_20260704.py \
  --database data/multi_symbol_field10_20260701.sqlite3 --no-backup
```

Both passed. No drop or destructive rename occurred. New publication tables remain empty until the next valid Settings run, by design.
