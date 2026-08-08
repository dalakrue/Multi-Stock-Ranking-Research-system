# ADX Quant Pro — Field 10 Immutable Daily Ranking Delivery

Delivered: 2026-07-02

This folder documents the institutional Field 10 upgrade: **One Morning, One Decision — Locked Multi-Symbol Daily Ranking**.

## Start Here

1. `IMPLEMENTATION_REPORT.md`
2. `ACCEPTANCE_MATRIX.md`
3. `TEST_REPORT.md`
4. `INCOMPLETE_ITEMS.md`
5. `DEPLOYMENT_INSTRUCTIONS.md`

## Key Verified Results

- 271 repository tests passed.
- 33 new acceptance tests passed.
- Compileall, Streamlit startup/health, preflight, and fresh/existing SQLite migration passed.
- Current-day publication is insert-once/checksum-validated and survives process restart from SQLite.
- 599 candles are blocked; 600 valid completed H1 candles can become eligible.
- 23:00 settlement and next-day candidates cannot overwrite the locked table.
- Safety Veto cannot change locked rank or direction.
- No protected source file was removed.

## Evidence and Registries

- `FIELD10_DATA_DICTIONARY.csv`
- `RANKING_FORMULA_THRESHOLD_REGISTRY.json`
- `DATABASE_MIGRATION_REPORT.md`
- `RESEARCH_METHODOLOGY_REPORT.md`
- `PERFORMANCE_COMPARISON.md`
- `CHANGED_FILE_MANIFEST.md`
- `SHA256_MANIFEST.txt`
- `RAW_EVIDENCE/`
