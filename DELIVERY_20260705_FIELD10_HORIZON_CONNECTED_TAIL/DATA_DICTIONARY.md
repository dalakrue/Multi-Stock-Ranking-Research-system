# Data Dictionary

All candidate tables are append-only children of the immutable Field 10 snapshot. Audit UTC is creation metadata only; broker identity comes from the parent snapshot.

## `field10_horizon_volatility_shadow`

| Column | SQL type | Nullable | Purpose |
|---|---|---:|---|
| `daily_snapshot_id` | TEXT | No | Immutable parent snapshot key |
| `parent_run_id` | TEXT | No | Exact parent calculation run |
| `child_run_id` | TEXT | Yes | Exact child generation id when present |
| `symbol` | TEXT | No | Canonical instrument |
| `timeframe` | TEXT | No | Canonical H1 timeframe |
| `broker_day` | TEXT | No | Locked broker day |
| `horizon` | INTEGER | No | Independent forecast horizon in hours |
| `completed_broker_candle` | TEXT | No | Locked latest completed H1 candle |
| `forecast_volatility` | REAL | Yes | Forecast volatility |
| `volatility_percentile` | REAL | Yes | Volatility percentile |
| `volatility_surprise` | REAL | Yes | Volatility surprise |
| `volatility_forecast_error` | REAL | Yes | Volatility forecast error |
| `expected_movement_lower` | REAL | Yes | Expected movement lower |
| `expected_movement_upper` | REAL | Yes | Expected movement upper |
| `har_sample_count` | INTEGER | No | Har sample count |
| `har_validation_status` | TEXT | No | Har validation status |
| `har_missing_reason` | TEXT | Yes | Har missing reason |
| `model_version` | TEXT | No | Model version |
| `feature_version` | TEXT | No | Feature version |
| `formula_version` | TEXT | No | Formula version |
| `threshold_version` | TEXT | No | Threshold version |
| `source_id` | TEXT | Yes | Exact source identifier |
| `source_hash` | TEXT | Yes | Exact persisted source/snapshot hash |
| `snapshot_hash` | TEXT | Yes | Exact immutable symbol snapshot hash |
| `universe_hash` | TEXT | No | Universe hash |
| `evidence_json` | TEXT | No | Versioned detailed evidence/provenance |
| `content_hash` | TEXT | No | Deterministic row content hash |
| `validation_status` | TEXT | No | Evidence validation state |
| `missing_reason` | TEXT | Yes | Explicit reason for unavailable evidence |
| `created_system_time` | TEXT | No | UTC audit timestamp; never market identity |

## `field10_semivariance_shadow`

| Column | SQL type | Nullable | Purpose |
|---|---|---:|---|
| `daily_snapshot_id` | TEXT | No | Immutable parent snapshot key |
| `parent_run_id` | TEXT | No | Exact parent calculation run |
| `child_run_id` | TEXT | Yes | Exact child generation id when present |
| `symbol` | TEXT | No | Canonical instrument |
| `timeframe` | TEXT | No | Canonical H1 timeframe |
| `broker_day` | TEXT | No | Locked broker day |
| `horizon` | INTEGER | No | Independent forecast horizon in hours |
| `completed_broker_candle` | TEXT | No | Locked latest completed H1 candle |
| `positive_realized_semivariance` | REAL | Yes | Positive realized semivariance |
| `negative_realized_semivariance` | REAL | Yes | Negative realized semivariance |
| `downside_share` | REAL | Yes | Downside share |
| `upside_share` | REAL | Yes | Upside share |
| `semivariance_imbalance` | REAL | Yes | Semivariance imbalance |
| `buy_directional_tail_pressure` | REAL | Yes | Buy directional tail pressure |
| `sell_directional_tail_pressure` | REAL | Yes | Sell directional tail pressure |
| `semivariance_method` | TEXT | No | Semivariance method |
| `semivariance_sample_count` | INTEGER | No | Semivariance sample count |
| `semivariance_validation_status` | TEXT | No | Semivariance validation status |
| `reliability_penalty` | REAL | Yes | Reliability penalty |
| `model_version` | TEXT | No | Model version |
| `feature_version` | TEXT | No | Feature version |
| `formula_version` | TEXT | No | Formula version |
| `threshold_version` | TEXT | No | Threshold version |
| `source_id` | TEXT | Yes | Exact source identifier |
| `source_hash` | TEXT | Yes | Exact persisted source/snapshot hash |
| `snapshot_hash` | TEXT | Yes | Exact immutable symbol snapshot hash |
| `universe_hash` | TEXT | No | Universe hash |
| `evidence_json` | TEXT | No | Versioned detailed evidence/provenance |
| `content_hash` | TEXT | No | Deterministic row content hash |
| `validation_status` | TEXT | No | Evidence validation state |
| `missing_reason` | TEXT | Yes | Explicit reason for unavailable evidence |
| `created_system_time` | TEXT | No | UTC audit timestamp; never market identity |

## `field10_gas_state_shadow`

| Column | SQL type | Nullable | Purpose |
|---|---|---:|---|
| `daily_snapshot_id` | TEXT | No | Immutable parent snapshot key |
| `parent_run_id` | TEXT | No | Exact parent calculation run |
| `child_run_id` | TEXT | Yes | Exact child generation id when present |
| `symbol` | TEXT | No | Canonical instrument |
| `timeframe` | TEXT | No | Canonical H1 timeframe |
| `broker_day` | TEXT | No | Locked broker day |
| `horizon` | INTEGER | No | Independent forecast horizon in hours |
| `completed_broker_candle` | TEXT | No | Locked latest completed H1 candle |
| `state_name` | TEXT | No | State name |
| `previous_state` | REAL | Yes | Previous state |
| `scaled_score` | REAL | Yes | Scaled score |
| `omega` | REAL | Yes | Omega |
| `score_loading` | REAL | Yes | Score loading |
| `persistence` | REAL | Yes | Persistence |
| `update_magnitude` | REAL | Yes | Update magnitude |
| `resulting_state` | REAL | Yes | Resulting state |
| `lower_bound` | REAL | Yes | Lower bound |
| `upper_bound` | REAL | Yes | Upper bound |
| `finite_validation` | INTEGER | No | Finite validation |
| `bound_validation` | INTEGER | No | Bound validation |
| `model_version` | TEXT | No | Model version |
| `feature_version` | TEXT | No | Feature version |
| `formula_version` | TEXT | No | Formula version |
| `threshold_version` | TEXT | No | Threshold version |
| `source_id` | TEXT | Yes | Exact source identifier |
| `source_hash` | TEXT | Yes | Exact persisted source/snapshot hash |
| `snapshot_hash` | TEXT | Yes | Exact immutable symbol snapshot hash |
| `universe_hash` | TEXT | No | Universe hash |
| `evidence_json` | TEXT | No | Versioned detailed evidence/provenance |
| `content_hash` | TEXT | No | Deterministic row content hash |
| `validation_status` | TEXT | No | Evidence validation state |
| `missing_reason` | TEXT | Yes | Explicit reason for unavailable evidence |
| `created_system_time` | TEXT | No | UTC audit timestamp; never market identity |

## `field10_tail_risk_shadow`

| Column | SQL type | Nullable | Purpose |
|---|---|---:|---|
| `daily_snapshot_id` | TEXT | No | Immutable parent snapshot key |
| `parent_run_id` | TEXT | No | Exact parent calculation run |
| `child_run_id` | TEXT | Yes | Exact child generation id when present |
| `symbol` | TEXT | No | Canonical instrument |
| `timeframe` | TEXT | No | Canonical H1 timeframe |
| `broker_day` | TEXT | No | Locked broker day |
| `horizon` | INTEGER | No | Independent forecast horizon in hours |
| `completed_broker_candle` | TEXT | No | Locked latest completed H1 candle |
| `direction` | TEXT | No | Direction |
| `directional_var_95` | REAL | Yes | Directional var 95 |
| `directional_expected_shortfall_95` | REAL | Yes | Directional expected shortfall 95 |
| `es_var_severity_ratio` | REAL | Yes | Es var severity ratio |
| `tail_loss_probability` | REAL | Yes | Tail loss probability |
| `tail_adjusted_expected_value` | REAL | Yes | Tail adjusted expected value |
| `tail_model_coverage` | REAL | Yes | Tail model coverage |
| `tail_exception_count` | INTEGER | Yes | Tail exception count |
| `tail_exception_total` | INTEGER | Yes | Tail exception total |
| `tail_exception_independence` | REAL | Yes | Tail exception independence |
| `joint_var_es_loss` | REAL | Yes | Joint var es loss |
| `tail_backtest_status` | TEXT | No | Tail backtest status |
| `purge_hours` | INTEGER | No | Purge hours |
| `embargo_hours` | INTEGER | No | Embargo hours |
| `model_version` | TEXT | No | Model version |
| `feature_version` | TEXT | No | Feature version |
| `formula_version` | TEXT | No | Formula version |
| `threshold_version` | TEXT | No | Threshold version |
| `source_id` | TEXT | Yes | Exact source identifier |
| `source_hash` | TEXT | Yes | Exact persisted source/snapshot hash |
| `snapshot_hash` | TEXT | Yes | Exact immutable symbol snapshot hash |
| `universe_hash` | TEXT | No | Universe hash |
| `evidence_json` | TEXT | No | Versioned detailed evidence/provenance |
| `content_hash` | TEXT | No | Deterministic row content hash |
| `validation_status` | TEXT | No | Evidence validation state |
| `missing_reason` | TEXT | Yes | Explicit reason for unavailable evidence |
| `created_system_time` | TEXT | No | UTC audit timestamp; never market identity |

## `field10_copula_shadow`

| Column | SQL type | Nullable | Purpose |
|---|---|---:|---|
| `daily_snapshot_id` | TEXT | No | Immutable parent snapshot key |
| `parent_run_id` | TEXT | No | Exact parent calculation run |
| `child_run_id` | TEXT | Yes | Exact child generation id when present |
| `symbol` | TEXT | No | Canonical instrument |
| `timeframe` | TEXT | No | Canonical H1 timeframe |
| `broker_day` | TEXT | No | Locked broker day |
| `peer_symbol` | TEXT | No | Peer symbol |
| `horizon` | INTEGER | No | Independent forecast horizon in hours |
| `completed_broker_candle` | TEXT | No | Locked latest completed H1 candle |
| `ordinary_conditional_dependence` | REAL | Yes | Ordinary conditional dependence |
| `lower_tail_dependence` | REAL | Yes | Lower tail dependence |
| `upper_tail_dependence` | REAL | Yes | Upper tail dependence |
| `joint_adverse_move_probability` | REAL | Yes | Joint adverse move probability |
| `joint_favorable_move_probability` | REAL | Yes | Joint favorable move probability |
| `dependence_regime` | TEXT | Yes | Dependence regime |
| `dependence_instability` | REAL | Yes | Dependence instability |
| `duplicate_currency_exposure` | REAL | Yes | Duplicate currency exposure |
| `currency_leg_detail_json` | TEXT | No | Currency leg detail json |
| `copula_validation_status` | TEXT | No | Copula validation status |
| `sample_count` | INTEGER | No | Sample count |
| `model_version` | TEXT | No | Model version |
| `feature_version` | TEXT | No | Feature version |
| `formula_version` | TEXT | No | Formula version |
| `threshold_version` | TEXT | No | Threshold version |
| `source_id` | TEXT | Yes | Exact source identifier |
| `source_hash` | TEXT | Yes | Exact persisted source/snapshot hash |
| `snapshot_hash` | TEXT | Yes | Exact immutable symbol snapshot hash |
| `universe_hash` | TEXT | No | Universe hash |
| `evidence_json` | TEXT | No | Versioned detailed evidence/provenance |
| `content_hash` | TEXT | No | Deterministic row content hash |
| `validation_status` | TEXT | No | Evidence validation state |
| `missing_reason` | TEXT | Yes | Explicit reason for unavailable evidence |
| `created_system_time` | TEXT | No | UTC audit timestamp; never market identity |

## `field10_connectedness_shadow`

| Column | SQL type | Nullable | Purpose |
|---|---|---:|---|
| `daily_snapshot_id` | TEXT | No | Immutable parent snapshot key |
| `parent_run_id` | TEXT | No | Exact parent calculation run |
| `child_run_id` | TEXT | Yes | Exact child generation id when present |
| `symbol` | TEXT | No | Canonical instrument |
| `timeframe` | TEXT | No | Canonical H1 timeframe |
| `broker_day` | TEXT | No | Locked broker day |
| `horizon` | INTEGER | No | Independent forecast horizon in hours |
| `completed_broker_candle` | TEXT | No | Locked latest completed H1 candle |
| `bad_volatility_received` | REAL | Yes | Bad volatility received |
| `bad_volatility_transmitted` | REAL | Yes | Bad volatility transmitted |
| `good_volatility_received` | REAL | Yes | Good volatility received |
| `good_volatility_transmitted` | REAL | Yes | Good volatility transmitted |
| `net_bad_spillover` | REAL | Yes | Net bad spillover |
| `net_good_spillover` | REAL | Yes | Net good spillover |
| `stress_receiver_status` | TEXT | Yes | Stress receiver status |
| `stress_transmitter_status` | TEXT | Yes | Stress transmitter status |
| `adverse_connectedness_score` | REAL | Yes | Adverse connectedness score |
| `contagion_safety_permission` | TEXT | No | Contagion safety permission |
| `model_version` | TEXT | No | Model version |
| `feature_version` | TEXT | No | Feature version |
| `formula_version` | TEXT | No | Formula version |
| `threshold_version` | TEXT | No | Threshold version |
| `source_id` | TEXT | Yes | Exact source identifier |
| `source_hash` | TEXT | Yes | Exact persisted source/snapshot hash |
| `snapshot_hash` | TEXT | Yes | Exact immutable symbol snapshot hash |
| `universe_hash` | TEXT | No | Universe hash |
| `evidence_json` | TEXT | No | Versioned detailed evidence/provenance |
| `content_hash` | TEXT | No | Deterministic row content hash |
| `validation_status` | TEXT | No | Evidence validation state |
| `missing_reason` | TEXT | Yes | Explicit reason for unavailable evidence |
| `created_system_time` | TEXT | No | UTC audit timestamp; never market identity |

## `field10_frequency_connectedness_shadow`

| Column | SQL type | Nullable | Purpose |
|---|---|---:|---|
| `daily_snapshot_id` | TEXT | No | Immutable parent snapshot key |
| `parent_run_id` | TEXT | No | Exact parent calculation run |
| `child_run_id` | TEXT | Yes | Exact child generation id when present |
| `symbol` | TEXT | No | Canonical instrument |
| `timeframe` | TEXT | No | Canonical H1 timeframe |
| `broker_day` | TEXT | No | Locked broker day |
| `horizon` | INTEGER | No | Independent forecast horizon in hours |
| `completed_broker_candle` | TEXT | No | Locked latest completed H1 candle |
| `connectedness_short` | REAL | Yes | Connectedness short |
| `connectedness_medium` | REAL | Yes | Connectedness medium |
| `connectedness_persistent` | REAL | Yes | Connectedness persistent |
| `mapped_connectedness` | REAL | Yes | Mapped connectedness |
| `mapped_band` | TEXT | No | Mapped band |
| `persistent_shock_share` | REAL | Yes | Persistent shock share |
| `short_horizon_net_transmitter` | REAL | Yes | Short horizon net transmitter |
| `medium_horizon_net_transmitter` | REAL | Yes | Medium horizon net transmitter |
| `persistent_net_transmitter` | REAL | Yes | Persistent net transmitter |
| `horizon_connectedness_status` | TEXT | No | Horizon connectedness status |
| `frequency_mapping_version` | TEXT | No | Frequency mapping version |
| `model_version` | TEXT | No | Model version |
| `feature_version` | TEXT | No | Feature version |
| `formula_version` | TEXT | No | Formula version |
| `threshold_version` | TEXT | No | Threshold version |
| `source_id` | TEXT | Yes | Exact source identifier |
| `source_hash` | TEXT | Yes | Exact persisted source/snapshot hash |
| `snapshot_hash` | TEXT | Yes | Exact immutable symbol snapshot hash |
| `universe_hash` | TEXT | No | Universe hash |
| `evidence_json` | TEXT | No | Versioned detailed evidence/provenance |
| `content_hash` | TEXT | No | Deterministic row content hash |
| `validation_status` | TEXT | No | Evidence validation state |
| `missing_reason` | TEXT | Yes | Explicit reason for unavailable evidence |
| `created_system_time` | TEXT | No | UTC audit timestamp; never market identity |

## `field10_model_confidence_set`

| Column | SQL type | Nullable | Purpose |
|---|---|---:|---|
| `daily_snapshot_id` | TEXT | No | Immutable parent snapshot key |
| `parent_run_id` | TEXT | No | Exact parent calculation run |
| `child_run_id` | TEXT | Yes | Exact child generation id when present |
| `symbol` | TEXT | No | Canonical instrument |
| `timeframe` | TEXT | No | Canonical H1 timeframe |
| `broker_day` | TEXT | No | Locked broker day |
| `horizon` | INTEGER | No | Independent forecast horizon in hours |
| `completed_broker_candle` | TEXT | No | Locked latest completed H1 candle |
| `model_name` | TEXT | No | Model name |
| `loss_function` | TEXT | No | Loss function |
| `mean_loss` | REAL | Yes | Mean loss |
| `mcs_membership` | INTEGER | No | Mcs membership |
| `elimination_round` | INTEGER | Yes | Elimination round |
| `test_statistic` | REAL | Yes | Test statistic |
| `p_value` | REAL | Yes | P value |
| `validation_window` | TEXT | Yes | Validation window |
| `bootstrap_draws` | INTEGER | No | Bootstrap draws |
| `block_length` | INTEGER | No | Block length |
| `model_weight` | REAL | Yes | Model weight |
| `mcs_status` | TEXT | No | Mcs status |
| `candidate_registry_hash` | TEXT | No | Candidate registry hash |
| `model_version` | TEXT | No | Model version |
| `feature_version` | TEXT | No | Feature version |
| `formula_version` | TEXT | No | Formula version |
| `threshold_version` | TEXT | No | Threshold version |
| `source_id` | TEXT | Yes | Exact source identifier |
| `source_hash` | TEXT | Yes | Exact persisted source/snapshot hash |
| `snapshot_hash` | TEXT | Yes | Exact immutable symbol snapshot hash |
| `universe_hash` | TEXT | No | Universe hash |
| `evidence_json` | TEXT | No | Versioned detailed evidence/provenance |
| `content_hash` | TEXT | No | Deterministic row content hash |
| `validation_status` | TEXT | No | Evidence validation state |
| `missing_reason` | TEXT | Yes | Explicit reason for unavailable evidence |
| `created_system_time` | TEXT | No | UTC audit timestamp; never market identity |

## `field10_sample_split_validation`

| Column | SQL type | Nullable | Purpose |
|---|---|---:|---|
| `daily_snapshot_id` | TEXT | No | Immutable parent snapshot key |
| `parent_run_id` | TEXT | No | Exact parent calculation run |
| `child_run_id` | TEXT | Yes | Exact child generation id when present |
| `symbol` | TEXT | No | Canonical instrument |
| `timeframe` | TEXT | No | Canonical H1 timeframe |
| `broker_day` | TEXT | No | Locked broker day |
| `horizon` | INTEGER | No | Independent forecast horizon in hours |
| `completed_broker_candle` | TEXT | No | Locked latest completed H1 candle |
| `model_name` | TEXT | No | Model name |
| `split_id` | TEXT | No | Split id |
| `training_start` | TEXT | Yes | Training start |
| `training_end` | TEXT | Yes | Training end |
| `validation_start` | TEXT | Yes | Validation start |
| `validation_end` | TEXT | Yes | Validation end |
| `test_start` | TEXT | Yes | Test start |
| `test_end` | TEXT | Yes | Test end |
| `out_of_sample_loss` | REAL | Yes | Out of sample loss |
| `calibration_error` | REAL | Yes | Calibration error |
| `coverage_error` | REAL | Yes | Coverage error |
| `net_expected_value_error` | REAL | Yes | Net expected value error |
| `split_rank` | REAL | Yes | Split rank |
| `split_pass` | INTEGER | No | Split pass |
| `purge_hours` | INTEGER | No | Purge hours |
| `embargo_hours` | INTEGER | No | Embargo hours |
| `candidate_registered_before_test` | INTEGER | No | Candidate registered before test |
| `model_version` | TEXT | No | Model version |
| `feature_version` | TEXT | No | Feature version |
| `formula_version` | TEXT | No | Formula version |
| `threshold_version` | TEXT | No | Threshold version |
| `source_id` | TEXT | Yes | Exact source identifier |
| `source_hash` | TEXT | Yes | Exact persisted source/snapshot hash |
| `snapshot_hash` | TEXT | Yes | Exact immutable symbol snapshot hash |
| `universe_hash` | TEXT | No | Universe hash |
| `evidence_json` | TEXT | No | Versioned detailed evidence/provenance |
| `content_hash` | TEXT | No | Deterministic row content hash |
| `validation_status` | TEXT | No | Evidence validation state |
| `missing_reason` | TEXT | Yes | Explicit reason for unavailable evidence |
| `created_system_time` | TEXT | No | UTC audit timestamp; never market identity |

## `field10_rank_components_v2`

| Column | SQL type | Nullable | Purpose |
|---|---|---:|---|
| `daily_snapshot_id` | TEXT | No | Immutable parent snapshot key |
| `parent_run_id` | TEXT | No | Exact parent calculation run |
| `child_run_id` | TEXT | Yes | Exact child generation id when present |
| `symbol` | TEXT | No | Canonical instrument |
| `timeframe` | TEXT | No | Canonical H1 timeframe |
| `broker_day` | TEXT | No | Locked broker day |
| `horizon` | INTEGER | No | Independent forecast horizon in hours |
| `completed_broker_candle` | TEXT | No | Locked latest completed H1 candle |
| `component_name` | TEXT | No | Component name |
| `raw_value` | REAL | Yes | Raw value |
| `normalized_score` | REAL | Yes | Normalized score |
| `configured_weight` | REAL | Yes | Configured weight |
| `duplicate_penalty` | REAL | Yes | Duplicate penalty |
| `effective_weight` | REAL | Yes | Effective weight |
| `weighted_contribution` | REAL | Yes | Weighted contribution |
| `shadow_score` | REAL | Yes | Shadow score |
| `shadow_rank` | INTEGER | Yes | Shadow rank |
| `production_rank` | INTEGER | Yes | Production rank |
| `locked_bias` | TEXT | Yes | Locked bias |
| `entry_permission` | TEXT | Yes | Entry permission |
| `managed_utility_6h` | REAL | Yes | Managed utility 6h |
| `managed_utility_12h` | REAL | Yes | Managed utility 12h |
| `expected_shortfall_95` | REAL | Yes | Expected shortfall 95 |
| `transition_risk_6h` | REAL | Yes | Transition risk 6h |
| `bad_connectedness` | REAL | Yes | Bad connectedness |
| `persistent_connectedness` | REAL | Yes | Persistent connectedness |
| `volatility_safety` | REAL | Yes | Volatility safety |
| `mcs_status` | TEXT | Yes | Mcs status |
| `split_robustness` | REAL | Yes | Split robustness |
| `reliability` | REAL | Yes | Reliability |
| `data_quality` | REAL | Yes | Data quality |
| `rank_evidence_fraction` | REAL | Yes | Rank evidence fraction |
| `promotion_status` | TEXT | No | Promotion status |
| `summary_json` | TEXT | No | Summary json |
| `model_version` | TEXT | No | Model version |
| `feature_version` | TEXT | No | Feature version |
| `formula_version` | TEXT | No | Formula version |
| `threshold_version` | TEXT | No | Threshold version |
| `source_id` | TEXT | Yes | Exact source identifier |
| `source_hash` | TEXT | Yes | Exact persisted source/snapshot hash |
| `snapshot_hash` | TEXT | Yes | Exact immutable symbol snapshot hash |
| `universe_hash` | TEXT | No | Universe hash |
| `evidence_json` | TEXT | No | Versioned detailed evidence/provenance |
| `content_hash` | TEXT | No | Deterministic row content hash |
| `validation_status` | TEXT | No | Evidence validation state |
| `missing_reason` | TEXT | Yes | Explicit reason for unavailable evidence |
| `created_system_time` | TEXT | No | UTC audit timestamp; never market identity |
