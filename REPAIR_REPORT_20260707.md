# ADX Quant Pro Repair Report — 2026-07-07

## Implemented repairs

- Fixed the three Settings selector state flow so an already-created Streamlit widget is authoritative. Removing or changing Third-selector symbols is no longer overwritten by stale session/database state.
- Changed Super Quick, Quick, and Full so all three calculate the cumulative exact-symbol universe successfully loaded across First, Second, and Third selectors. The selected button changes calculation depth only.
- Kept each selector limited to six symbols while removing the six-symbol cap from the cumulative calculation transaction.
- Kept all run buttons active whenever at least one symbol is configured and no real calculation is currently running. When no current load exists, the clicked button performs one genuine load for its owner group before calculation.
- Replaced the Third selector startup choices with `GBPAUD, GBPCAD, AUDJPY, XAUUSD, XAGUSD, NAS100`. `EURUSD`, `USDJPY`, and `GBPUSD` are not Third-selector defaults.
- Added quota-safe load pacing, unresolved-symbol retries, exact-symbol/timeframe cache recovery, and validation that never borrows or fabricates another symbol's candles.
- Retained the full 25-day history target, but added an adaptive genuine-history calculation contract:
  - full history: normal full-history calculation;
  - 100 candles or more: adaptive partial-history calculation with explicit labels and coverage/reliability penalties;
  - fewer than 100 candles: rejected as below the genuine minimum.
- A valid 597/600 H1 frame is now accepted for adaptive calculation rather than failing because only three candles are absent.
- Added same-symbol OHLC-derived fallback estimates for Field 10 expected returns, regime probability, transition risks, and reliability when optional historical calibration layers are unavailable. No synthetic candles or cross-symbol values are created.
- Relaxed Field 10 publication/completion validation only for valid adaptive rows. Missing identity, invalid spacing, below-minimum history, unavailable estimates, and failed validation still block publication.
- Added persistent selector/load architecture:
  - `runtime_symbol_groups_20260706` stores all three selector choices and the completed universe;
  - `multi_symbol_load_audit_20260707` stores load signatures, loaded/failed symbols, validation results, status, and timestamps;
  - schema migration version `2026070702` is idempotent.
- Corrected Field 10 section order so the session map, sentiment rank, crowd rank, final combined rank, and immutable history appear in the validated order.

## Validation performed

- Python compilation passed for `core/`, `ui/`, and `tabs/`.
- Targeted selector, loading, cumulative-run, Field 3/Field 10 synchronization, daily snapshot, routing, and publication regression suite: **95 passed**.
- Final repair regression subset after the last UI/order edits: **63 passed**.
- New repair-specific tests cover 597/600 acceptance, 100-candle adaptive output, 99-candle rejection, nine-symbol cumulative activation, Third defaults, preference persistence, migration tables, widget authority, and adaptive daily validation: **9 passed**.
- Temporary-database migration and selector save/restore smoke test passed.
- Streamlit server startup smoke test passed on `app.py` with no immediate traceback.

## Important operational note

The repair never invents candles or claims live provider success without genuine data. Live Twelve Data, Finnhub, MT5, and deployment behavior still depend on the user's valid credentials, provider symbol coverage, rate limits, and network availability. Those external services were not called from the offline test environment.
