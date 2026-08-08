# Fast Multi-Symbol Loading Repair — 2026-07-08

## User-visible problem

Clicking **Load Selected Data** could remain busy for a long time and still finish without valid symbol results, especially for H4 multi-symbol selections.

## Root causes repaired

1. **Wrong quota pacing was applied to Finnhub-primary loads.**
   The scheduler could automatically re-enable the Twelve Data rolling-window pause for large selectors even when Finnhub was the active primary provider. This introduced avoidable 60-second waits before/around Finnhub work.

2. **Finnhub H4 used an unsupported direct resolution.**
   The old request sent `resolution=240`. The repaired path requests real Finnhub H1 candles with `resolution=60`, then causally aggregates complete H1 OHLCV candles into H4 candles. No price is padded, copied from another symbol, or synthesized.

3. **Every Finnhub asset was sent to the forex endpoint.**
   The loader now selects the correct Finnhub candle endpoint for forex/metals, crypto, and stocks, and resolves common provider symbols such as `BTCUSD -> BINANCE:BTCUSDT`.

4. **The same provider-wide failure could repeat for every selected symbol.**
   A run-scoped circuit breaker now skips a provider for the remaining symbols after an authentication/configuration failure or transport timeout, while continuing through configured fallbacks and exact-symbol local cache.

5. **Unexpected loader exceptions could leave the UI without a complete result object.**
   The load manager now always returns structured per-symbol failure information and still attempts exact-symbol/timeframe SQLite recovery.

6. **The progress display did not show useful elapsed-time information.**
   During loading, the UI now displays completed/total symbols and elapsed seconds. After completion, each selector displays **Last Load Time**.

## Reliability contract

- Valid provider data is preferred.
- If a live provider fails, configured fallback providers are attempted.
- If live providers are unavailable, only validated local cache for the exact symbol and timeframe may be reused.
- The repair does **not** invent candles to force a false success.
- When no provider and no exact validated cache is available, the loader fails quickly with the provider attempt reasons instead of hanging or reporting an untrue success.

## Validation completed

- Changed modules compile successfully.
- 56 focused regression tests passed.
- The tests cover Finnhub H4 resampling, 12-symbol no-wait loading, provider circuit breaking, selector capacity, quota pacing, load-first state, multi-symbol routing, Field 10 population, and Field 3/Field 10 synchronization.
- Three existing scikit-learn warnings were emitted for single-label confusion-matrix test data; they are unrelated to the loader repair.
- UI modules that require the Streamlit package could not be fully runtime-launched in this sandbox because Streamlit is not installed here. Their changed Python source compiled successfully.
