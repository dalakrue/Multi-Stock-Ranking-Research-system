# Field 3 / Field 10 Multi-Symbol Sync Repair — 2026-07-03

## Delivered behavior

1. **Lunch selector synchronization repaired**
   - Recovers the current canonical run symbol, completed Settings symbols, generation-registry symbols, and readable per-symbol runtime snapshots.
   - Repairs the stale state shown in the supplied screenshot where the market/canonical run was `NZDUSD` but the Lunch selector and metrics stayed on `EURUSD`.
   - The first symbol remains the Settings/main symbol; completed secondary symbols stay selectable.

2. **New Field 10 top table**
   - Added **“Field 3 Higher-Standard Multi-Symbol Bias — All Completed Settings Symbols”** at the very top of Field 10.
   - One row per recovered symbol.
   - Uses the exact Field 3 **Higher Standard** row first.
   - Does not borrow a Lower/Middle row or another symbol.
   - If the saved Higher row has no directional result but exact-symbol completed H1 OHLC exists, it derives a transparent local H1 adaptive direction and labels the evidence source.
   - Includes rank, symbol, Higher Standard regime, Higher-Standard bias, less-risky bias, reliability, regime probability, transition risks, sample count, data quality, source, status, completed candle, and comparative score.

3. **Field 3 multi-symbol connector**
   - Added a Field 3 connector above all Field 3 tables.
   - **Settings completed symbols** mode loads a previously completed child generation and synchronizes Lunch/Field 10.
   - **Plan B — Top 10 Currency Pairs** exposes: EURUSD, USDJPY, AUDUSD, GBPUSD, USDCAD, USDCHF, EURJPY, GBPJPY, EURGBP, NZDUSD.
   - Plan B builds Lower/Middle/Higher Field 3 tables from the selected pair’s own completed H1 data. It may reuse the saved provider profile/exact-candle cache when a saved child snapshot is unavailable.
   - The local fallback is display-only and does not overwrite the protected production canonical decision.

4. **Higher Standard bias extraction repaired**
   - Added one shared standard-aware resolver.
   - A generic `Regime Bias` value is accepted only when its row/container is identified as the requested standard.
   - Field 10 daily publication and display overlay now use the same resolver.
   - A generic `WAIT` no longer hides a valid exact-symbol directional H1 result.

5. **Streamlit widget-state safety**
   - Uses pending-reset keys and reruns instead of modifying an already-instantiated Lunch widget.
   - Adds a one-time stale-widget recovery so the current canonical symbol is displayed first without preventing later choose-then-connect use.

## Changed files

- `core/field3_bias_resolver_20260703.py` (new)
- `core/field3_multi_symbol_fallback_20260703.py` (new)
- `core/multi_symbol_field10_20260701.py`
- `core/system_continuous_validation_20260702.py`
- `core/field10_daily_snapshot_contract_20260702.py`
- `ui/lunch_four_core_fields_20260619.py`
- `ui/lunch_field10_multi_symbol_20260701.py`
- `tests/test_field3_field10_multi_symbol_sync_20260703.py` (new)
