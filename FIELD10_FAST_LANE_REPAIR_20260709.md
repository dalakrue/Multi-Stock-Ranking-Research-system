# Field 10 Fast-Lane Run Repair — 2026-07-09

## Goal
Reduce the calculation time of **Super Quick — Calculate All Loaded Symbols + Open Lunch** by making it a Field-10-first production path, while moving non-Field-10 Lunch/AI/Field 11/research burdens to **Quick — Calculate All Loaded Symbols + Open Lunch** or Full.

## What changed

### 1. Added a run-profile control module
New file: `core/field10_fast_lane_20260709.py`

It provides:
- `set_field10_fast_lane(...)`
- `is_field10_fast_lane(...)`
- `defer_to_quick(...)`
- `field10_fast_lane_summary(...)`

This keeps the Super Quick behavior explicit and auditable instead of hiding skipped work silently.

### 2. Settings button behavior
File: `tabs/antd_page_router_20260615.py`

- Super Quick now enables `FIELD10_FAST_LANE` when scope is `LUNCH_CORE`.
- Quick and Full disable the fast lane and continue to run heavier work.
- The one-click labels now describe the real split:
  - Super Quick = Field 10 production rank + minimum identity gates + Open Lunch
  - Quick = completes deferred Lunch/AI/Field 11 work + Field 10 refresh

### 3. Single-symbol Settings orchestrator
File: `core/settings_run_orchestrator_20260617.py`

When the fast lane is enabled:
- Full Power BI projection is deferred.
- The child publisher still builds the minimum real-candle Field 2 identity bundle needed by Field 10.
- NLP/research/data-mining pack is deferred to Quick/Full.
- Reliability/regime inner-cache builds are deferred to Quick/Full.
- Institutional quant shadow layer is deferred to Quick/Full.
- The run status is marked as `FIELD10_FAST_LANE_MINIMUM_GATES` instead of ordinary Lunch Fields 1–3.

### 4. Multi-symbol Field 10 engine
File: `core/multi_symbol_field10_20260701.py`

When the fast lane is enabled:
- Field 10 production publication remains active.
- Minimum Field 1/2/3 identity gates remain active so Field 10 child snapshots stay trustworthy.
- Per-symbol shadow research candidate evaluation is deferred.
- Field 11 similar-path index and outcome settlement are deferred.
- The manifest records `run_profile = FIELD10_FAST_LANE` and lists deferred work.
- Resource rows show `Field 10 + minimum Fields 1-3 gates` instead of implying Fields 10–11 were fully run.

## What did not change
- Existing production Field 10 formulas were not deleted.
- Existing ranking/database publication logic was not removed.
- Quick and Full remain available for heavier Lunch/AI/Field 11/research completion.
- Deferred items are recorded, not silently ignored.

## Validation performed
- Python compile check passed for:
  - `core/field10_fast_lane_20260709.py`
  - `tabs/antd_page_router_20260615.py`
  - `core/multi_symbol_field10_20260701.py`
  - `core/settings_run_orchestrator_20260617.py`
- Fast-lane helper smoke test passed.

## Test note
A broader pytest run could not be fully used in this sandbox because this environment does not have Streamlit installed, and one existing deployment test also failed on pre-existing selector UI expectations unrelated to this fast-lane repair.
