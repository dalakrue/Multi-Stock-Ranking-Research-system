# Test Report

Date: 2026-07-06 (Asia/Yangon)

## Automated Python suite

The complete project test suite was run in two deterministic batches to avoid the execution environment's single-command timeout:

- Batch 1: **324 passed**
- Batch 2: **176 passed**
- Total: **500 passed, 0 failed**
- Warnings: **3** existing scikit-learn single-label confusion-matrix warnings

Additional protected-hash verification rerun:

- **4 passed**, 18 deselected

Compilation:

- `python -m compileall` for `app.py`, `core`, `ui`, `lunch`, `scripts`, and `tests`: **passed**

## Required 20-case repair suite

`tests/test_complete_h4_child_publication_20260706.py` contains the requested twenty cases. Result: **20 passed**.

Coverage includes:

1. Top 10 currency symbols with H4.
2. One-run deterministic Super Quick publication workflow.
3. All ten symbols reach COMPLETED with sufficient fixtures.
4. H4 higher window = 150.
5. H1 higher window = 600.
6. Field 1 explicit load changes identity/history.
7. Field 2 explicit load changes its Power BI bundle.
8. Settings main symbol remains unchanged.
9. Switching is read-only and does not call an API/heavy runner.
10. Form-based selector avoids post-widget session-state mutation.
11. Distinct child IDs, hashes and source IDs.
12. Field 10 Time/Timeframe columns.
13. Four-hour spacing and bar/hour duration semantics.
14. No cross-symbol source borrowing.
15. Complete Field 2 run/generation/hash/candle identity.
16. Session clear and SQLite reload for all ten.
17. 100% processing with one failed validation remains PARTIAL.
18. Actual Field 1 rows only; no generated blank rows.
19. Controlled float/missing-value formatting.
20. Shadow research cannot publish a production decision.

## Deterministic ten-symbol H4 acceptance

Script: `scripts/run_h4_acceptance_20260706.py`

Result: **PASSED** in deterministic offline mode.

Verified:

- 10/10 completed child snapshots
- 150 required H4 candles
- valid 4-hour spacing
- 10 distinct child snapshot hashes
- 10 distinct exact-symbol source IDs
- 10 Field 2 bundles
- Field 1 load to USDJPY
- Field 2 load to AUDUSD
- all display authorities agree after load
- Settings main symbol remains EURUSD
- all ten reload after an empty session state
- SQLite integrity is `ok`

Evidence: `test_artifacts/h4_acceptance_20260706/h4_acceptance_result.json`.

## Streamlit startup smoke test

Command-equivalent startup: `streamlit run app.py --server.headless true`.

- health endpoint: **ok**
- startup log: Uvicorn/Streamlit server started successfully
- main entry point: **app.py**

## Limits of this environment

No live API credentials were used. Therefore, the deterministic acceptance proves orchestration, validation, persistence, isolation and reload behavior, but it is not evidence that a particular live provider currently supplies 150 H4 candles for each symbol.

An attempted Chromium test at an iPhone-width viewport was blocked by the container administrator policy (`ERR_BLOCKED_BY_ADMINISTRATOR`) before the browser could access localhost. Static mobile tests, dynamic-row tests and Streamlit health passed, but a true pixel-level browser acceptance must be rerun in Streamlit Cloud or a local browser.

Overall live-provider acceptance is therefore **not claimed** in this report.

---

## 2026-07-07 repair regression

- Focused new API/selector/publication tests: **7 passed**.
- Combined relevant provider, selector, multi-symbol, Field 1/3/10 publication and ten-symbol acceptance regression: **112 passed, 0 failed**.
- Added deterministic H1 case: **597/600 genuine H1 candles**, exact USDCAD identity, local three-standard Field 3 sidecar, cache serialization, immutable publication and reload validation all pass.
- Streamlit startup: `streamlit run app.py --server.headless=true --server.port=8765` started successfully; the timeout intentionally stopped the smoke server after startup.
- Live API credentials were not used.
