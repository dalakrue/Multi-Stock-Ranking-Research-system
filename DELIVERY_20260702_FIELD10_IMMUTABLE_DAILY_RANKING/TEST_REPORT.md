# Test Report

## Final Results

| Verification | Result |
|---|---|
| Full repository pytest | **271 passed, 9 warnings in 28.88 s** |
| New immutable-daily contract suite | **33 passed in 0.55 s** |
| Python compileall | **PASS** |
| Streamlit process startup | **PASS** |
| Streamlit health endpoint | **`ok`** |
| Streamlit Cloud import preflight | **PASS** |
| Fresh SQLite migration | **PASS** |
| Existing SQLite migration | **PASS; legacy row preserved** |

The nine warnings are scikit-learn single-label confusion-matrix warnings in existing Field 10/routing tests. They are warnings, not test failures.

## Raw Evidence

- `RAW_EVIDENCE/FULL_PYTEST_RAW.txt`
- `RAW_EVIDENCE/ACCEPTANCE_PYTEST_RAW.txt`
- `RAW_EVIDENCE/COMPILEALL_RAW.txt`
- `RAW_EVIDENCE/STREAMLIT_STARTUP_RAW.txt`
- `RAW_EVIDENCE/STREAMLIT_PREFLIGHT_RAW.txt`
- `RAW_EVIDENCE/DATABASE_MIGRATION_RAW.json`
- `RAW_EVIDENCE/PERFORMANCE_BENCHMARK_RAW.json`

## Tested Environment

- Test interpreter: Python 3.13.5 in the available container.
- Project deployment target: `runtime.txt` specifies Python 3.12.
- Exact Python 3.12 execution was not available in this container; this is recorded under incomplete items.
