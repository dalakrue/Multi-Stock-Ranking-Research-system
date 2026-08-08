# ADX Quant Pro Repair Notes — Current Result Synchronization (2026-07-08)

## What was fixed

- Added `core/current_result_sync_20260708.py` as the single current-result synchronization layer.
- Settings selected symbols and selected timeframe are now the source of truth for:
  - Field 3 / Table 3
  - Field 10
  - Data Visualization
  - NLP / sentiment table
  - CSV export
  - Copy Short / Copy Full
- Selector/timeframe changes clear stale visible/export/copy objects so old symbols do not remain after the selector changes.
- Super Quick / Quick / Full calculation buttons now use the cumulative loaded universe for calculation depth, while the visible selected universe remains the current Settings selection.
- Data Visualization is now routed and rendered as a real tab instead of falling back to Settings.
- Field 3 / Table 3 now shows current selected symbols with Rank, Scaled Score, Timeframe, provider/status, candle count, latest candle time, and failure reason.
- Field 10 now includes a public `Scaled Score` column and a current-result CSV download.
- Copy Short now copies the current Field 10 result only.
- Copy Full now copies current selected symbols, timeframe, Field 3/Table 3, Field 10, load status, NLP/sentiment, and diagnostics text.
- Current CSV export now includes run metadata, current selected symbols, timeframe, Field 3/Table 3, Field 10, loaded candle/provider status, and NLP/sentiment.
- Cache/display validation is tightened by keeping symbol + timeframe status visible and preventing old cached symbols from becoming selected unless the user selected them.

## Files changed / added

- Added: `core/current_result_sync_20260708.py`
- Updated: `tabs/antd_page_router_20260615.py`
- Updated: `core/multi_symbol_load_manager_20260707.py`
- Updated: `ui/multi_symbol_settings_20260701.py`
- Updated: `ui/lunch_four_core_fields_20260619.py`
- Updated: `ui/lunch_field10_multi_symbol_20260701.py`
- Updated: `ui/canonical_copy_export_20260619.py`

## Tests run

- Python compile check on changed files: passed.
- Current-result smoke test with changed selected symbols/timeframe: passed.
- Targeted pytest:
  - `tests/test_field10_all_selected_repair_20260707.py`
  - `tests/test_consolidated_field10_settings_repair_20260707.py`
  - `tests/test_adaptive_cumulative_selector_repair_20260707.py::test_cumulative_activation_merges_all_loaded_groups_without_six_symbol_cap`
  - Result: 11 passed.

## Note

Live API loading was not executed because real provider keys are not available in this sandbox. The patch preserves existing API/data-loading logic and fixes the synchronization, display, export, and copy architecture around it.
