# Test Report — 2026-07-02

## Passed

### Full Python syntax compilation

Command:

```powershell
python -m compileall -q .
```

Result: **PASS** across the complete project tree.

### Focused multi-symbol, Field 3 and Field 10 regression suite

Command:

```powershell
$env:PYTHONPATH = (Get-Location).Path
pytest -q tests/test_field10_multi_symbol_20260701.py tests/test_field3_regime_lifecycle_monitor_20260701.py tests/test_multi_symbol_routing_20260702.py --disable-warnings --maxfail=3
```

Result: **24 passed**, 9 warnings.

The suite verifies:

- Required supported symbols and provider aliases.
- More than 2,000 candles.
- Duplicate and missing-candle detection.
- Daily Higher-standard lock behavior and 23:00 review.
- Best-score-first ranking.
- Multi-symbol cache isolation.
- Main symbol runs requested scope first.
- Secondary symbols run `LUNCH_CORE` only.
- Field validation for secondary symbols is limited to Fields 1–3.
- Main symbol is restored after the batch.
- Lunch display symbol is separated from the main symbol.
- Scope matrix is correctly published.
- Top Lunch selector precedes copy controls.
- Duplicate Field 10 symbol selector is absent.
- Field 10 scope, allocation, filters and downloads are wired.
- Field 1 Table 5 filters, views, charts and download are wired.
- Connector reuse and forced refresh are wired.
- Credential/endpoint rotation changes the transient connection fingerprint.
- A non-EURUSD main symbol (`GBPJPY`) produces an available Field 3 payload and populated history.

### Deployment guard and routing tests

Command:

```powershell
$env:PYTHONPATH = (Get-Location).Path
pytest -q tests/test_deployment_runtime_guards_20260702.py tests/test_multi_symbol_routing_20260702.py --disable-warnings --maxfail=3
```

Result: **9 passed**.


### Final clean-package combined regression

Command:

```powershell
$env:PYTHONPATH = (Get-Location).Path
pytest -q tests/test_field10_multi_symbol_20260701.py tests/test_field3_regime_lifecycle_monitor_20260701.py tests/test_multi_symbol_routing_20260702.py tests/test_deployment_runtime_guards_20260702.py --disable-warnings --maxfail=3
```

Result: **31 passed**, 9 warnings.

## Full-suite environment limitation

The container used for this repair does not have the `streamlit` package installed. Running all 26 test files therefore stops during collection for UI modules that import Streamlit. This is an environment dependency failure, not a Python syntax failure in the modified code. The project `requirements.txt` already specifies `streamlit>=1.35,<2` for deployment.

A broad run excluding three collection-blocked files reached **120 passed** before stopping at eight failures; seven were additional missing-Streamlit imports, and one was an old exact-label assertion. The label compatibility failure was fixed and its deployment guard now passes.

## Recommended deployment smoke test

After installing `requirements.txt` in the real deployment environment:

```powershell
python -m pip install -r requirements.txt
$env:PYTHONPATH = (Get-Location).Path
pytest -q tests --disable-warnings --maxfail=1
streamlit run app.py
```

Then verify manually:

1. Connect Once does not download again on a second identical click.
2. Refresh Main Feed does download again.
3. Choose GBPJPY as main and EURUSD/XAUUSD as secondary.
4. Run Quick.
5. Confirm Field 10 scope matrix shows GBPJPY Fields 1–9 + AI and secondaries Fields 1–3 + Field 10.
6. Switch Lunch symbol and confirm Fields 1–3 change.
7. Open a non-Lunch page and confirm main-symbol identity is restored.
8. Export Field 1 Table 5 and Field 10 CSV files.
