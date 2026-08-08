# Field 10 Merged Buy/Sell + 100-Pip/4H Ranking Repair — 2026-07-09

## What changed

1. Merged the first Field 10 authority surface with the supporting evidence / entry-timing surface.
   - New first visible section:
     `✅📊 Open / Close — Field 10 Unified Institutional Daily Rank Authority + Supporting Evidence / Entry Timing Rank`
   - The first table now contains trusted rank columns plus entry timing, news/event, absorption, and session evidence.
   - Supporting evidence remains explanation/timing only and cannot publish a separate competing rank.

2. Removed WAIT from final Field 10 bias output.
   - `Stable Daily Bias` and `Less-Risky Bias` are now forced to BUY or SELL only.
   - Risk is displayed through `Entry Permission`, `Risk Control Gate`, `Trust Status`, transition risk, and event-risk columns instead of becoming a WAIT bias.

3. Added next-4-hour 100-pip movement logic.
   - New columns:
     - `Probability 100 Pip Move 4H`
     - `Projected 4H Move Pips`
     - `100 Pip 4H Priority`
     - `100 Pip 4H Target Status`
     - `100 Pip 4H Method`

4. Changed rank priority order.
   - Ranking now prioritizes:
     1. `Probability 100 Pip Move 4H`
     2. `Higher-Standard Regime Bias Priority`
     3. lowest `Transition Risk 6H`
   - Reliability, data quality, expected return, event/tail safety, calibration, and uniqueness remain supporting safeguards.

5. Added merged export support.
   - New CSV export: `field10_merged_authority_entry_timing_rank_*`
   - Full snapshot ZIP now includes `field10_merged_authority_supporting_rank.csv`.

## Files changed

- `core/field10_rank_governance_20260709.py`
- `core/field10_unified_authority_20260709.py`
- `ui/lunch_field10_multi_symbol_20260701.py`
- `ui/mobile_export_panel.py`

## Validation

- `python -m py_compile` passed for all modified files.
- `python -m compileall -q core ui app.py main.py adx_dashpoard.py` passed.
- A direct authority build test confirmed final bias columns no longer output WAIT.
