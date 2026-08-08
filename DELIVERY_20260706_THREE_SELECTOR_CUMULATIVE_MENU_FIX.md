# Delivery — Three Selector, Cumulative Field 10, and Menu Position Repair

Date: 2026-07-06

## Implemented

1. **Floating menu moved down and made viewport-safe**
   - The fixed three-dot menu button is placed near the lower-right area on desktop and mobile.
   - The opened menu is positioned inside the viewport, has a bounded height, and scrolls vertically.
   - Lunch and Dinner remain clickable on phone, laptop, Auto, Mobile Lite, and Full Interface modes.

2. **Three independent Settings multi-symbol selectors**
   - First Multi-Symbol Selector — owned by Super Quick Calculation + Open Lunch.
   - Second Multi-Symbol Selector — owned by Quick Calculation + Open Lunch.
   - Third Multi-Symbol Selector — owned by Full Calculation + Open Lunch.
   - Each selector accepts a maximum of six symbols.

3. **Dedicated button-to-selector routing**
   - Super Quick calculates only the First selector.
   - Quick calculates only the Second selector.
   - Full calculates only the Third selector.
   - The existing calculation formulas are reused; no parallel prediction engine was added.

4. **Additive result preservation**
   - A later group run does not clear earlier successfully completed symbols.
   - Completed symbols are stored in a persistent cumulative symbol universe.
   - Existing database and exact-symbol cached results are reused where available instead of forcing unnecessary recalculation.
   - Partial runs add only completed symbols and keep previous valid results protected.

5. **Cumulative Field 10 ranking**
   - Field 10 loads the latest persisted compatible-timeframe row for every completed symbol across the First, Second, and Third groups.
   - All available completed symbols are ranked together using the existing Rank Score.
   - The original stored daily rank remains available as `Stored Daily Rank` for audit.

## Main changed files

- `core/multi_symbol_run_groups_20260706.py` — new three-group ownership and persistence layer.
- `ui/multi_symbol_settings_20260701.py` — three max-six selectors and explicit ownership labels.
- `tabs/antd_page_router_20260615.py` — dedicated button routing and cumulative completion handling.
- `core/multi_symbol_field10_20260701.py` — cumulative latest-per-symbol loading and ranking.
- `ui/home_master_control_bar_20260615.py` — lower floating button position.
- `ui/liquid_menu_popup_20260615.py` — fixed, lower, scrollable menu panel.
- `tests/test_three_selector_cumulative_20260706.py` — regression coverage.

## Validation completed

- Changed Python files passed `py_compile`.
- Three-selector/cumulative tests passed.
- Existing instant-run, H4 auto-connect/quota, multi-symbol routing, Field 3–Field 10 sync, and Field 10 multi-symbol targeted tests passed.
- A complete repository-wide test run was not claimed because this repair container does not include Streamlit for two import-time test modules.
