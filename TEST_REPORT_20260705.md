# Test Report — ADX Quant Pro Repair (2026-07-05)

## Automated result
- Pytest files: **44**
- Tests passed: **397**
- Tests failed: **0**
- Warnings: **3** (scikit-learn single-class confusion-matrix warnings in one synthetic routing test; no application exception)
- Python compileall: **PASS**
- Streamlit AppTest: **PASS — 0 rendered exceptions**
- Streamlit headless startup: **PASS — server started and stopped cleanly**
- SQLite main integrity: **PASS**
- SQLite Field 11 integrity: **PASS**

## Covered repair scenarios
The automated suite covers canonical publication, partial-run protection, multi-symbol routing, provider request deduplication, Field 1/2/3/11 selector contracts, Field 10 ranking/schema/history/evidence, Field 11 simulator and timeframe-safe resampling, M1/H1/H4/D1 contracts, refresh/copy/AI context, database migration/idempotency, stale-cache prevention, automatic Field 10 navigation, mobile/desktop rendering contracts and startup/deployment guards.

## Environment-limited checks
- Live Twelve Data and Finnhub requests were not executed because this isolated repair environment has no user API secrets and no dependable external network access. Provider priority, retries, failover, redaction and mocked/offline fallback paths were tested.
- Physical iPhone browser testing was not available. Responsive mobile layouts were validated through source/UI contract tests and Streamlit AppTest, not device automation.
- No claim is made that a new statistical model is profitable. Existing research engines remain gated by chronological validation, calibration, coverage, drift and out-of-sample evidence.

## Logs
- `reports/test_logs/batch1.txt`: 190 passed
- `reports/test_logs/batch2.txt`: 121 passed
- `reports/test_logs/batch3.txt`: 86 passed, 3 warnings
- `reports/test_logs/streamlit_apptest.txt`: zero exceptions
- `reports/test_logs/streamlit_smoke.txt`: headless server startup
