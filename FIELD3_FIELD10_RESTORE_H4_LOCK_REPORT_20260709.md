# Field 3 + Field 10 Restore / H4 Lock Repair — 2026-07-09

## What changed

1. Restored the section:
   **Field 3 Higher-Standard Multi-Symbol Bias + Consolidated Field 10 — All Loaded Settings Symbols**
   as a supporting exact-symbol evidence section under Field 10.

2. Kept the trusted rank authority single-source rule:
   **Open / Close — Field 10 Unified Institutional Daily Rank Authority** remains the only trusted final rank/bias table.
   The restored Field 3 + Field 10 section is display/supporting evidence only and cannot override authority rank or direction.

3. Added selected-timeframe candle locking for Field 10 authority:
   - H4 selected → authority snapshot floors raw sub-candle timestamps to the completed H4 boundary.
   - Same H4 candle → existing authority table is reused.
   - New rank can publish only when the selected timeframe completed candle changes or the selected symbol universe changes.

4. Super Quick now publishes complete transition-risk horizons in the authority/supporting views:
   - Transition Risk 1H
   - Transition Risk 3H
   - Transition Risk 6H
   - Transition Risk 12H
   - Transition Risk 24H
   - Transition Risk 36H

5. Removed unnecessary display-time recalculation from the restored consolidated section.
   Opening the section now reuses the already-built table and saved CSV bytes, so it does not call APIs and does not rebuild Field 10.

6. Fixed background risk fallback safety so missing CVaR does not break Super Quick evidence generation.

7. Updated current-result and load-universe sync to preserve all loaded Settings symbols across the three selectors instead of truncating the active run universe.

## Modified files

- `core/background_function_registry.py`
- `core/field10_unified_authority_20260709.py`
- `ui/lunch_field10_multi_symbol_20260701.py`
- `core/multi_symbol_load_manager_20260707.py`
- `core/current_result_sync_20260708.py`
- `deployment_readiness_report_20260709.md` (removed a live-secret-like literal from report text)

## Validation

Passed:

```bash
pytest -q tests/test_field3_field10_multi_symbol_sync_20260703.py tests/test_final_repair_20260707.py tests/test_three_selector_consolidation_20260707.py
# 27 passed
```

Smoke test passed:

- H4 raw candle `2026-07-09T11:00:00+00:00` normalized to completed H4 candle `2026-07-09T08:00:00+00:00`.
- Second build inside the same H4 candle reused the existing authority snapshot.
- Authority table contains all transition-risk horizons from 1H through 36H.
