# Implementation Report

## Architecture retained

`Settings orchestrator → canonical Field 10 daily snapshot → persisted source children → persisted crowd child → persisted final child → read-only Lunch tables`

No second production ranking truth was introduced. `field10_daily_snapshot` and `field10_daily_snapshot_symbol` remain the parent authority.

## Main implementation

`core/field10_crowd_final_20260704.py` adds:

- centralized formula/threshold registry;
- exactly-600 completed-H1 extraction with forming-candle exclusion;
- eight-session persisted map;
- pair-aware crowd state, contrarian, panic/FOMO, exhaustion, divergence, volatility, and proxy-flow features;
- 1H/6H/12H/24H transition risk and EV;
- four-persisted-source final fusion and evidence lineage;
- immutable publication/outcome helpers;
- read-only loaders and live-safety permission overlay.

`core/multi_symbol_field10_20260701.py` publishes these tables only after the existing daily snapshot succeeds inside the Settings-owned heavy run. A complete identity gate (`run_id`, `source_id`, `snapshot_hash`, completed candle) now prevents the Field 3 sidecar from fitting on incomplete partial/synthetic snapshots.

`ui/lunch_field10_multi_symbol_20260701.py` renders the required order, closed by default, with no migration, API call, or model fit on expander open. It includes state text/icons, top-four full-row styles, safety overrides, and mobile-first final columns.

## Immutability and lineage

Each final row persists four source row references and hashes, fusion components, penalties, horizon EV components, transition components, formula/model versions, final publication hash, and content hash. Live safety may downgrade permission to caution/block/exit-reduce but cannot rewrite persisted rank or locked bias.

## Units

Returns, EV, MFE, MAE, CVaR, spread, and slippage use `PERCENT_RETURN`; risks/probabilities use 0–100 percentages.

## Honest status and limitations

- Both new models remain **shadow-only**: `field10_crowd_psychology_candidate_v1` and `field10_final_multi_symbol_candidate_v1`.
- The supplied environment had no live retail-positioning, social-sentiment, or true institutional order-flow feed. Those values remain `UNAVAILABLE`; candle/tick-volume measures are labelled proxies.
- No production calibration, accuracy, or profitability claim is made.
- The migrated database has zero new crowd/final rows until the next qualifying Settings calculation; migration does not fabricate historical publications.
- Long-history promotion tests (purged/embargoed OOS calibration, Hansen SPA, CSCV/PBO, Deflated Sharpe Ratio, and structural-break stability) need more clean history and immutable outcomes than were supplied.
- The container provided Python 3.13.5, not 3.12. Changed files passed a Python-3.12 AST syntax check, and compile/import/Streamlit launch checks passed on 3.13.5. Installing 3.12 was blocked by the offline environment.

