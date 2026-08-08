# Test Report

## Automated tests

Command scope: Field 10 contracts, daily snapshot contract, evidence heatmap, integrated history, multi-symbol runner, shadow methods, Field 1 Table 4 publication bridge, ten-paper research layer, Field 3/Field 10 synchronization, and the new rank-column migration tests.

Result: **87 passed, 0 failed**.

Six scikit-learn warnings were emitted by an existing single-label confusion-matrix fixture. They do not indicate a failed calculation or migration.

## Static/compile validation

- `python -m compileall -q core ui tests`: PASS
- Duplicate rank headings absent: PASS
- One authoritative Today First rank heading: PASS
- Top Lunch connector reused by Field 10: PASS

## Application smoke test

`streamlit run app.py --server.headless true` started successfully and served the application. The process was intentionally stopped by the smoke-test timeout after startup.

## Database checks

- Unified migration: PASS
- SQLite `PRAGMA integrity_check`: ok
- SQLite `PRAGMA foreign_key_check`: zero issues
