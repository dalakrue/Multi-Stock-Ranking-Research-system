# Deployment Readiness Report — 20260709 Field 10 Research Authority

## Entry points
- Preferred: `streamlit run app.py`
- Legacy compatible: `streamlit run adx_dashpoard.py`

## Runtime
- `runtime.txt`: `python-3.12`
- `requirements.txt` includes `streamlit>=1.35,<2`.

## Import / syntax
- Python compile check passed for all new and modified files.
- Local full import of `app.py` was not run because the container does not have Streamlit installed. This is an environment limitation, not a source-code syntax failure.

## Database
- New Field 10 research authority migration applied successfully.
- Migration is idempotent and safe to run more than once.
- Existing database objects are preserved.

## Mobile export
- Added normal expander: `Open / Close — CSV Export and Phone Download Panel`.
- Added `Exit Download Mode` and `Close Export Panel` buttons.
- No full-screen modal is used.
- Downloads do not intentionally reset active tab, selected symbol, or current snapshot.

## Snapshot sync
- Field 10, Dinner, Data Visualization, and Export now share one `snapshot_hash` through the new view-model sync guard.
- If hashes diverge, the UI displays `SYNC_ERROR` and explains mismatched hashes.

## Trusted table rule
- `Field 10 Unified Daily Locked Rank Table` is the only table allowed to publish final rank, final less-risky bias, BUY/SELL/WAIT, and Top 4.
- Session/news/legacy fusion tables are supporting evidence only.

## Secret scan
- No OpenRouter-style OpenRouter-style secret prefix secret was found in active Python/TOML files by the local scan.
- Two documentation files contain generic hash-like strings; these were not treated as exposed API keys.

## Known limitation
- The new research background functions are lightweight deterministic background outputs over existing saved evidence. They do not replace your protected trading formulas.
- True order flow, FinBERT, scheduled economic actual/consensus, and exact event release times remain `UNAVAILABLE` unless the upstream data source provides them.
