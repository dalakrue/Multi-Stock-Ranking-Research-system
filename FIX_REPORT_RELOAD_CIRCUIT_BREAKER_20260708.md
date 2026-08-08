# ADX Quant Pro — Reload / Circuit Breaker Repair 2026-07-08

## User-visible problem fixed
The Settings foreground symbol loader could show 7 / 12 loaded and 5 / 12 failed with the message:

`Provider skipped by foreground symbol-level circuit breaker after recent hard failure.`

After that, Reload Failed Symbols Only / Force Reload could appear to do nothing because the failed rows were classified as `FAILED_EXPLICIT` / circuit-open rows and were not always selected for retry.

## Root causes
1. Run-wide circuit breaker disabled the whole Twelve Data provider pool after transient failures, rate-limit windows, or timeout-like failures. This caused remaining symbols to be skipped instead of waiting for quota or retrying safely.
2. `force_live=True` did not bypass the local symbol-level circuit breaker, so force reload could replay the same old skipped result.
3. Canonical failed-only reload did not include `FAILED_EXPLICIT`, `RUN_CIRCUIT_OPEN`, `INSUFFICIENT`, and `PENDING` in the retry-eligible states.
4. Retry-only validation could overwrite already successful symbols with empty placeholder validation, so retrying the last 5 symbols could damage the first 7 successful symbols.

## Files changed
- `core/data/multi_symbol_scheduler.py`
- `core/data/market_data_orchestrator.py`
- `core/data/symbol_level_provider_registry_20260708.py`
- `core/multi_symbol_load_manager_20260707.py`

## Behavior after repair
- Load Selected Data still respects Twelve Data key-pool limits.
- Rate-limit/timeout failures no longer disable the whole provider for all remaining symbols.
- Reload / failed-only retry clears only the local circuit flag for the exact failed symbols and timeframe.
- Reload does **not** clear Twelve Data per-key credit counters or cooldowns.
- The first 7 successful symbols remain READY while the failed 5 retry.
- `FAILED_EXPLICIT` and `RUN_CIRCUIT_OPEN` rows now become reload eligible.
- Force Reload bypasses stale local circuit skip and makes a fresh provider decision.

## Important note
This patch does not bypass Twelve Data limits. If both keys are truly out of credits, the reload button will wait/fail with a quota-safe message instead of silently reusing the old circuit-breaker failure.

## Validation performed
- Python bytecode compile passed for the modified files:
  - `core/data/market_data_orchestrator.py`
  - `core/data/multi_symbol_scheduler.py`
  - `core/data/symbol_level_provider_registry_20260708.py`
  - `core/multi_symbol_load_manager_20260707.py`
- Local status smoke test passed: a synthetic canonical 7-loaded / 5-`FAILED_EXPLICIT` record now marks all five failed symbols as `Reload Eligible=True` while keeping the first seven loaded symbols READY.
