# Database Migration Report

## New table

`field10_integrated_evidence_history`

Primary key:

```text
parent_run_id, symbol, timeframe, broker_timestamp, child_run_id, snapshot_hash
```

Indexes created:

- `idx_field10_integrated_symbol_time` on symbol + broker timestamp
- `idx_field10_integrated_parent_rank` on parent run + rank
- `idx_field10_integrated_broker_date` on broker date
- `idx_field10_integrated_action` on protected final action
- `idx_field10_integrated_regime` on higher-standard regime + regime bias
- `idx_field10_integrated_session` on current session
- `idx_field10_integrated_quality` on data-quality grade

## Supporting state tables

- `field10_shadow_incremental_state`: incremental Bayesian changepoint/ADWIN state by symbol and state name.
- `field10_conformal_state`: symbol × horizon × session coverage state.

## Safety

Migration is additive and does not alter or drop existing Field 10 tables. WAL and `synchronous=NORMAL` are enabled. Duplicate identities are rejected by the primary key. No runtime SQLite file is shipped in the ZIP; tables are created on first calculation.
