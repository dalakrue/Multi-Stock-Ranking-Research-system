# ADX Quant Pro — Field 10 / Multi-Symbol Repair Delivery

## Read first

This delivery repairs the symbol identity, immutable child publication, Field 10 evidence, saved-generation restoration, copy identity, collapsed-slider and dtype contracts before adding research outputs.

Start with:

1. `docs/ROOT_CAUSE_REPORT_20260702.md`
2. `docs/REQUIREMENT_CLASSIFICATION_20260702.md`
3. `docs/DEPLOYMENT_INSTRUCTIONS_20260702.md`
4. `docs/ROLLBACK_INSTRUCTIONS_20260702.md`

## Verification summary

- Preferred entry file: `app.py`
- Full pytest: see `evidence/pytest_final_raw.txt`
- Compileall: see `evidence/compileall_final_raw.txt`
- Streamlit health: see `evidence/streamlit_health.txt`
- Performance: warm deterministic fixture improves substantially, but the live 30–50% target is **not claimed**.
- Research: ten methods are shadow-only; insufficient-data methods return `UNAVAILABLE`.

## Important production storage setting

On ephemeral hosting, set `ADX_DURABLE_DB_PATH` and `ADX_DURABLE_SNAPSHOT_DIR` to durable storage. Session State and ephemeral local files alone are not sufficient.
