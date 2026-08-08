# Canonical 12-Symbol Loader Repair — 2026-07-08

## Goal delivered
The three Settings multi-symbol selectors now feed one authoritative, deduplicated canonical ranking universe capped at 12 symbols. Selector 1, Selector 2, and Selector 3 are no longer loaded as separate state-owned engines for the main ranking path.

## Main architecture changes
- Added `CANONICAL` load group and canonical state keys:
  - `st.session_state["canonical_selected_symbols"]`
  - `st.session_state["canonical_loaded_symbols"]`
  - `st.session_state["canonical_symbol_load_record_20260708"]`
- Added `canonical_universe_from_groups(...)`, `publish_canonical_universe(...)`, `load_canonical_market_data(...)`, and `loaded_canonical_status(...)`.
- Canonical universe preserves selected order, deduplicates symbols, and limits total ranking symbols to 12.
- Old selector-specific load/retry buttons were removed from the visible Settings UI. The old records remain only as compatibility/audit data.

## Provider order
Default provider route is now:
1. Fresh local database/cache check inside the orchestrator
2. `FCS_API_MAIN`
3. `TWELVE_DATA_FALLBACK`
4. `LOCAL_VALID_CACHE` / last-known valid exact-symbol cache

The API Source selector can still move Twelve Data to first position by choosing `twelve`. Finnhub is not in the active candle-provider priority and remains optional for news/sentiment/confirmation only.

## FCS connector
- Settings includes FCS API Connector.
- Normal FCS requests use only `access_key`.
- Public key remains optional and hidden under Advanced.
- FCS key can auto-resolve from Streamlit Secrets/env/session through `resolve_api_key("fcs_api", st.session_state)`.
- Connection test shows status, last successful request time, response time, and symbol-list availability.

## Loading behavior
- One main Settings button: `Load Selected Data for 12-Symbol Ranking`.
- Loading is queue-based symbol-by-symbol through the existing scheduler/orchestrator path.
- Already-loaded symbols are kept even if later symbols fail.
- Per-symbol status table shows provider, candle count, latest candle time, freshness, quality, and failure reason.
- Canonical loading accepts emergency exact-symbol history as low as 25 candles and marks quality instead of showing “Insufficient local history”.

## Field 10 changes
Field 10 now renders one row for every canonical selected symbol, up to 12. It uses exact-symbol load evidence only and does not borrow data from another symbol.

Required columns added/normalized:
- Symbol
- Timeframe
- Data Provider Used
- Candle Count
- Latest Candle Time
- Data Freshness
- Data Quality Grade
- Load Status
- Rank Score
- Decision
- Reason

## Validation performed
- Python syntax compilation passed for all changed files.
- Targeted test set passed: 31 passed.
- A manual canonical-loader simulation loaded 12 selected symbols and produced statuses: FCS_SUCCESS, TWELVE_SUCCESS, and USING_CACHE.

## Known legacy-test note
`tests/test_provider_selector_capacity_20260708.py` still contains old expectations that Finnhub is the active candle provider. Those two legacy assertions intentionally conflict with the new user requirement: “Do not use Finnhub as the main candle provider.”
