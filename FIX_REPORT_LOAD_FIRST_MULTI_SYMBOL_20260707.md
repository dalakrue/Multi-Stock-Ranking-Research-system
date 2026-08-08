# Load-First Multi-Symbol Repair — 2026-07-07

## Implemented behavior

1. **Three separate Load buttons in Settings**
   - First selector → its own `Load Selected Data` button.
   - Second selector → its own `Load Selected Data` button.
   - Third selector → its own `Load Selected Data` button.
   - Each group remains capped at six symbols and retains its own selection order.

2. **Calculation is now a separate second step**
   - Super Quick calculates only loaded/validated symbols from the First selector.
   - Quick calculates only loaded/validated symbols from the Second selector.
   - Full calculates only loaded/validated symbols from the Third selector.
   - Calculation does not call the market-data provider again.
   - A changed selector or timeframe makes the previous load stale and requires a new load.

3. **Real-history admission gate**
   - A symbol is calculation-ready only when the provider/cache result is successful, the genuine selected-timeframe frame contains the required 25-day higher-standard candle count, and candle spacing is valid.
   - Symbols with insufficient history remain rejected and are not calculated.
   - Partial loads are supported: the calculation button runs only the successfully loaded symbols and clearly reports rejected symbols.
   - Market-closure gaps for equities, indices, metals, weekends, holidays, and daylight-saving boundaries are accepted without accepting duplicate or sub-timeframe candles.

4. **97% publication failure repaired**
   - Legacy values such as `GEN-d95bb1bf93bb3e05` are no longer passed to `int()`.
   - `calculation_generation` is always a deterministic positive integer.
   - The readable `GEN-*` value is preserved separately as `generation_id`.
   - Canonical runtime, snapshot publication, history persistence, reliability, regime, AI/Dinner, and research generation consumers now tolerate and normalize legacy saved values.

5. **Field 10 incomplete-card prevention**
   - Raw selector values and partial readable caches are no longer treated as completed Field 10 publications.
   - Field 10's all-symbol universe is built from completed cumulative/registry/manifest publications only.
   - Load-ready but not-yet-calculated symbols stay in Settings until a successful child publication exists.

6. **Failure safety**
   - Missing/stale loaded data blocks calculation with a direct instruction to reload the related selector.
   - Previous completed database/canonical results remain preserved.
   - No synthetic candles, borrowed rows, or cross-symbol replacement data are created.

## Validation completed

- Python compile validation completed for `core`, `ui`, `tabs`, `services`, and `research_quant`.
- Focused automated tests: **23 passed**.
- Exact legacy generation test covers `GEN-d95bb1bf93bb3e05`.
- Load-first tests verify partial history rejection, stale selection detection, exact loaded-symbol activation, and that calculation never invokes the loader.
- Existing Instant Run, three-selector cumulative, and Field 10 all-selected repair tests passed.

## Operational note

The application cannot manufacture genuine provider history when an API is unavailable, rate-limited, or does not support a symbol. In that case the Load button reports the affected symbol as rejected and the calculation safely excludes it instead of publishing a false successful result.
