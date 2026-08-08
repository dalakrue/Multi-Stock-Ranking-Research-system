# ADX Quant Pro — API Connection and Three-Selector Repair Report

Date: 2026-07-08
Base project: `ADX_Quant_Pro_Market_Connection_Recovery_20260708`

## 1. Root cause

The one-click connection path crashed before a valid provider request because `core/app/refresh.py` selected the previous canonical object with Python Boolean short-circuiting:

```python
state.get("canonical_result_20260617") or state.get("canonical_result")
```

When the first object was a non-empty pandas DataFrame, Python attempted `bool(dataframe)` and raised:

`ValueError: The truth value of a DataFrame is ambiguous.`

The repaired path uses explicit `is not None`, DataFrame type checks, and `.empty` checks. The same audit was applied to connection provenance, cached frames, selector state, adapter tuple success metadata, local recovery, and deferred cache restoration.

A second root cause was normalized selector persistence: Selector 1 displayed a 12-symbol limit, but `replace_current_selections()` still truncated every selector to 6. The normalized schema and write path now preserve 12 / 6 / 6 exactly.

A third root cause was result loss: the load manager discarded failed per-symbol payloads after each batch. This removed provider attempts and precise failure categories, weakening diagnostics and causing “Reload Failed Symbols” to rely on incomplete state. All currently selected per-symbol results are now retained, while calculations still activate only validated symbols.

## 2. Files changed

- `core/app/refresh.py`
- `core/complete_repair_20260705.py`
- `core/connector_state_machine_20260621.py`
- `core/data/market_data_orchestrator.py`
- `core/multi_symbol_load_manager_20260707.py`
- `core/normalized_multi_symbol_migration_20260707.py`
- `ui/multi_symbol_settings_20260701.py`
- `ui/provider_health_panel_20260705.py`
- `ui/sidebar_fallback_panel.py`
- `tests/test_api_selector_connection_repair_20260708.py` (new, 24 tests)
- `tests/test_market_data_recovery_20260708.py` (updated to required provider route)
- `tests/test_deployment_readiness_upgrade_20260705.py` (updated to required provider route)

No existing user database/history file is included as a modified repair artifact. Test/startup-generated database changes were reverted before packaging.

## 3. Provider fallback repair

The real candle route and the Settings labels now use the same immutable order:

1. `FINNHUB`
2. `TWELVE_DATA`
3. `MT5`
4. `ALPHA_VANTAGE`
5. `LOCAL_VALID_CACHE`

Legacy connector-mode values no longer silently reorder this route. Yahoo Finance code remains dormant for backward compatibility but is not registered in, or reachable through, the production fallback chain.

Each symbol is resolved independently. A Finnhub candle restriction, empty response, malformed result, rate limit, unsupported symbol/timeframe, or temporary error continues to Twelve Data and then the remaining providers. A fallback success is not converted to a global connection error.

Connection outcomes now support:

- `CONNECTED`
- `CONNECTED_WITH_FALLBACK`
- `PARTIAL`
- `ERROR`

Settings records and displays:

- Preferred provider
- Actual candle provider
- Finnhub candle-attempt result
- Fallback reason
- Per-provider attempt category
- Actual validated row count

A cache reuse is reported as `VALIDATED_LOCAL_CACHE_REUSED`, not falsely described as a failed Finnhub request.

## 4. Selector isolation repair

All three selectors retain dedicated:

- Widget keys
- Selection state keys
- Pending/reload state keys
- Load button keys
- Retry button keys
- Load records
- Validation records
- Provider results

Capacities are enforced consistently in the UI, session state, normalized persistence, and loader:

- Selector 1: 12
- Selector 2: 6
- Selector 3: 6

The visible selection is authoritative. Deselected symbols are not loaded, stale presets do not overwrite visible selections, order is preserved, a failure does not stop later symbols, and one selector does not overwrite another.

## 5. Symbol and timeframe mapping

Central provider-specific symbol mapping remains inside `MarketDataOrchestrator.provider_symbol()`.

Examples:

- Canonical `EURUSD`
- Finnhub `OANDA:EUR_USD`
- Twelve Data `EUR/USD`
- MT5 `EURUSD`
- Alpha Vantage `EURUSD`

The canonical symbol is retained in state and persistence.

Central H4 interval mapping is now explicit:

- Finnhub: `60`, causally aggregated from genuine H1 candles to H4
- Twelve Data: `1h`, causally aggregated from genuine H1 candles to H4
- MT5: `H4`
- Alpha Vantage: `60min`
- Local cache: `H4`

The provider interval, requested timeframe, and requested row count are recorded in provider attempts.

## 6. Validation, cache, and database repair

Validated candles require:

- A non-empty DataFrame
- Parseable timestamps or a DatetimeIndex
- OHLC columns
- Numeric OHLC values
- Valid OHLC relationships
- Sorted, deduplicated timestamps
- Exact canonical symbol and timeframe identity
- Completed-candle spacing consistent with the requested timeframe

Volume is nullable for forex feeds and is never used to fabricate OHLC values.

The genuine history target remains 600. The existing defensible adaptive calculation minimum remains 100 genuine selected-timeframe candles, so valid 597/600 or other above-minimum histories are accepted and clearly marked as adaptive rather than rejected or padded.

Cache reuse uses explicit DataFrame checks. Empty cached DataFrames do not block fresh provider requests. Persistence remains exact-symbol/exact-timeframe and occurs only after validation. Existing history is preserved.

## 7. Status and retry repair

Each selector status row now provides:

- Order
- Symbol
- Status
- Genuine Rows
- Timeframe
- Preferred Provider
- Actual Provider
- Provider Symbol
- Latest Completed Candle
- Failure Category
- Failure Reason
- Attempt Count
- Load Duration
- Persisted
- Validation State

Public load summaries are mathematically consistent:

`Selected = Loaded & Valid + Rejected / Failed`

Public load status is `COMPLETED`, `PARTIAL`, or `FAILED`.

“Reload Failed Symbols” retries only the latest allowed failure categories:

- `FAILED`
- `RATE_LIMITED`
- `EMPTY`
- `INVALID_DATA`
- `PROVIDER_UNAVAILABLE`
- `TEMPORARY_ERROR`

Successful symbols are preserved and not re-fetched by a failed-only retry.

## 8. Verification performed

- Repair and legacy integration test selection: **97 passed**
- New task-specific regression file: **24 passed**
- Python compilation: **passed** for `app.py`, `core`, `ui`, `tabs`, `scripts`, and `tests`
- Changed-module import smoke test: **passed**
- Headless Streamlit startup: **passed**; server reached a local URL with no traceback, import error, syntax error, duplicate-widget error, or ambiguous DataFrame truth-value error in the startup log
- Critical connection/cache-path unsafe Boolean pattern scan: **0 findings**
- Three-selector key-isolation regression: **passed**
- Full repository collection: **606 tests collected**. A monolithic historical-suite run exceeded the execution window after progressing through roughly the first quarter; no claim is made that all 606 completed in this environment.

## 9. Manual/live acceptance status and external limitations

The exact live-account acceptance workflow could not be completed in this environment because the upload contains only `secrets.example.toml`, not usable Finnhub/Twelve Data credentials, and there is no authenticated browser session connected to the user’s deployed Streamlit instance.

Therefore this delivery does **not** claim that Finnhub candle entitlement or current free-plan rate limits were live-verified. The repaired code treats those outcomes correctly and the deterministic provider/selector simulations pass, but the user should perform the final live sequence in Settings with their saved secrets.

External limitations that remain outside the repository:

- Finnhub credential validity does not guarantee candle entitlement.
- Free-plan endpoint availability and rate limits can change.
- MT5 requires an available compatible terminal/bridge.
- Alpha Vantage intraday FX availability depends on account plan and current service policy.
- A provider may return fewer than 600 genuine candles; the app records the genuine count and never duplicates rows.
