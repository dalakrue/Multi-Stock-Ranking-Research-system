# README FIRST — Field 10 Crowd Psychology + Final Multi-Symbol Upgrade

Date: 2026-07-04  
Entry point: `app.py`  
Delivery status: **deployment package built and locally verified**

## Added Field 10 order

1. Existing immutable whole-day ranking.
2. Persisted eight-session entry map.
3. Existing persisted sentiment/news/absorption ranking.
4. **Open / Close — Multi-Symbol Crowd Psychology Ranking**.
5. **Open / Close — Final Multi-Symbol Ranking**.
6. Existing histories, research, validation, and diagnostics.

The two new rankings are children of the existing canonical daily snapshot and reuse its run IDs, snapshot ID, broker day, completed H1 candle, universe hash, symbol/source identities, versions, and hashes. Field 10 rendering is read-only.

## Deploy

```bash
python scripts/migrate_field10_crowd_final_20260704.py \
  --database data/multi_symbol_field10_20260701.sqlite3 \
  --backup backups/multi_symbol_field10_20260701.pre_crowd_final_20260704_verified.sqlite3
streamlit run app.py
```

The included DB is already migrated, and the migration is idempotent.

## Verification commands used

```bash
python -m compileall -q app.py core ui tabs scripts tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_field10_crowd_final_20260704.py
```

All 42 test files were then executed in six reproducible batches listed in `TEST_REPORT.md` and the raw logs. Result: **367 passed, 0 failed**.

## Acceptance flow

Open Settings, connect available APIs, select symbols, run the existing calculation once, then open Lunch → Field 10. Missing optional data displays `UNAVAILABLE`; critical missing evidence produces `INSUFFICIENT_EVIDENCE`.

## Honest status and limitations

- Both new models remain **shadow-only**: `field10_crowd_psychology_candidate_v1` and `field10_final_multi_symbol_candidate_v1`.
- The supplied environment had no live retail-positioning, social-sentiment, or true institutional order-flow feed. Those values remain `UNAVAILABLE`; candle/tick-volume measures are labelled proxies.
- No production calibration, accuracy, or profitability claim is made.
- The migrated database has zero new crowd/final rows until the next qualifying Settings calculation; migration does not fabricate historical publications.
- Long-history promotion tests (purged/embargoed OOS calibration, Hansen SPA, CSCV/PBO, Deflated Sharpe Ratio, and structural-break stability) need more clean history and immutable outcomes than were supplied.
- The container provided Python 3.13.5, not 3.12. Changed files passed a Python-3.12 AST syntax check, and compile/import/Streamlit launch checks passed on 3.13.5. Installing 3.12 was blocked by the offline environment.

