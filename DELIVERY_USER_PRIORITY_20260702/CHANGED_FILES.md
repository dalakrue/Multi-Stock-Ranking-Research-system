# Changed Files

## Production code

1. `core/multi_symbol_field10_20260701.py`
   - Makes the first ordered Settings selection authoritative at run start.
   - Prevents a stale saved Main Core Symbol from replacing the first current selection.
   - Corrects secondary calculation scope descriptions to Fields 1–3 plus Fields 10–11.

2. `core/system_continuous_validation_20260702.py`
   - Adds symbol-local lower/higher bias recovery.
   - Adds a complete Field 10 priority overlay for every selected symbol.
   - Preserves the immutable daily publication and original eligible rank.
   - Adds comparative all-symbol rank, evidence coverage, explicit statuses, and local H1 fallback metrics.
   - Prevents blank, N/A, and generic unavailable cells in the visible priority table without inventing numeric zeroes.
   - Adds validation for missing selected symbols, complete ranking, visible-cell coverage, and metric variability.

3. `ui/lunch_field10_multi_symbol_20260701.py`
   - Places the current-day selected-symbol ranking first.
   - Uses the saved selected-symbol universe when rendering.
   - Builds a clearly labelled local-cache recovery view when the immutable morning publication is absent.
   - Adds safe metric formatting for numeric/status values.
   - Shows comparative rank while retaining the original eligible rank in the table.

4. `tabs/antd_page_router_20260615.py`
   - Corrects Settings run scope text to Fields 10–11 for secondary symbols.

## Tests updated or added

5. `tests/test_multi_symbol_routing_20260702.py`
   - Verifies first-selected Main Core Symbol authority and correct scope restoration.

6. `tests/test_full_multi_symbol_repair_20260702.py`
   - Adds complete selected-universe Field 10 coverage, immutable-source, no-blank, and no-unavailable assertions.

7. `tests/test_field10_daily_snapshot_contract_20260702.py`
   - Updates the accepted secondary scope contract to Fields 10–11.

No production calculation model, protected history table, canonical snapshot, API connector, Power BI model, or existing valid field was deleted or replaced.
