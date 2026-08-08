# ADX Quant Pro — Field 10 Institutional Shadow Upgrade

## Start here

The deployment keeps **`field10_daily_snapshot`** and **`field10_daily_snapshot_symbol`** as the only production ranking authority. All newly added models and evidence are versioned children and are **not promoted**.

### Deployment sequence

```bash
python --version                       # deployment target: Python 3.12
python scripts/migrate_field10_institutional_20260704.py   --db data/multi_symbol_field10_20260701.sqlite3   --report reports/DATABASE_MIGRATION_EXECUTION.json
pytest -q
streamlit run app.py
```

Heavy calculations remain owned by **Settings → Run Calculation + Open Lunch**. Lunch and startup are read-only and never launch a heavy run.

### Verified migration

- Migration: `20260704_field10_institutional_shadow_v1`
- Backup: `/mnt/data/field10_work/ADX_QUANT_PRO_FIELD10_CROWD_FINAL_20260704/backups/multi_symbol_field10_20260701.pre_20260704_field10_institutional_shadow_v1_20260704T133023Z.sqlite3`
- Backup integrity: `['ok']`
- Post-migration integrity: `['ok']`
- Foreign-key issues: `0`
- Idempotent second run: `True`

### Validation truth

There are only **2 broker-day parent snapshots**, **5 parent symbol rows**, and **0 institutional settled outcomes** in the uploaded database. Calibration, conformal coverage, SPA, PBO, Deflated Sharpe, accuracy and profitability therefore remain unvalidated or shadow-only.

Read `IMPLEMENTATION_REPORT.md`, `TEST_REPORT.md`, `KNOWN_LIMITATIONS.md`, and `ROLLBACK_INSTRUCTIONS.md` before deployment.
