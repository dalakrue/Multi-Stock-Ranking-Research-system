# Render Evidence — 2026-07-04

Live browser screenshots were not produced because this environment has no user credentials, MT5 terminal, or live connector session. The following executable/static evidence demonstrates the render paths:

- `ui/lunch_four_core_fields_20260619.py` renders `ui.lunch_multi_symbol_selector_20260704.render(1, state)` immediately before Field 1 and `.render(2, state)` immediately before Field 2.
- Both selectors share `lunch_active_symbol_20260704`, use separate widget keys, and queue a pending value before rerun.
- Selector source contains no call to `run_settings_calculation` or `run_selected_symbols`; the non-heavy-render test passes.
- `ui/lunch_field10_multi_symbol_20260701.py` includes the new pinned decision columns, legend, semantic styling, EV-vs-risk scatter, target-probability chart, volume heatmap, severity display, and API budget card.
- Protected Field 1/2 renderer hashes match the uploaded ZIP; existing content is preserved below the additive selector section.
- Import smoke and Streamlit-dependent tests pass after installing the project-declared Streamlit requirement.

See `delivery_evidence_20260704/import_smoke.log`, `pytest_protected_files.log`, and `pytest_upgrade.log`.
