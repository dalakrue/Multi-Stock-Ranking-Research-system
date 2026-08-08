# Consolidated Field 3 / Field 10 Repair — 2026-07-07

## Visible UI changes

- Removed the visible Lunch search header and the duplicated `Lunch — Core Fields 1–3 + Fields 10–11` heading.
- Replaced the visible duplicated Field 10 surfaces with one closed-first expander:
  `Field 3 Higher-Standard Multi-Symbol Bias + Consolidated Field 10 Decision System`.
- The expander contains one wide, color-coded exact-symbol table, one selectable bar visualization, and one CSV export.
- The visible table starts from the cumulative loaded/configured/completed symbol spine, then left-merges Field 3 Higher Standard, latest-run ranking, technical/fundamental, sentiment/news/absorption, session, crowd, reliability, validation, and load evidence.
- Optional child-table gaps cannot remove a loaded symbol or copy another symbol's values.
- The former Field 10 Part 4 remainder is no longer rendered in Dinner.

## Settings and API behavior

- H4 is the first-session Settings timeframe.
- Each Load button uses the currently selected timeframe.
- Three selectors are rendered inside the always-visible Twelve Data connection container.
- Removed the duplicate legacy calculation-profile radio and duplicate explanatory text.
- The three existing run buttons remain the only calculation triggers.
- Secure server-side API credentials and connection-only startup are fixed on.
- Automatic calculation remains fixed off.
- Duplicate-run cooldown is fixed at 3 minutes.
- Live-request scheduler capacity is 7, with quota-aware pacing and exact local-cache recovery.

## Database and synchronization

- Deployment schema version: `2026070703`.
- Added `multi_symbol_symbol_sync_20260707` for per-group, per-symbol, per-timeframe load state.
- Extended `multi_symbol_load_audit_20260707` with request/load/failure counts and accepted live capacity.
- Added exact-symbol/timeframe load-record restoration after session/browser restart.
- Tightened Field 10 completion validation so insufficient-history rows cannot be marked complete.

## Security

- The uploaded live `.streamlit/secrets.toml` was removed from this delivery.
- Configure actual keys in Streamlit Cloud/App Settings. Only `.streamlit/secrets.example.toml` is included.

## Validation

- Python compile-all: passed for `core`, `ui`, and `tabs`.
- Temporary-database migration smoke test: passed.
- Focused repair suite: **38 passed**.
- The environment used to package this ZIP did not have Streamlit installed, so the unrelated complete repository suite could not finish collection. Streamlit remains declared in `requirements.txt` and `requirements-core.txt`.
