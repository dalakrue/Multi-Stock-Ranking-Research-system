# Instant Run Engine — 2026-07-05

## What was repaired

The Settings calculation buttons now use a durable cooperative Streamlit job engine instead of executing the complete multi-symbol transaction directly inside the click event.

- The first click immediately creates a unique queued job and reruns the page.
- The next Streamlit pass claims and executes that job through the existing protected calculation stack.
- Duplicate clicks are blocked only while the same job is queued or running.
- Repeating the same symbols and scope creates a new job ID, so an old completed one-click transaction cannot be returned as though it were a new calculation.
- Provider preparation and each symbol publish live progress to the visible table.
- Completed, partial, and failed outcomes remain visible instead of ending with a blank page.
- A stale RUNNING job can recover after an interrupted server pass.
- Authenticated accounts receive a stable per-login journal; anonymous sessions receive isolated random journals.
- Secrets and credentials are excluded from the persisted job summary.

## Streamlit safety

The engine deliberately does not mutate `st.session_state` from a Python background thread. Streamlit session state and UI APIs are not thread-safe. The implementation uses a queued rerun/state-machine pattern, which gives immediate click acknowledgement while keeping the existing calculation and canonical publication transaction safe.

## API and multi-symbol reliability

- Every selected symbol is isolated with `try/except` at the scheduler boundary.
- An unexpected provider or normalization failure reuses validated local candles when available.
- A failed symbol no longer aborts all remaining symbols.
- Twelve Data waits are bounded and scope-aware:
  - Super Quick (`LUNCH_CORE`): one attempt
  - Quick: up to two attempts
  - Full: up to three attempts
- Finnhub and Alpha Vantage request timeouts are bounded.
- Provider timeout defaults may be configured with:
  - `TWELVE_DATA_TIMEOUT_SECONDS` (default 8)
  - `FINNHUB_TIMEOUT_SECONDS` (default 8)
  - `ALPHA_VANTAGE_TIMEOUT_SECONDS` (default 10)
- Existing provider fallback order and canonical calculation logic are preserved.

## Important scope correction

The direct Super Quick service previously set and executed scope `QUICK`. It now correctly uses `LUNCH_CORE` for all selected symbols.

## Modified files

- `tabs/antd_page_router_20260615.py`
- `core/instant_run_engine_20260705.py` (new)
- `core/calculation/run_orchestrator.py`
- `core/data/multi_symbol_scheduler.py`
- `core/data/market_data_orchestrator.py`
- `core/connectors/data_parts/fetchers.py`
- `core/super_quick_service_20260704.py`
- `tests/test_instant_run_engine_20260705.py` (new)

## Validation performed

- Python compilation completed for `core`, `tabs`, `ui`, `app.py`, and `adx_dashpoard.py`.
- 40 focused instant-engine, deployment-readiness, connector, routing, and Field 10 tests passed.
- The broader test collection could not be completed in this execution environment because the Streamlit package is not installed; four unrelated UI test modules fail during import for that reason.
