# ADX Quant Pro — v9 Architecture Rebuild Delivery

## Package
Patched project: `ADX_QUANT_PRO_FIELD10_INTEGRATED_EVIDENCE_20260702`

## Main v9 fixes applied

1. Added `core/v9_architecture_guard_20260702.py` as an additive single-source-of-truth guard.
   - Publishes complete canonical identity aliases.
   - Repairs missing `run_id`, source/snapshot id, completed candle id, symbol, timeframe, and broker candle identity when evidence exists.
   - Builds `canonical_state` and Power BI bundle fallbacks without replacing protected calculations.

2. Patched app startup/runtime.
   - `core/app/runner.py` installs global symbol state and pre-render canonical repair.
   - `tabs/antd_page_router_20260615.py` finalizes canonical identity after Settings calculation.
   - `core/multi_symbol_field10_20260701.py` finalizes canonical identity after each child-symbol batch run.

3. Fixed Streamlit widget-state crash.
   - `ui/lunch_four_core_fields_20260619.py` now uses an `on_change` lunch symbol selector and does not mutate the widget key after selectbox creation.

4. Fixed slider `min_value == max_value` crash.
   - `core/streamlit_compat_20260615.py` now wraps sliders and safely expands equal min/max ranges.

5. Fixed Pandas string-time assignment warning.
   - `ui/lunch_next_hour_bias_history_20260626.py` explicitly casts time columns to string before assigning values like `04:00`.

6. Field 10 integrity check softened correctly for optional render-only fields.
   - Fields 1–3 still fail if required saved results are missing.
   - Fields 4–9 become warnings instead of hard failures when the canonical run exists but optional render-only payloads are not published.

7. Power BI missing bundle fallback.
   - v9 guard stores `powerbi_bundle`, `powerbi_calibrated_bundle`, and `powerbi_calibrated_bundle_20260617` after calculation if legacy code did not publish a calibrated bundle.

8. Field 10 research saved-state fallback.
   - `core/field10_ten_paper_research_20260701.py` now uses the active canonical state as a safe fallback when saved canonical symbol state is unavailable immediately after a completed generation.

9. Expanded multi-symbol presets and instrument groups.
   - Added top FX pairs, high-volume equities, indices, metals, and crypto symbols.
   - Added preset buttons in `ui/multi_symbol_settings_20260701.py`.

10. Candle safety.
   - v9 guard exposes `MAX_CANDLES = 60000` and `safe_candle_count()` for new/updated call sites.

## Validation performed in sandbox

- Python syntax compile passed for all changed files:
  - `core/v9_architecture_guard_20260702.py`
  - `core/streamlit_compat_20260615.py`
  - `ui/lunch_next_hour_bias_history_20260626.py`
  - `ui/lunch_four_core_fields_20260619.py`
  - `core/multi_symbol_field10_20260701.py`
  - `tabs/antd_page_router_20260615.py`
  - `core/field10_ten_paper_research_20260701.py`
  - `ui/multi_symbol_settings_20260701.py`

- Runtime smoke test passed for v9 canonical repair with a Pandas DataFrame payload.

## Notes

This rebuild is additive. It does not delete, rename, or replace protected trading calculations, regime formulas, decision outputs, ML models, or history rows. It fixes orchestration, canonical identity publication, UI safety, and renderer stability.
