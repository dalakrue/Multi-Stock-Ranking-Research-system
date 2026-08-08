# Field 10 Two-Table Authority + H4 Refresh Gate — 2026-07-09

## What changed

Field 10 Lunch now renders only two multi-symbol ranking surfaces:

1. **Open / Close — Field 10 Unified Institutional Daily Rank Authority**
   - The only trusted table for final daily rank, Top 4, final less-risky bias, BUY/SELL/WAIT, and hold permission.
   - Shows snapshot identity, selected timeframe, completed broker candle, next allowed refresh, loaded/failed symbols, provider, sample count, and data quality.
   - Includes compact mobile-safe visualization controls for rank, confidence, regime probability, risk, expected return, sample size, bias, permission, quality, and publication status.

2. **Open / Close — Field 10 Supporting Evidence + Entry Timing Rank**
   - Supporting-only table for entry timing, best session, news/event veto, absorption, short-horizon risk, probability and expected-return explanation.
   - It explicitly states `Can Override Authority Bias? = NO` so it cannot become a second trusted direction table.
   - Includes its own mobile-safe visualization controls for session/risk/probability/expected-return and evidence-category distributions.

## H4 refresh rule

When the selected timeframe is **H4**, Field 10 now floors the publication watermark to the completed H4 candle boundary and sets:

- `Refresh Gate = REFRESH_ONLY_AFTER_H4_CANDLE_END`
- `Next Allowed Refresh = completed H4 candle + 4 hours`

If Lunch is reopened or lower-timeframe/interim cache values change before the next H4 candle boundary, the existing Field 10 authority snapshot is reused instead of recomputed. This prevents a selected-H4 ranking table from changing every 1 hour.

## Files changed

- `core/field10_unified_authority_20260709.py`
- `ui/lunch_field10_multi_symbol_20260701.py`
- `ui/mobile_export_panel.py`

## Validation

Targeted Python syntax validation passed for:

- `app.py`
- `adx_dashpoard.py`
- `core/field10_unified_authority_20260709.py`
- `ui/lunch_field10_multi_symbol_20260701.py`
- `ui/mobile_export_panel.py`

A local smoke test confirmed that an H4 run with raw candle `2026-07-09T09:00:00+00:00` locks to completed H4 candle `2026-07-09T08:00:00+00:00` and next allowed refresh `2026-07-09T12:00:00+00:00`. A second same-candle build reused the original rank table.
