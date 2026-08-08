# Rollback Instructions

## Verified backup

`/mnt/data/field10_work/ADX_QUANT_PRO_FIELD10_CROWD_FINAL_20260704/backups/multi_symbol_field10_20260701.pre_20260704_field10_institutional_shadow_v1_20260704T133023Z.sqlite3`

SHA-256: `5adbbcbf70d9c4d3e6bb6f31fd6bdafa9a3c0420abdbb35974ac3aec87e311fa`

## Procedure

1. Stop Streamlit and any process holding the database.
2. Preserve the current migrated database for forensics.
3. Copy the verified backup over `data/multi_symbol_field10_20260701.sqlite3`.
4. Remove stale `-wal` and `-shm` sidecars only while all database processes are stopped.
5. Run integrity and foreign-key checks.
6. Redeploy the previous source package if source rollback is also required.

```bash
cp data/multi_symbol_field10_20260701.sqlite3    data/multi_symbol_field10_20260701.migrated_rollback_copy.sqlite3
cp "/mnt/data/field10_work/ADX_QUANT_PRO_FIELD10_CROWD_FINAL_20260704/backups/multi_symbol_field10_20260701.pre_20260704_field10_institutional_shadow_v1_20260704T133023Z.sqlite3" data/multi_symbol_field10_20260701.sqlite3
rm -f data/multi_symbol_field10_20260701.sqlite3-wal       data/multi_symbol_field10_20260701.sqlite3-shm
python - <<'PYDB'
import sqlite3
p='data/multi_symbol_field10_20260701.sqlite3'
with sqlite3.connect(p) as c:
    c.execute('PRAGMA foreign_keys=ON')
    print(c.execute('PRAGMA integrity_check').fetchall())
    print(c.execute('PRAGMA foreign_key_check').fetchall())
PYDB
```

Rollback removes the institutional child schema/data introduced by this migration but preserves the pre-migration authoritative parent state exactly as backed up.

---

## 2026-07-07 focused repair rollback

The original uploaded ZIP remains the full clean rollback source. A local source backup of the principal edited modules is also stored under `backups/repair_20260707_api_selector_publication/`. Restore the corresponding file from that directory, or replace the repository with the original uploaded package. Database changes in this pass are additive/idempotent; no destructive migration was introduced.
