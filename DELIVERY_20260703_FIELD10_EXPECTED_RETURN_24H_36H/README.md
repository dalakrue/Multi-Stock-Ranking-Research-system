# Field 10 Expected Return 24H / 36H Upgrade

## Delivered

- Added `Expected Return 24H (%)` and `Expected Return 36H (%)` to the Field 10 calculation, hourly quality table, daily higher-standard lock, immutable daily snapshot, integrated evidence history, child-generation contract, continuous validation overlay, and Lunch surfaces.
- The authoritative **Today First — Ranked Multi-Symbol Decision Table** places both columns at the far left and pins them during horizontal scrolling through `streamlit-aggrid`. If AgGrid is unavailable, the columns remain first in the normal Streamlit table.
- Settings publication and Lunch loading now use the same migration version: `field10-unified-rank-columns-20260703-v2`.
- Existing `Daily Rank` remains the first CSV/export contract field, so previous exports and tests are preserved.

## Calculation

For each horizon (12, 24, and 36 completed H1 candles), the engine:

1. Builds causal H1 regime, strength, and volatility features.
2. Uses same-regime historical observations when at least 24 exist; otherwise it uses the broader symbol history.
3. Selects the closest historical analogues by normalized strength and volatility distance.
4. Requires at least 20 valid forward-return observations.
5. Clips the 5th/95th percentile tails and applies exponential distance weights.
6. Publishes the weighted signed percentage return. It does not fabricate zero when evidence is unavailable.

## Migration safety

- Schema migration is additive and idempotent.
- Historical backfill accepts only exact same-symbol local H1 evidence.
- Every historical calculation is truncated at that row's own completed-candle timestamp to prevent future-data leakage.
- Unknown or mismatched instrument identity is rejected.
- The original bundled database is preserved as:
  `data/multi_symbol_field10_20260701.pre_expected_return_24h_36h_backup.sqlite3`

## Bundled database result

- SQLite integrity: `ok`
- Foreign-key issues: `0`
- Missing required columns: none
- 24H/36H sync conflicts: `0`
- First migration backfilled two EURUSD snapshot dates using identity-verified local H1 history.
- USDJPY, GBPJPY, and XAUUSD expected returns remain `NULL` because no exact same-symbol local H1 source was bundled. Their values will be calculated and persisted by their next successful Settings multi-symbol run.
- Second migration run changed zero rows, confirming idempotence.

See `FIELD10_EXPECTED_RETURN_24H_36H_MIGRATION_REPORT.json` for the machine-readable report.
