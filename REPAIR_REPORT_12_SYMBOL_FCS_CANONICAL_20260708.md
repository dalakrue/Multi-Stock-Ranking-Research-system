# 12-Symbol FCS Canonical Provider Repair — 2026-07-08

## Fixed areas

- Replaced selector-specific loading behavior with one canonical 12-symbol ranking universe.
- Added canonical session-state keys:
  - `canonical_ranking_symbols`
  - `canonical_ranking_timeframe`
  - `canonical_symbol_load_status`
  - `canonical_symbol_candles`
  - `canonical_provider_trace`
  - `canonical_last_load_run_id`
- Enforced provider order for forex candles:
  1. Local cache/database
  2. FCS API main
  3. Twelve Data fallback
  4. Last-known valid cache
- Prevented legacy Twelve Data / Finnhub API-source settings from making those providers the main candle route.
- Kept Finnhub outside the candle-loading route.
- Added FCS-first provider diagnostics in the canonical status rows.
- Added FCS symbol-format fallback attempts (`AUD/USD` then `AUDUSD`).
- Added Settings buttons:
  - Load Selected Data for 12-Symbol Ranking
  - Reload Failed Symbols Only
  - Force Reload All 12 Symbols
- Fixed canonical Loaded Now counts from actual load status rows, not selector state.
- Fixed timeframe propagation so canonical load and Field 10 use the selected timeframe and do not render `nan`.
- Updated Field 10 to read canonical load status/candles/timeframe and keep all 12 rows visible.
- Added failed-row visibility with provider trace and reload eligibility.
- Added pandas-safe `first_valid_df` / explicit DataFrame checks in repaired paths.

## Validation performed

- Python compilation passed for repaired modules:
  - `core/data/market_data_orchestrator.py`
  - `core/multi_symbol_load_manager_20260707.py`
  - `ui/multi_symbol_settings_20260701.py`
  - `ui/lunch_field10_multi_symbol_20260701.py`
- Imported core provider/router modules successfully.
- Synthetic canonical test confirmed:
  - 12 deduplicated symbols are preserved in canonical order.
  - H4 is written to every canonical status row.
  - Legacy provider modes `twelve`, `twelve_data`, `finnhub`, `fcs`, and `auto` all resolve to FCS-first provider order.
