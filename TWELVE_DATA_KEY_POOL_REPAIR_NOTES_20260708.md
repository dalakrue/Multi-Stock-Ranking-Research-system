# ADX Quant Pro — Twelve Data Key Pool Repair (2026-07-08)

## Main change
The active market-data route is now:

1. Validated local database/cache
2. Twelve Data key pool (`TWELVE_KEY_1`, `TWELVE_KEY_2`)
3. Finnhub candle fallback when configured
4. Last-known valid cache
5. Explicit failure row with reason

The FCS API connector, key input, connection test, and live request path have been removed from the active runtime/UI. Legacy disabled alias handling remains only to stop old saved sessions from selecting the removed provider.

## Added
- `core/twelve_data_key_pool.py`
- Per-key credit counter
- Per-key cooldown and 429 handling
- Masked key display only
- Key 1 / Key 2 Settings tests
- Canonical 12-symbol loader compatibility
- `provider_key_alias` database storage, never raw keys
- Targeted tests in `tests/test_twelve_data_key_pool_20260708.py`

## Tested
```bash
python -m pytest tests/test_twelve_data_key_pool_20260708.py tests/test_foreground_symbol_router_20260708.py -q
# 14 passed
```
