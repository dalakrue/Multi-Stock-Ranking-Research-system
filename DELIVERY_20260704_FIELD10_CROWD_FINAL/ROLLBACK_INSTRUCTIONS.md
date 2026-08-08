# Rollback Instructions

## Database rollback

Stop Streamlit, archive the migrated DB, then restore the verified backup:

```bash
cp data/multi_symbol_field10_20260701.sqlite3 \
  backups/multi_symbol_field10_20260701.post_crowd_final_rollback_audit.sqlite3
cp backups/multi_symbol_field10_20260701.pre_crowd_final_20260704_verified.sqlite3 \
  data/multi_symbol_field10_20260701.sqlite3
```

Verify with `PRAGMA integrity_check` and `PRAGMA foreign_key_check`. Expected backup SHA-256: `47a1b1209cda053fdd178c4ed0ce2d3f2848f46625685ea2f8506cbe5b34e41e`.

## Full code rollback

Redeploy the prior known-good source archive/release, then restore the backup above. The safer non-destructive option is to deploy prior code while leaving additive tables unused; do not drop audit/outcome tables unless they are archived first.

To reapply, deploy this package and rerun the idempotent migration command in `README_FIRST.md`.
