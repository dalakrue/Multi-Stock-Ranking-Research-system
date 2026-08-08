# Database Schemas

## Field 11 SQLite

### `field11_schema_migration`
`version` primary key, applied timestamp and description.

### `field11_index_manifest`
One versioned index per canonical identity: index/run/hash/rank identity, broker date/candle, universe, versions, artifact paths/hashes, timeframes, row counts, status and creation time.

### `field11_simulator_run`
Unique selection hash and simulator run id, index identity, source symbol/timeframe/candle, horizon, serialized selectors, scenario/summary payloads, reliability grade, drift status, pending/settled status and timestamps.

### `field11_simulator_analogue`
Composite primary key `(simulator_run_id, analogue_id)`, match rank, source identity/time, similarity, weight, component JSON, outcome/path JSON, cluster, inclusion status and rejection reason.

### `field11_outcome_settlement`
Deterministic `settlement_key`, unique simulator run id, actual path/endpoint/MFE/MAE, closest scenario, path distances, 50%/80% band coverage, dominant-scenario correctness, settlement time and status.

## Field 10 storage

The existing migration-safe Field 10 tables remain authoritative:

- `field10_daily_snapshot`
- `field10_daily_snapshot_symbol`
- `field10_daily_score_component`
- `field10_daily_safety_event`
- `field10_daily_outcome`
- `field10_next_day_candidate`
- `field10_model_validation_registry`
- `field10_daily_snapshot_audit`

No old row is dropped by the Field 11 migration.
