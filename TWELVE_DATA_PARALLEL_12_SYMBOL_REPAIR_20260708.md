# ADX Quant Pro — Twelve Data Parallel 12-Symbol Repair (2026-07-08)

## Problem fixed
The Settings screen could show two Twelve Data keys as connected, but the 12-symbol loader still behaved like only one key was being used. In practice, 7 symbols loaded and 5 symbols failed.

## Root cause
The live Twelve Data fetch path converted the runtime state into a temporary `dict` copy before creating the key pool. During parallel loading, every worker received its own empty per-key runtime ledger. Because each worker saw Key 1 as unused, they all preferred Key 1 first. Key 2 was configured, but it was not reliably used as an independent worker during the live 12-symbol transaction.

## Repair implemented
- Kept the real Streamlit session/runtime state object inside `TwelveDataKeyPool` instead of requiring strict `MutableMapping` type checks.
- Added Streamlit SessionStateProxy-compatible state detection using `get` + `__setitem__`.
- Stopped converting state to `dict` in `MarketDataOrchestrator._fetch_twelve()`.
- Added a shared per-key runtime ledger so parallel workers reserve Key 1 and Key 2 fairly.
- Preserved one separate credit counter, cooldown, 429 handling, failure reason, and masked status per key.
- Added alias-specific reservation for Settings `Test Key 1` / `Test Key 2`, so test requests consume the correct key counter and the remaining-credit table is honest.
- Added regression test for a Streamlit-like session object that is mutable but not a strict `MutableMapping` subclass.

## Files changed
- `core/twelve_data_key_pool.py`
- `core/data/market_data_orchestrator.py`
- `tests/test_twelve_data_key_pool_20260708.py`

## Validation run
```bash
python -m compileall -q core/twelve_data_key_pool.py core/data/market_data_orchestrator.py core/data/multi_symbol_scheduler.py core/multi_symbol_load_manager_20260707.py
python -m pytest tests/test_twelve_data_key_pool_20260708.py tests/test_foreground_symbol_router_20260708.py -q
```

Result:
- `15 passed`

## Important operational note
This repair makes both configured Twelve Data keys work as two separate rate-limited workers. It does not bypass provider limits. If both keys are exhausted, cooled down, invalid, or the provider rejects a symbol, the system must still show an explicit failure reason or use valid exact-symbol cache if available.
