# Foreground Symbol Router Repair Report — 2026-07-08

## Changed files

- `core/data/symbol_level_provider_registry_20260708.py` — new symbol/timeframe/provider health registry with live states, circuit breaker, score persistence, and frontend health-board data.
- `core/data/market_data_orchestrator.py` — added foreground provider ledger, provider-health scoring after each symbol request, circuit-breaker bypass, explicit failure states, and last-valid-cache degradation publication.
- `core/data/deployment_migrations_20260705.py` — added legacy-safe `schema_migrations` repair, fixed duplicate macro observation column, and added router tables/indexes.
- `core/data/candle_repository.py` — added accepted-candle-by-provider persistence with unique symbol/timeframe/candle_time/provider key.
- `core/multi_symbol_load_manager_20260707.py` — expanded canonical load status board with requested columns, final-state names, provider trace, coverage, and explicit failure reason.
- `ui/multi_symbol_settings_20260701.py` — added `Foreground Symbol Loading Control Center`, visible canonical universe, clear state, and provider trace CSV export.
- `ui/provider_health_panel_20260705.py` — updated provider policy wording and added Symbol-Level Provider Health Board.
- `tabs/antd_page_router_20260615.py` — added `Main Provider Choice`, API Source Connector Panel wording, FCS candle validation labels, and Twelve fallback connector controls.
- `ui/lunch_field10_multi_symbol_20260701.py` — added Field 10 load contract columns so all selected symbols can show provider/final-state/failure evidence.
- `tests/test_foreground_symbol_router_20260708.py` — new focused tests for foreground routing, fallback/cache behavior, circuit breaker, and Field 10 status publication.

## Architecture summary

The foreground loader now uses one canonical 12-symbol universe collected from the three selectors. The selectors remain UI inputs only; loading/ranking uses the single canonical state contract:

- `st.session_state["canonical_selected_symbols"]`
- `st.session_state["canonical_loaded_symbols"]`
- `st.session_state["canonical_symbol_load_status"]`
- `st.session_state["canonical_symbol_candles"]`
- `st.session_state["canonical_provider_trace"]`
- `st.session_state["canonical_ranking_timeframe"]`

The new provider registry stores health by provider/symbol/timeframe and supports live states such as `HEALTHY`, `RATE_LIMITED`, `AUTH_FAILED`, `EMPTY_DATA`, `TIMEOUT`, `STALE_CACHE_ONLY`, and `DISABLED`.

## Provider routing flow

1. Use exact local database/cache first when symbol/timeframe/freshness/row-count validation passes.
2. Try FCS API as the first live candle provider unless FCS is hard-disabled or circuit-open.
3. Try Twelve Data as fallback, respecting the existing quota manager and pending queue behavior.
4. Use last-known valid cache as `DEGRADED_VALID_CACHE` when live providers fail.
5. Publish `FAILED_EXPLICIT` with exact failure reason when no source can provide valid candles.

## Frontend behavior

Settings now exposes a `Foreground Symbol Loading Control Center` plus an `API Source Connector Panel` with `Main Provider Choice` options:

- `AUTO_SYMBOL_ROUTER`
- `FCS_API_MAIN`
- `TWELVE_DATA_FALLBACK`

The load board now shows requested timeframe, local cache result, FCS result, Twelve result, last cache result, actual provider used, candle count, completed candle time, coverage ratio, data quality grade, final state, provider trace, and explicit failure reason. Field 10 now receives all selected symbols, including failed or degraded rows.

## Validation results

- `python -m compileall .` — passed.
- Focused foreground router tests — `7 passed`.
- Full `pytest -q` — could not complete because this container does not have `streamlit` installed; collection stopped on UI tests importing Streamlit.
- `streamlit run app.py` — could not execute in this container because the `streamlit` command is not installed.

## Remaining limitations

- Live API calls were not executed because no real FCS/Twelve Data keys were available in the sandbox.
- Streamlit runtime smoke test requires installing the app requirements in the target environment.
- Twelve Data quota waiting remains bounded by the existing quota-manager mechanics; the UI now publishes pending/rate-limit states rather than freezing or silently dropping symbols.
