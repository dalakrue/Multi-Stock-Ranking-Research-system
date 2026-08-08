# Selector 2 Twelve Data Symbol Format Repair — 2026-07-08

## User-visible problem
Selector 2 selected symbols such as:

`NZDUSD → EURCHF → EURAUD → EURCAD → EURNZD → GBPCHF`

Key 2 spent credits but loaded only 1 symbol. The last error was:

`Twelve Data request failed (HTTP 404): symbol or figi parameter is missing or invalid.`

## Root cause
The Twelve Data formatter in `core/connectors/data_parts/utils.py` cleaned symbols by removing `/`, then only re-added `/` for a small whitelist of majors. That means Selector 2 crosses were sent like:

- `EURCHF` instead of `EUR/CHF`
- `EURAUD` instead of `EUR/AUD`
- `EURCAD` instead of `EUR/CAD`
- `EURNZD` instead of `EUR/NZD`
- `GBPCHF` instead of `GBP/CHF`

Twelve Data rejected those requests with HTTP 404, so credits were consumed but candles were not returned.

## Fix
Updated `_twelve_symbol()` to:

1. Preserve special aliases for metals, crypto, and index names.
2. Format any valid six-letter fiat FX pair as `BASE/QUOTE` automatically.
3. Add regression tests for the exact Selector 2 symbols.

## Files changed
- `core/connectors/data_parts/utils.py`
- `tests/test_twelve_symbol_formatter_20260708.py`

## Smoke tests run
Passed:

- `tests/test_twelve_symbol_formatter_20260708.py`
- `tests/test_selector_owned_twelve_loader_20260708.py`
- `tests/test_twelve_data_key_pool_20260708.py`

Note: older `tests/test_market_data_recovery_20260708.py` still expects a Finnhub/MT5 primary candle fallback order that conflicts with the current selector-owned Twelve two-key architecture.
