# Test Report

## Automated suite

Command scope:

- Deployment/runtime guards
- Field 10 daily snapshot contract
- Multi-symbol orchestration and state isolation
- Field 11 multi-symbol simulator
- Field 3 lifecycle monitor
- Multi-symbol API request deduplication
- User-priority repair acceptance
- Multi-symbol routing

Result: **99 passed, 0 failed**.

Warnings: 9 scikit-learn single-label confusion-matrix warnings from existing synthetic test samples. These did not cause failures.

A minimal test-only Streamlit session-state shim was used because Streamlit is not installed in the execution sandbox. The project itself correctly declares `streamlit>=1.35,<2` in `requirements.txt`; no shim was added to production code.

## Eight-symbol Field 10 validation

Symbols:

- EURUSD
- GBPUSD
- USDJPY
- USDCHF
- USDCAD
- AUDUSD
- NZDUSD
- EURJPY

Results:

- 8 selected symbols produced 8 visible rows.
- Every row received comparative Rank 1–8.
- All required priority columns were present.
- Blank required cells: 0.
- Generic `N/A` or `UNAVAILABLE` in the visible table: 0.
- Immutable source modified: false.
- All 14 advanced metric columns varied across the symbol set in this validation.
- Higher-standard, stable-daily, and less-risky biases were populated from each symbol's own evidence.

Evidence files:

- `FIELD10_SYNTHETIC_VALIDATION_20260702.json`
- `FIELD10_SYNTHETIC_VALIDATION_TABLE_20260702.csv`

## Static validation

- Changed Python files compiled successfully.
- Obsolete secondary-scope strings were removed from the repaired run path.
- Test-generated databases, caches, and indexes were removed before packaging; the user's original persisted `data/` directory was restored.

## Not executed in this sandbox

- Live MT5 terminal login and candle download
- Live Twelve Data/Finnhub calls with user credentials
- Browser-driven Streamlit click automation
- Streamlit Cloud deployment

Those items remain deployment-environment verification, not claimed as live PASS here.
