# Complete Test Report

## Compilation

```powershell
python -m compileall -q .
```

Result: PASS (no output, exit code 0).

## Required baseline suite before changes

```powershell
$env:PYTHONPATH = (Get-Location).Path
pytest -q `
  tests/test_field10_multi_symbol_20260701.py `
  tests/test_field10_ten_paper_research_20260701.py `
  tests/test_multi_symbol_routing_20260702.py `
  tests/test_field3_regime_lifecycle_monitor_20260701.py `
  tests/test_deployment_runtime_guards_20260702.py `
  --disable-warnings --maxfail=1
```

Result: **39 passed, 9 warnings, 13.88 s**.

## Same required suite after implementation

Result: **39 passed, 9 warnings, 13.32 s**.

## Required suite plus six dedicated feature suites

```powershell
pytest -q `
  tests/test_field10_multi_symbol_20260701.py `
  tests/test_field10_ten_paper_research_20260701.py `
  tests/test_multi_symbol_routing_20260702.py `
  tests/test_field3_regime_lifecycle_monitor_20260701.py `
  tests/test_deployment_runtime_guards_20260702.py `
  tests/test_field1_table5_quant_enrichment.py `
  tests/test_field10_table4_publication_bridge.py `
  tests/test_field10_integrated_evidence_history.py `
  tests/test_field10_evidence_heatmap.py `
  tests/test_secondary_symbol_shared_sentiment.py `
  tests/test_multi_symbol_api_request_deduplication.py `
  --disable-warnings --maxfail=1
```

Result: **51 passed, 9 warnings, 13.74 s**.

## Full repository suite

```text
PYTHONPATH=<temporary test-only streamlit shim>:$PWD pytest -q --disable-warnings --maxfail=1
```

Result: **218 passed, 9 warnings, 23.85 s**.

The shim was needed only because Streamlit was absent from this runner. It was created under `/tmp` and is not included in the delivered project or ZIP.

## Clean staged-delivery validation

The exact staged directory used to build the ZIP was compiled and reran the 51-test required + dedicated suite.

Result: **51 passed, 9 warnings, 15.90 s**.
