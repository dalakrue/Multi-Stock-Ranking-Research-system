# Streamlit Cloud Import Repair — 2026-07-03

## Root cause

`core.ui.legacy_impl.styles_impl` depended at runtime on generated `styles_impl_v9_parts/part_*.py` files. The deployed GitHub tree did not contain that generated directory, so `core.v9_compat_loader` raised `ModuleNotFoundError` before the application shell could start.

## Repairs applied

1. Flattened 20 non-protected V9 compatibility wrappers into normal Python modules using their exact preserved `SOURCE_LINES` content.
2. Preserved all additive wrapper extensions, including the Settings post-publication hooks and Lunch Field 7/8 copy extensions.
3. Kept protected canonical and decision-engine files byte-for-byte unchanged.
4. Added an exact standalone fallback for the protected canonical runtime and taught `core.v9_compat_loader` to use it if generated split directories are absent.
5. Hardened the loader to search both `*_v9_parts` and archived `*_parts` directories.
6. Added missing compatibility modules for canonical lookup and Lunch Fields 2, 3, and 4.
7. Removed all active runtime dependence on V9 source-part directories except the protected canonical wrapper, which now has a verified standalone fallback.

## Validation

- Python compile audit: PASS for the complete repository.
- Internal import audit: 1,639 imports checked; 0 missing.
- Regression tests: 301 passed in four isolated batches.
- Protected upload hashes: 10/10 unchanged.
- Secret scan: 0 embedded API-key findings.
- Deployment simulation: PASS after temporarily removing all 33 `*_v9_parts` directories.
- `app.py` import: PASS; `run_app` is callable in the no-V9-parts simulation.

## Deployment entry point

- Main file: `app.py`
- Python: 3.12 (`.python-version` and `runtime.txt` are included)

## Important limitation of local validation

The execution environment used for this repair was offline and did not contain the real Streamlit package. Full imports and regression tests were therefore validated with local no-op UI stubs; the project requirements and the supplied Cloud log confirm Streamlit and its deployment dependencies are installed by Streamlit Cloud.
