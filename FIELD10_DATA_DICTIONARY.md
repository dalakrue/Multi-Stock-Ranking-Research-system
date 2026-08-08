# Field 10 Institutional Data Dictionary

All tables below are children of the immutable parent snapshot unless noted. NULL means unavailable evidence and must be accompanied by status/reason fields where defined.

## `field10_canonical_identity`

| Column | Type | Null allowed | Key |
|---|---|---|---|
| `daily_snapshot_id` | `TEXT` | Yes | PK |
| `run_id` | `TEXT` | No |  |
| `broker_day` | `TEXT` | No |  |
| `broker_timestamp` | `TEXT` | No |  |
| `completed_h1_candle` | `TEXT` | No |  |
| `main_symbol` | `TEXT` | No |  |
| `selected_symbol_universe_json` | `TEXT` | No |  |
| `universe_hash` | `TEXT` | No |  |
| `source_ids_json` | `TEXT` | No |  |
| `snapshot_hashes_json` | `TEXT` | No |  |
| `feature_version` | `TEXT` | No |  |
| `formula_version` | `TEXT` | No |  |
| `threshold_version` | `TEXT` | No |  |
| `model_version` | `TEXT` | No |  |
| `publication_status` | `TEXT` | No |  |
| `content_hash` | `TEXT` | No |  |
| `created_system_time` | `TEXT` | No |  |

## `field10_forecast_ledger`

| Column | Type | Null allowed | Key |
|---|---|---|---|
| `forecast_id` | `TEXT` | Yes | PK |
| `daily_snapshot_id` | `TEXT` | No |  |
| `parent_run_id` | `TEXT` | No |  |
| `child_run_id` | `TEXT` | Yes |  |
| `broker_day` | `TEXT` | No |  |
| `symbol` | `TEXT` | No |  |
| `horizon_hours` | `INTEGER` | No |  |
| `completed_h1_candle` | `TEXT` | No |  |
| `published_at_broker_time` | `TEXT` | No |  |
| `outcome_due_broker_time` | `TEXT` | No |  |
| `raw_direction_probability` | `REAL` | Yes |  |
| `calibrated_direction_probability` | `REAL` | Yes |  |
| `calibration_status` | `TEXT` | No |  |
| `raw_expected_return` | `REAL` | Yes |  |
| `expected_value` | `REAL` | Yes |  |
| `net_expected_value` | `REAL` | Yes |  |
| `risk_adjusted_expected_value` | `REAL` | Yes |  |
| `expected_spread_cost` | `REAL` | Yes |  |
| `expected_slippage_cost` | `REAL` | Yes |  |
| `var_95` | `REAL` | Yes |  |
| `cvar_95` | `REAL` | Yes |  |
| `expected_mfe` | `REAL` | Yes |  |
| `expected_mae` | `REAL` | Yes |  |
| `probability_reach_expected_value` | `REAL` | Yes |  |
| `sample_count` | `INTEGER` | Yes |  |
| `effective_sample_size` | `REAL` | Yes |  |
| `lower_interval` | `REAL` | Yes |  |
| `median_prediction` | `REAL` | Yes |  |
| `upper_interval` | `REAL` | Yes |  |
| `target_coverage` | `REAL` | Yes |  |
| `transition_probability` | `REAL` | Yes |  |
| `entry_permission` | `TEXT` | No |  |
| `formula_version` | `TEXT` | No |  |
| `feature_version` | `TEXT` | No |  |
| `model_version` | `TEXT` | No |  |
| `calibration_version` | `TEXT` | No |  |
| `source_id` | `TEXT` | Yes |  |
| `source_hash` | `TEXT` | Yes |  |
| `content_hash` | `TEXT` | No |  |
| `missing_reason` | `TEXT` | Yes |  |
| `publication_status` | `TEXT` | No |  |
| `created_system_time` | `TEXT` | No |  |

## `field10_outcome_ledger`

| Column | Type | Null allowed | Key |
|---|---|---|---|
| `forecast_id` | `TEXT` | No | PK |
| `settlement_version` | `TEXT` | No | PK |
| `outcome_due_broker_time` | `TEXT` | No |  |
| `settled_at_broker_time` | `TEXT` | No |  |
| `realized_return` | `REAL` | Yes |  |
| `realized_mfe` | `REAL` | Yes |  |
| `realized_mae` | `REAL` | Yes |  |
| `direction_outcome` | `TEXT` | Yes |  |
| `expected_value_reached` | `INTEGER` | Yes |  |
| `transition_occurred` | `INTEGER` | Yes |  |
| `spread_cost` | `REAL` | Yes |  |
| `slippage_cost` | `REAL` | Yes |  |
| `net_realized_return` | `REAL` | Yes |  |
| `outcome_source_id` | `TEXT` | No |  |
| `outcome_source_hash` | `TEXT` | No |  |
| `content_hash` | `TEXT` | No |  |
| `created_system_time` | `TEXT` | No |  |

## `field10_regime_shadow`

| Column | Type | Null allowed | Key |
|---|---|---|---|
| `daily_snapshot_id` | `TEXT` | No | PK |
| `symbol` | `TEXT` | No | PK |
| `selected_regime` | `TEXT` | Yes |  |
| `selected_regime_probability` | `REAL` | Yes |  |
| `second_regime` | `TEXT` | Yes |  |
| `second_regime_probability` | `REAL` | Yes |  |
| `posterior_margin` | `REAL` | Yes |  |
| `regime_entropy` | `REAL` | Yes |  |
| `self_transition_probability` | `REAL` | Yes |  |
| `transition_probability_1h` | `REAL` | Yes |  |
| `transition_probability_6h` | `REAL` | Yes |  |
| `transition_probability_12h` | `REAL` | Yes |  |
| `transition_probability_24h` | `REAL` | Yes |  |
| `regime_age` | `INTEGER` | Yes |  |
| `expected_remaining_duration` | `REAL` | Yes |  |
| `regime_model_version` | `TEXT` | No | PK |
| `validation_status` | `TEXT` | No |  |
| `evidence_sample_size` | `INTEGER` | No |  |
| `missing_reason` | `TEXT` | Yes |  |
| `content_hash` | `TEXT` | No |  |
| `created_system_time` | `TEXT` | No |  |

## `field10_structural_break_shadow`

| Column | Type | Null allowed | Key |
|---|---|---|---|
| `daily_snapshot_id` | `TEXT` | No | PK |
| `symbol` | `TEXT` | No | PK |
| `last_structural_break` | `TEXT` | Yes |  |
| `structural_break_strength` | `REAL` | Yes |  |
| `post_break_h1_count` | `INTEGER` | Yes |  |
| `pre_post_parameter_distance` | `REAL` | Yes |  |
| `changepoint_probability` | `REAL` | Yes |  |
| `modal_run_length` | `INTEGER` | Yes |  |
| `expected_run_length` | `REAL` | Yes |  |
| `run_length_uncertainty` | `REAL` | Yes |  |
| `post_break_validation_permission` | `TEXT` | No |  |
| `break_components_json` | `TEXT` | No |  |
| `model_version` | `TEXT` | No | PK |
| `validation_status` | `TEXT` | No |  |
| `missing_reason` | `TEXT` | Yes |  |
| `content_hash` | `TEXT` | No |  |
| `created_system_time` | `TEXT` | No |  |

## `field10_session_shadow`

| Column | Type | Null allowed | Key |
|---|---|---|---|
| `daily_snapshot_id` | `TEXT` | No | PK |
| `symbol` | `TEXT` | No | PK |
| `session_name` | `TEXT` | No | PK |
| `session_rank` | `INTEGER` | Yes |  |
| `session_normalized_volatility` | `REAL` | Yes |  |
| `volatility_percentile` | `REAL` | Yes |  |
| `abnormal_activity` | `REAL` | Yes |  |
| `normalized_tick_volume` | `REAL` | Yes |  |
| `normalized_spread` | `REAL` | Yes |  |
| `expected_movement` | `REAL` | Yes |  |
| `net_expected_value` | `REAL` | Yes |  |
| `cvar_95` | `REAL` | Yes |  |
| `directional_hit_rate` | `REAL` | Yes |  |
| `regime_compatibility` | `REAL` | Yes |  |
| `entry_permission` | `TEXT` | No |  |
| `sample_count` | `INTEGER` | No |  |
| `data_completeness` | `REAL` | Yes |  |
| `current_active_session` | `INTEGER` | No |  |
| `next_session` | `INTEGER` | No |  |
| `session_transition_risk` | `REAL` | Yes |  |
| `formula_version` | `TEXT` | No | PK |
| `validation_status` | `TEXT` | No |  |
| `missing_reason` | `TEXT` | Yes |  |
| `content_hash` | `TEXT` | No |  |
| `created_system_time` | `TEXT` | No |  |

## `field10_calibration_shadow`

| Column | Type | Null allowed | Key |
|---|---|---|---|
| `daily_snapshot_id` | `TEXT` | No | PK |
| `symbol` | `TEXT` | No | PK |
| `horizon_hours` | `INTEGER` | No | PK |
| `target_name` | `TEXT` | No | PK |
| `raw_probability` | `REAL` | Yes |  |
| `calibrated_probability` | `REAL` | Yes |  |
| `selected_method` | `TEXT` | Yes |  |
| `calibration_status` | `TEXT` | No |  |
| `brier_score` | `REAL` | Yes |  |
| `brier_skill_score` | `REAL` | Yes |  |
| `baseline_brier_score` | `REAL` | Yes |  |
| `log_loss` | `REAL` | Yes |  |
| `expected_calibration_error` | `REAL` | Yes |  |
| `maximum_calibration_error` | `REAL` | Yes |  |
| `reliability_component` | `REAL` | Yes |  |
| `resolution_component` | `REAL` | Yes |  |
| `calibration_sample_count` | `INTEGER` | No |  |
| `calibration_freshness_hours` | `REAL` | Yes |  |
| `purging_hours` | `INTEGER` | No |  |
| `embargo_hours` | `INTEGER` | No |  |
| `training_interval` | `TEXT` | Yes |  |
| `validation_interval` | `TEXT` | Yes |  |
| `test_interval` | `TEXT` | Yes |  |
| `calibration_version` | `TEXT` | No | PK |
| `validation_status` | `TEXT` | No |  |
| `missing_reason` | `TEXT` | Yes |  |
| `metrics_json` | `TEXT` | No |  |
| `content_hash` | `TEXT` | No |  |
| `created_system_time` | `TEXT` | No |  |

## `field10_conformal_shadow`

| Column | Type | Null allowed | Key |
|---|---|---|---|
| `daily_snapshot_id` | `TEXT` | No | PK |
| `symbol` | `TEXT` | No | PK |
| `horizon_hours` | `INTEGER` | No | PK |
| `regime_key` | `TEXT` | No | PK |
| `session_key` | `TEXT` | No | PK |
| `lower_conformal_return` | `REAL` | Yes |  |
| `median_expected_return` | `REAL` | Yes |  |
| `upper_conformal_return` | `REAL` | Yes |  |
| `interval_width` | `REAL` | Yes |  |
| `target_coverage` | `REAL` | Yes |  |
| `rolling_realized_coverage` | `REAL` | Yes |  |
| `lower_tail_miss_rate` | `REAL` | Yes |  |
| `upper_tail_miss_rate` | `REAL` | Yes |  |
| `adaptive_alpha` | `REAL` | Yes |  |
| `coverage_error` | `REAL` | Yes |  |
| `distribution_shift_status` | `TEXT` | No |  |
| `calibration_sample_count` | `INTEGER` | No |  |
| `conformal_version` | `TEXT` | No | PK |
| `validation_status` | `TEXT` | No |  |
| `missing_reason` | `TEXT` | Yes |  |
| `content_hash` | `TEXT` | No |  |
| `created_system_time` | `TEXT` | No |  |

## `field10_dependence_shadow`

| Column | Type | Null allowed | Key |
|---|---|---|---|
| `daily_snapshot_id` | `TEXT` | No | PK |
| `symbol` | `TEXT` | No | PK |
| `correlation_cluster` | `TEXT` | Yes |  |
| `cluster_concentration` | `REAL` | Yes |  |
| `duplicate_exposure_penalty` | `REAL` | Yes |  |
| `marginal_diversification_value` | `REAL` | Yes |  |
| `usd_exposure` | `REAL` | Yes |  |
| `eur_exposure` | `REAL` | Yes |  |
| `common_factor_exposure` | `REAL` | Yes |  |
| `covariance_method` | `TEXT` | No | PK |
| `sample_count` | `INTEGER` | No |  |
| `validation_status` | `TEXT` | No |  |
| `missing_reason` | `TEXT` | Yes |  |
| `evidence_json` | `TEXT` | No |  |
| `content_hash` | `TEXT` | No |  |
| `created_system_time` | `TEXT` | No |  |

## `field10_event_intensity_shadow`

| Column | Type | Null allowed | Key |
|---|---|---|---|
| `daily_snapshot_id` | `TEXT` | No | PK |
| `symbol` | `TEXT` | No | PK |
| `event_family` | `TEXT` | No | PK |
| `baseline_intensity` | `REAL` | Yes |  |
| `current_excitation` | `REAL` | Yes |  |
| `decay` | `REAL` | Yes |  |
| `event_cluster_state` | `TEXT` | Yes |  |
| `estimated_remaining_impact` | `REAL` | Yes |  |
| `event_transition_warning` | `TEXT` | Yes |  |
| `model_version` | `TEXT` | No | PK |
| `validation_status` | `TEXT` | No |  |
| `sample_count` | `INTEGER` | No |  |
| `missing_reason` | `TEXT` | Yes |  |
| `content_hash` | `TEXT` | No |  |
| `created_system_time` | `TEXT` | No |  |

## `field10_reliability_shadow`

| Column | Type | Null allowed | Key |
|---|---|---|---|
| `daily_snapshot_id` | `TEXT` | No | PK |
| `symbol` | `TEXT` | No | PK |
| `calibration_reliability` | `REAL` | Yes |  |
| `conformal_coverage_reliability` | `REAL` | Yes |  |
| `sample_adequacy` | `REAL` | Yes |  |
| `data_completeness` | `REAL` | Yes |  |
| `source_identity_reliability` | `REAL` | Yes |  |
| `regime_stability` | `REAL` | Yes |  |
| `structural_stability` | `REAL` | Yes |  |
| `rank_stability` | `REAL` | Yes |  |
| `feature_availability` | `REAL` | Yes |  |
| `outcome_settlement_completeness` | `REAL` | Yes |  |
| `aggregate_reliability` | `REAL` | Yes |  |
| `reliability_status` | `TEXT` | No |  |
| `principal_reliability_weakness` | `TEXT` | Yes |  |
| `reliability_explanation` | `TEXT` | No |  |
| `effective_sample_size` | `REAL` | Yes |  |
| `component_weights_json` | `TEXT` | No |  |
| `reliability_version` | `TEXT` | No | PK |
| `validation_status` | `TEXT` | No |  |
| `content_hash` | `TEXT` | No |  |
| `created_system_time` | `TEXT` | No |  |

## `field10_rank_confidence_shadow`

| Column | Type | Null allowed | Key |
|---|---|---|---|
| `daily_snapshot_id` | `TEXT` | No | PK |
| `symbol` | `TEXT` | No | PK |
| `original_rank` | `INTEGER` | Yes |  |
| `candidate_utility` | `REAL` | Yes |  |
| `probability_rank_1` | `REAL` | Yes |  |
| `probability_rank_le_4` | `REAL` | Yes |  |
| `median_rank` | `REAL` | Yes |  |
| `rank_percentile_low` | `REAL` | Yes |  |
| `rank_percentile_high` | `REAL` | Yes |  |
| `rank_instability` | `REAL` | Yes |  |
| `score_gap_to_next_symbol` | `REAL` | Yes |  |
| `bootstrap_draws` | `INTEGER` | No |  |
| `block_length` | `INTEGER` | No |  |
| `bootstrap_seed` | `TEXT` | No |  |
| `validation_status` | `TEXT` | No |  |
| `missing_reason` | `TEXT` | Yes |  |
| `model_version` | `TEXT` | No | PK |
| `content_hash` | `TEXT` | No |  |
| `created_system_time` | `TEXT` | No |  |

## `field10_shadow_publication_audit`

| Column | Type | Null allowed | Key |
|---|---|---|---|
| `audit_id` | `TEXT` | Yes | PK |
| `daily_snapshot_id` | `TEXT` | Yes |  |
| `action` | `TEXT` | No |  |
| `status` | `TEXT` | No |  |
| `details_json` | `TEXT` | No |  |
| `content_hash` | `TEXT` | No |  |
| `created_system_time` | `TEXT` | No |  |
