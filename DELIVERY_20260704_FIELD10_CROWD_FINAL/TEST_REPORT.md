# Test Report

## Final result

- 42/42 test files executed
- **367 passed**
- **0 failed**
- New crowd/final suite: 38 passed
- 3 legacy single-class sklearn warnings; no failures

| Batch | Files | Passed |
|---|---:|---:|
| Existing files 1–10 | 10 | 93 |
| Field 10 contracts + new suite | 2 | 53 |
| Field 10 files 13–20 | 8 | 67 |
| Research/Field 11/Field 1 files 21–25 | 5 | 53 |
| Field 1/3/navigation files 26–30 | 5 | 28 |
| Remaining files 31–42 | 12 | 73 |
| **Total** | **42** | **367** |

Additional PASS checks: compileall, changed-module imports, Streamlit health endpoint, actual migration, repeated migration, SQLite integrity/FK checks, and 7/7 Python-3.12 syntax parses.

The environment only had Python 3.13.5. Actual Python 3.12 execution remains incomplete because offline installation failed; `.python-version` and `runtime.txt` still declare 3.12.

Third-party pytest telemetry plugins occasionally held aggregate processes open after a 100% pass summary. Reproducible batch commands used `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; no test was skipped or hidden. Logs are in `RAW_EVIDENCE/`.

## Extracted ZIP validation

A clean extraction of the deployment ZIP passed compileall, idempotent migration, 38/38 new acceptance tests, changed-module imports, all 12 required report checks, and the Streamlit health endpoint. See `RAW_EVIDENCE/ZIP_EXTRACTION_VALIDATION.txt`.
