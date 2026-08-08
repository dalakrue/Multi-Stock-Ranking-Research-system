# Verification Report

## Final verification

- Python source compilation: **PASS** (`python -m compileall -q .`)
- Total collected project tests: **302**
- Passing tests: **302**
- Failing tests: **0**
- New targeted repair tests: **7/7 PASS**
- Core Field 10 + Field 11 regression set: **70/70 PASS**
- Expanded multi-symbol/acceptance set: **127/127 PASS**

The complete test collection was executed in deterministic file groups because one monolithic CI process exceeded the container's execution window. Every collected test file passed when run in those groups.

## Coverage areas verified

- Ordered multi-symbol selector and removal of legacy single-symbol UI.
- First selection as Main Core Symbol.
- Non-EURUSD routing and Field 3 publishing.
- Field 10 daily publication and immutable history contract.
- Independent adaptive metrics and column variability.
- Field 3 Higher Standard Bias propagation.
- Power BI non-EURUSD fallback generation.
- Field 11 historical-index identity and simulation.
- Broker/session time synchronization.
- API request deduplication.
- Post-run navigation and closed-first field behavior.
- Deployment entry point, Python runtime declarations and serializer fallback.
- Protected-file invariants and canonical identity consistency.

## Non-failing warnings

Several sklearn tests emit a warning that a synthetic test fixture contains only one class. This is a known test-data warning and did not cause any failed assertions.

## Commands used

```bash
python -m compileall -q .
PYTHONPATH=. pytest -q tests/test_full_multi_symbol_repair_20260702.py
PYTHONPATH=. pytest -q tests/test_field10_daily_snapshot_contract_20260702.py tests/test_field11_similar_path_simulator_20260702.py tests/test_field10_multi_symbol_20260701.py
```

The remaining files were run in three stable pytest groups; their combined count plus the research-quant tests equals all 302 collected tests.
