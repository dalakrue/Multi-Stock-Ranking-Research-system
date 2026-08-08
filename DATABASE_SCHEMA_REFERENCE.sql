-- FIELD 10 DATABASE SCHEMA REFERENCE
-- Generated from the migrated deployment database.
PRAGMA foreign_keys=ON;

-- TABLE: field10_calibration_shadow
CREATE TABLE field10_calibration_shadow (
    daily_snapshot_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    horizon_hours INTEGER NOT NULL,
    target_name TEXT NOT NULL,
    raw_probability REAL,
    calibrated_probability REAL,
    selected_method TEXT,
    calibration_status TEXT NOT NULL,
    brier_score REAL,
    brier_skill_score REAL,
    baseline_brier_score REAL,
    log_loss REAL,
    expected_calibration_error REAL,
    maximum_calibration_error REAL,
    reliability_component REAL,
    resolution_component REAL,
    calibration_sample_count INTEGER NOT NULL,
    calibration_freshness_hours REAL,
    purging_hours INTEGER NOT NULL,
    embargo_hours INTEGER NOT NULL,
    training_interval TEXT,
    validation_interval TEXT,
    test_interval TEXT,
    calibration_version TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    missing_reason TEXT,
    metrics_json TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    created_system_time TEXT NOT NULL,
    PRIMARY KEY(daily_snapshot_id,symbol,horizon_hours,target_name,calibration_version),
    FOREIGN KEY(daily_snapshot_id,symbol)
      REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id,symbol)
);

-- TABLE: field10_canonical_identity
CREATE TABLE field10_canonical_identity (
    daily_snapshot_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    broker_day TEXT NOT NULL,
    broker_timestamp TEXT NOT NULL,
    completed_h1_candle TEXT NOT NULL,
    main_symbol TEXT NOT NULL,
    selected_symbol_universe_json TEXT NOT NULL,
    universe_hash TEXT NOT NULL,
    source_ids_json TEXT NOT NULL,
    snapshot_hashes_json TEXT NOT NULL,
    feature_version TEXT NOT NULL,
    formula_version TEXT NOT NULL,
    threshold_version TEXT NOT NULL,
    model_version TEXT NOT NULL,
    publication_status TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    created_system_time TEXT NOT NULL,
    FOREIGN KEY(daily_snapshot_id) REFERENCES field10_daily_snapshot(daily_snapshot_id)
);

-- TABLE: field10_conformal_shadow
CREATE TABLE field10_conformal_shadow (
    daily_snapshot_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    horizon_hours INTEGER NOT NULL,
    regime_key TEXT NOT NULL,
    session_key TEXT NOT NULL,
    lower_conformal_return REAL,
    median_expected_return REAL,
    upper_conformal_return REAL,
    interval_width REAL,
    target_coverage REAL,
    rolling_realized_coverage REAL,
    lower_tail_miss_rate REAL,
    upper_tail_miss_rate REAL,
    adaptive_alpha REAL,
    coverage_error REAL,
    distribution_shift_status TEXT NOT NULL,
    calibration_sample_count INTEGER NOT NULL,
    conformal_version TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    missing_reason TEXT,
    content_hash TEXT NOT NULL UNIQUE,
    created_system_time TEXT NOT NULL,
    PRIMARY KEY(daily_snapshot_id,symbol,horizon_hours,regime_key,session_key,conformal_version),
    FOREIGN KEY(daily_snapshot_id,symbol)
      REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id,symbol)
);

-- TABLE: field10_conformal_state
CREATE TABLE field10_conformal_state (
                symbol TEXT NOT NULL,
                horizon INTEGER NOT NULL,
                session TEXT NOT NULL,
                target_coverage REAL,
                realized_coverage REAL,
                coverage_status TEXT,
                interval_width REAL,
                sample_count INTEGER NOT NULL DEFAULT 0,
                last_broker_timestamp TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(symbol, horizon, session)
            );

-- TABLE: field10_crowd_final_migration_audit
CREATE TABLE field10_crowd_final_migration_audit (
                migration_id TEXT PRIMARY KEY,
                migration_version TEXT NOT NULL,
                status TEXT NOT NULL,
                details_json TEXT NOT NULL,
                applied_system_time TEXT NOT NULL
            );

-- TABLE: field10_crowd_psychology_outcome
CREATE TABLE field10_crowd_psychology_outcome (
                outcome_id TEXT PRIMARY KEY,
                daily_snapshot_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                prediction_content_hash TEXT NOT NULL,
                horizon_hours INTEGER NOT NULL,
                realized_return_pct REAL,
                realized_direction TEXT,
                direction_correct INTEGER,
                realized_mfe_pct REAL,
                realized_mae_pct REAL,
                evaluation_json TEXT NOT NULL,
                outcome_hash TEXT NOT NULL UNIQUE,
                settled_broker_time TEXT NOT NULL,
                created_system_time TEXT NOT NULL,
                FOREIGN KEY(daily_snapshot_id,symbol) REFERENCES field10_daily_crowd_psychology_rank(daily_snapshot_id,symbol)
            );

-- TABLE: field10_daily_crowd_psychology_rank
CREATE TABLE "field10_daily_crowd_psychology_rank" ("daily_snapshot_id" TEXT NOT NULL,"run_id" TEXT,"parent_run_id" TEXT NOT NULL,"broker_day" TEXT NOT NULL,"completed_h1_candle" TEXT NOT NULL,"universe_hash" TEXT NOT NULL,"symbol" TEXT NOT NULL,"source_identity" TEXT,"snapshot_hash" TEXT,"crowd_rank" INTEGER,"crowd_state" TEXT NOT NULL,"crowd_direction" TEXT NOT NULL,"crowd_psychology_score" REAL,"crowd_confidence" REAL,"evidence_completeness" REAL,"data_freshness" TEXT,"calculation_status" TEXT NOT NULL,"herding_pressure" REAL,"fomo_pressure" REAL,"panic_pressure" REAL,"greed_pressure" REAL,"fear_pressure" REAL,"capitulation_probability" REAL,"crowd_exhaustion_probability" REAL,"contrarian_reversal_probability" REAL,"retail_trap_probability" REAL,"stop_hunt_vulnerability" REAL,"late_crowd_entry_risk" REAL,"crowd_momentum_1h" REAL,"crowd_momentum_6h" REAL,"crowd_momentum_12h" REAL,"crowd_momentum_24h" REAL,"price_momentum_1h" REAL,"price_momentum_6h" REAL,"sentiment_price_divergence_1h" REAL,"sentiment_price_divergence_6h" REAL,"sentiment_price_divergence_12h" REAL,"sentiment_price_divergence_24h" REAL,"divergence_direction" TEXT,"divergence_severity" REAL,"divergence_persistence" REAL,"retail_long_percentage" REAL,"retail_short_percentage" REAL,"retail_positioning_bias" TEXT,"positioning_extreme_percentile" REAL,"positioning_change_1h" REAL,"positioning_change_6h" REAL,"flow_proxy_bias" TEXT,"flow_proxy_strength" REAL,"signed_candle_pressure" REAL,"abnormal_tick_volume_pressure" REAL,"spread_stress_pressure" REAL,"liquidity_withdrawal_risk" REAL,"true_flow_data_available" INTEGER NOT NULL DEFAULT 0,"positioning_data_available" INTEGER NOT NULL DEFAULT 0,"volatility_fear_index" REAL,"volatility_expansion_score" REAL,"volatility_compression_score" REAL,"panic_volatility_probability" REAL,"calm_complacency_probability" REAL,"session_normalized_volatility" REAL,"volatility_regime" TEXT,"volatility_transition_risk" REAL,"finnhub_news_sentiment_contribution" REAL,"high_impact_event_contribution" REAL,"event_absorption_contribution" REAL,"social_sentiment_contribution" REAL,"social_sentiment_momentum" REAL,"social_evidence_source" TEXT,"news_social_agreement" TEXT,"news_crowd_conflict" TEXT,"active_event_risk" TEXT,"base_currency_crowd_effect" REAL,"quote_currency_crowd_effect" REAL,"pair_crowd_effect" REAL,"base_quote_agreement" REAL,"currency_basket_crowd_score" REAL,"cross_symbol_crowd_agreement" REAL,"usd_crowd_regime" TEXT,"eur_crowd_regime" TEXT,"pair_specific_crowd_reliability" REAL,"crowd_less_risky_bias" TEXT,"crowd_entry_permission" TEXT,"crowd_hold_permission" TEXT,"crowd_reversal_warning" TEXT,"crowd_transition_risk_1h" REAL,"crowd_transition_risk_6h" REAL,"crowd_transition_risk_12h" REAL,"crowd_transition_risk_24h" REAL,"crowd_expected_value_1h" REAL,"crowd_expected_value_6h" REAL,"crowd_expected_value_12h" REAL,"crowd_expected_value_24h" REAL,"crowd_risk_adjusted_ev_1h" REAL,"crowd_risk_adjusted_ev_6h" REAL,"crowd_risk_adjusted_ev_12h" REAL,"crowd_risk_adjusted_ev_24h" REAL,"crowd_cvar_95" REAL,"crowd_explanation" TEXT,"crowd_no_trade_reason" TEXT,"model_version" TEXT NOT NULL,"formula_version" TEXT NOT NULL,"threshold_registry_version" TEXT NOT NULL,"validation_status" TEXT NOT NULL,"evidence_sample_size" INTEGER NOT NULL DEFAULT 0,"value_unit" TEXT NOT NULL,"component_json" TEXT NOT NULL,"penalty_json" TEXT NOT NULL,"source_provenance_json" TEXT NOT NULL,"source_hashes_json" TEXT NOT NULL,"publication_status" TEXT NOT NULL,"content_hash" TEXT NOT NULL,"created_broker_time" TEXT NOT NULL,"created_system_time" TEXT NOT NULL,PRIMARY KEY("daily_snapshot_id","symbol"),FOREIGN KEY("daily_snapshot_id","symbol") REFERENCES field10_daily_snapshot_symbol("daily_snapshot_id","symbol"));

-- TABLE: field10_daily_final_multi_symbol_rank
CREATE TABLE "field10_daily_final_multi_symbol_rank" ("daily_snapshot_id" TEXT NOT NULL,"run_id" TEXT,"parent_run_id" TEXT NOT NULL,"broker_day" TEXT NOT NULL,"completed_h1_candle" TEXT NOT NULL,"universe_hash" TEXT NOT NULL,"symbol" TEXT NOT NULL,"source_identity" TEXT,"snapshot_hash" TEXT,"final_rank" INTEGER,"rank_icon" TEXT,"final_score" REAL,"previous_final_rank" INTEGER,"rank_change" INTEGER,"final_lock_status" TEXT NOT NULL,"locked_at_broker_time" TEXT NOT NULL,"locked_until_broker_time" TEXT NOT NULL,"final_publication_hash" TEXT NOT NULL,"technical_fundamental_rank" INTEGER,"technical_fundamental_score" REAL,"technical_fundamental_bias" TEXT,"best_session_rank" INTEGER,"best_session_1" TEXT,"best_session_2" TEXT,"session_score" REAL,"session_bias" TEXT,"news_sentiment_rank" INTEGER,"news_sentiment_bias" TEXT,"event_risk_permission" TEXT,"impact_remaining_percentage" REAL,"absorption_percentage" REAL,"crowd_psychology_rank" INTEGER,"crowd_psychology_score" REAL,"crowd_state" TEXT,"crowd_direction" TEXT,"crowd_confidence" REAL,"final_less_risky_bias_to_hold" TEXT NOT NULL,"final_less_risky_bias_confidence" REAL,"final_bias_agreement" REAL,"final_bias_conflict" REAL,"final_hold_permission" TEXT,"final_entry_permission" TEXT,"final_exit_risk_warning" TEXT,"bias_source_majority" TEXT,"strongest_supporting_source" TEXT,"strongest_conflicting_source" TEXT,"no_trade_reason" TEXT,"final_explanation" TEXT,"final_transition_bias_risk_1h" REAL,"final_transition_bias_risk_6h" REAL,"final_transition_bias_risk_12h" REAL,"final_transition_bias_risk_24h" REAL,"transition_direction_1h" TEXT,"transition_direction_6h" TEXT,"transition_direction_12h" TEXT,"transition_direction_24h" TEXT,"probability_bias_remains_1h" REAL,"probability_bias_remains_6h" REAL,"probability_bias_remains_12h" REAL,"probability_bias_remains_24h" REAL,"probability_bias_reverses_1h" REAL,"probability_bias_reverses_6h" REAL,"probability_bias_reverses_12h" REAL,"probability_bias_reverses_24h" REAL,"transition_risk_confidence" REAL,"main_transition_risk_driver" TEXT,"regime_transition_contribution" REAL,"crowd_transition_contribution" REAL,"news_transition_contribution" REAL,"session_transition_contribution" REAL,"expected_value_1h" REAL,"expected_value_6h" REAL,"expected_value_12h" REAL,"expected_value_24h" REAL,"risk_adjusted_expected_value_1h" REAL,"risk_adjusted_expected_value_6h" REAL,"risk_adjusted_expected_value_12h" REAL,"risk_adjusted_expected_value_24h" REAL,"expected_return_1h" REAL,"expected_return_6h" REAL,"expected_return_12h" REAL,"expected_return_24h" REAL,"probability_of_profit_1h" REAL,"probability_of_profit_6h" REAL,"probability_of_profit_12h" REAL,"probability_of_profit_24h" REAL,"probability_reach_expected_value_1h" REAL,"probability_reach_expected_value_6h" REAL,"probability_reach_expected_value_12h" REAL,"probability_reach_expected_value_24h" REAL,"expected_mfe_1h" REAL,"expected_mfe_6h" REAL,"expected_mfe_12h" REAL,"expected_mfe_24h" REAL,"expected_mae_1h" REAL,"expected_mae_6h" REAL,"expected_mae_12h" REAL,"expected_mae_24h" REAL,"cvar_95_1h" REAL,"cvar_95_6h" REAL,"cvar_95_12h" REAL,"cvar_95_24h" REAL,"expected_spread_cost" REAL,"expected_slippage_cost" REAL,"net_expected_value_after_cost" REAL,"value_unit" TEXT NOT NULL,"evidence_lineage_json" TEXT NOT NULL,"four_source_row_references_json" TEXT NOT NULL,"four_source_hashes_json" TEXT NOT NULL,"horizon_probability_json" TEXT NOT NULL,"horizon_ev_component_json" TEXT NOT NULL,"transition_risk_component_json" TEXT NOT NULL,"fusion_component_json" TEXT NOT NULL,"penalty_json" TEXT NOT NULL,"formula_version" TEXT NOT NULL,"model_version" TEXT NOT NULL,"threshold_registry_version" TEXT NOT NULL,"validation_status" TEXT NOT NULL,"lock_status" TEXT NOT NULL,"publication_status" TEXT NOT NULL,"content_hash" TEXT NOT NULL,"created_broker_time" TEXT NOT NULL,"created_system_time" TEXT NOT NULL,PRIMARY KEY("daily_snapshot_id","symbol"),FOREIGN KEY("daily_snapshot_id","symbol") REFERENCES field10_daily_snapshot_symbol("daily_snapshot_id","symbol"));

-- TABLE: field10_daily_higher_lock
CREATE TABLE field10_daily_higher_lock (
                broker_day TEXT NOT NULL,
                symbol TEXT NOT NULL,
                rank INTEGER,
                higher_standard_regime TEXT NOT NULL,
                higher_standard_bias TEXT,
                less_risky_bias TEXT NOT NULL,
                data_quality_grade TEXT NOT NULL,
                data_quality_score REAL NOT NULL,
                higher_reliability REAL,
                higher_transition_risk REAL,
                transition_risk_24h REAL,
                expected_return_12h REAL,
                higher_alpha REAL,
                higher_delta REAL,
                sample_count INTEGER,
                current_session TEXT,
                session_priority REAL,
                average_spread REAL,
                spread_quality TEXT,
                uncertainty REAL,
                error_percentage REAL,
                trade_permission TEXT,
                final_action TEXT,
                rank_score REAL,
                rank_reason TEXT,
                lock_status TEXT NOT NULL,
                locked_at_broker_time TEXT NOT NULL,
                last_reviewed_broker_time TEXT NOT NULL,
                next_review_broker_time TEXT,
                parent_run_id TEXT NOT NULL,
                run_id TEXT,
                source_id TEXT, expected_return_24h REAL, expected_return_36h REAL, transition_risk_6h REAL, expected_value_6h REAL, risk_adjusted_expected_value_6h REAL, probability_profit_1h REAL, probability_profit_6h REAL, probability_profit_12h REAL, probability_reach_ev_1h REAL, probability_reach_ev_6h REAL, probability_reach_ev_12h REAL, ev_target_1h REAL, ev_target_6h REAL, ev_target_12h REAL, tick_volume_12h REAL, volume_12h_z REAL, volume_source TEXT, ev_model_version TEXT, probability_calibration_status TEXT, unexpected_situation_status TEXT, unexpected_situation_severity REAL, validation_permission TEXT, evidence_sample_size INTEGER, metric_provenance_json TEXT, migration_version TEXT,
                PRIMARY KEY(broker_day, symbol)
            );

-- TABLE: field10_daily_news_event_rank
CREATE TABLE field10_daily_news_event_rank (
                daily_snapshot_id TEXT NOT NULL,
                broker_day TEXT NOT NULL,
                symbol TEXT NOT NULL,
                event_id TEXT NOT NULL,
                news_rank INTEGER,
                sentiment_bias TEXT,
                sentiment_probability REAL,
                base_currency_effect TEXT,
                quote_currency_effect TEXT,
                pair_direction_effect TEXT,
                headline TEXT NOT NULL,
                event_type TEXT,
                affected_currency TEXT,
                source TEXT,
                source_quality REAL,
                release_utc TEXT,
                release_broker_time TEXT,
                current_broker_time TEXT,
                event_age_minutes REAL,
                scheduled_status TEXT,
                actual_value TEXT,
                consensus_value TEXT,
                surprise_score REAL,
                entity_relevance REAL,
                pair_relevance REAL,
                novelty_score REAL,
                duplicate_group TEXT,
                finbert_tone TEXT,
                fallback_tone TEXT,
                sentiment_agreement TEXT,
                abnormal_return REAL,
                cumulative_abnormal_return REAL,
                abnormal_volatility REAL,
                abnormal_tick_volume REAL,
                event_response_percentile REAL,
                event_intensity REAL,
                estimated_half_life_minutes REAL,
                expected_impact_time_left_minutes REAL,
                impact_remaining_pct REAL,
                absorption_pct REAL,
                absorption_status TEXT,
                next_1h_shock_probability REAL,
                reversal_risk REAL,
                event_risk_permission TEXT,
                evidence_sample_size INTEGER NOT NULL DEFAULT 1,
                model_version TEXT NOT NULL,
                formula_version TEXT NOT NULL,
                threshold_version TEXT NOT NULL,
                data_provider TEXT NOT NULL,
                provider_authentication TEXT NOT NULL,
                timestamp_provenance TEXT NOT NULL,
                provider_article_id TEXT,
                normalized_url TEXT,
                content_hash TEXT NOT NULL,
                row_json TEXT NOT NULL,
                publication_status TEXT NOT NULL,
                stored_at TEXT NOT NULL,
                PRIMARY KEY(daily_snapshot_id, symbol, event_id),
                FOREIGN KEY(daily_snapshot_id, symbol)
                    REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id, symbol)
            );

-- TABLE: field10_daily_outcome
CREATE TABLE field10_daily_outcome (
                daily_snapshot_id TEXT NOT NULL,
                broker_day TEXT NOT NULL,
                symbol TEXT NOT NULL,
                settlement_status TEXT NOT NULL,
                settled_at_broker_time TEXT,
                actual_1h_direction TEXT,
                actual_3h_direction TEXT,
                actual_6h_direction TEXT,
                day_close_direction TEXT,
                correct_1h INTEGER,
                correct_3h INTEGER,
                correct_6h INTEGER,
                mfe REAL,
                mae REAL,
                spread_adjusted_outcome REAL,
                slippage_adjusted_outcome REAL,
                calibration_error REAL,
                outcome_hash TEXT,
                outcome_json TEXT NOT NULL,
                PRIMARY KEY(daily_snapshot_id, symbol),
                FOREIGN KEY(daily_snapshot_id, symbol)
                    REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id, symbol)
            );

-- TABLE: field10_daily_safety_event
CREATE TABLE field10_daily_safety_event (
                event_id TEXT PRIMARY KEY,
                daily_snapshot_id TEXT,
                broker_day TEXT NOT NULL,
                symbol TEXT NOT NULL,
                observed_at_broker_time TEXT NOT NULL,
                safety_veto TEXT NOT NULL,
                reasons_json TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                event_hash TEXT NOT NULL UNIQUE,
                FOREIGN KEY(daily_snapshot_id) REFERENCES field10_daily_snapshot(daily_snapshot_id)
            );

-- TABLE: field10_daily_score_component
CREATE TABLE field10_daily_score_component (
                daily_snapshot_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                component_name TEXT NOT NULL,
                component_value REAL,
                configured_weight REAL NOT NULL,
                available INTEGER NOT NULL,
                critical INTEGER NOT NULL,
                contribution REAL,
                status TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                PRIMARY KEY(daily_snapshot_id, symbol, component_name),
                FOREIGN KEY(daily_snapshot_id, symbol)
                    REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id, symbol)
            );

-- TABLE: field10_daily_session_entry_map
CREATE TABLE field10_daily_session_entry_map (
                daily_snapshot_id TEXT NOT NULL,
                broker_day TEXT NOT NULL,
                completed_h1_candle TEXT NOT NULL,
                parent_run_id TEXT NOT NULL,
                run_id TEXT,
                universe_hash TEXT NOT NULL,
                symbol TEXT NOT NULL,
                session_name TEXT NOT NULL,
                session_rank INTEGER,
                session_score REAL,
                session_bias TEXT,
                entry_permission TEXT,
                sample_size INTEGER NOT NULL DEFAULT 0,
                mean_return_1h REAL,
                median_return_1h REAL,
                win_rate REAL,
                session_volatility REAL,
                source_row_id TEXT NOT NULL,
                source_hash TEXT NOT NULL,
                snapshot_hash TEXT,
                formula_version TEXT NOT NULL,
                model_version TEXT NOT NULL,
                publication_status TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_broker_time TEXT NOT NULL,
                created_system_time TEXT NOT NULL,
                PRIMARY KEY(daily_snapshot_id,symbol,session_name),
                FOREIGN KEY(daily_snapshot_id,symbol) REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id,symbol)
            );

-- TABLE: field10_daily_snapshot
CREATE TABLE field10_daily_snapshot (
                daily_snapshot_id TEXT PRIMARY KEY,
                broker_day TEXT NOT NULL UNIQUE,
                cutoff_broker_time TEXT NOT NULL,
                latest_completed_h1 TEXT NOT NULL,
                ordered_symbol_universe_json TEXT NOT NULL,
                universe_hash TEXT NOT NULL,
                main_symbol TEXT NOT NULL,
                secondary_symbols_json TEXT NOT NULL,
                provider_aliases_json TEXT NOT NULL,
                symbol_count INTEGER NOT NULL,
                parent_run_id TEXT NOT NULL,
                child_run_ids_json TEXT NOT NULL,
                canonical_run_ids_json TEXT NOT NULL,
                source_ids_json TEXT NOT NULL,
                snapshot_hashes_json TEXT NOT NULL,
                model_version TEXT NOT NULL,
                formula_version TEXT NOT NULL,
                threshold_version TEXT NOT NULL,
                content_hash TEXT NOT NULL UNIQUE,
                publication_status TEXT NOT NULL,
                published_at_broker_time TEXT NOT NULL,
                locked_until_broker_time TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at_broker_time TEXT NOT NULL
            );

-- TABLE: field10_daily_snapshot_audit
CREATE TABLE field10_daily_snapshot_audit (
                audit_id TEXT PRIMARY KEY,
                daily_snapshot_id TEXT,
                broker_day TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                observed_at_broker_time TEXT NOT NULL,
                details_json TEXT NOT NULL,
                audit_hash TEXT NOT NULL UNIQUE,
                FOREIGN KEY(daily_snapshot_id) REFERENCES field10_daily_snapshot(daily_snapshot_id)
            );

-- TABLE: field10_daily_snapshot_symbol
CREATE TABLE field10_daily_snapshot_symbol (
                daily_snapshot_id TEXT NOT NULL,
                broker_day TEXT NOT NULL,
                symbol TEXT NOT NULL,
                role TEXT NOT NULL,
                daily_rank INTEGER,
                daily_grade TEXT NOT NULL,
                institutional_score REAL,
                existing_rank_score REAL,
                eligibility_status TEXT NOT NULL,
                trade_permission TEXT NOT NULL,
                stable_daily_bias TEXT,
                less_risky_bias TEXT,
                higher_standard_regime TEXT,
                sample_count INTEGER NOT NULL DEFAULT 0,
                sample_complete_status TEXT NOT NULL,
                completed_candle TEXT,
                canonical_run_id TEXT,
                source_id TEXT,
                snapshot_hash TEXT,
                correlation_cluster TEXT,
                content_hash TEXT NOT NULL,
                row_json TEXT NOT NULL,
                score_explanation_json TEXT NOT NULL, transition_risk_24h REAL, expected_return_12h REAL, expected_return_24h REAL, expected_return_36h REAL, "transition_risk_6h" REAL, "expected_value_6h" REAL, "risk_adjusted_expected_value_6h" REAL, "probability_profit_1h" REAL, "probability_profit_6h" REAL, "probability_profit_12h" REAL, "probability_reach_ev_1h" REAL, "probability_reach_ev_6h" REAL, "probability_reach_ev_12h" REAL, "ev_target_1h" REAL, "ev_target_6h" REAL, "ev_target_12h" REAL, "tick_volume_12h" REAL, "volume_12h_z" REAL, "volume_source" TEXT, "ev_model_version" TEXT, "probability_calibration_status" TEXT, "unexpected_situation_status" TEXT, "unexpected_situation_severity" REAL, "validation_permission" TEXT, "evidence_sample_size" INTEGER, "metric_provenance_json" TEXT, "migration_version" TEXT,
                PRIMARY KEY(daily_snapshot_id, symbol),
                FOREIGN KEY(daily_snapshot_id) REFERENCES field10_daily_snapshot(daily_snapshot_id)
            );

-- TABLE: field10_dependence_shadow
CREATE TABLE field10_dependence_shadow (
    daily_snapshot_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    correlation_cluster TEXT,
    cluster_concentration REAL,
    duplicate_exposure_penalty REAL,
    marginal_diversification_value REAL,
    usd_exposure REAL,
    eur_exposure REAL,
    common_factor_exposure REAL,
    covariance_method TEXT NOT NULL,
    sample_count INTEGER NOT NULL,
    validation_status TEXT NOT NULL,
    missing_reason TEXT,
    evidence_json TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    created_system_time TEXT NOT NULL,
    PRIMARY KEY(daily_snapshot_id,symbol,covariance_method),
    FOREIGN KEY(daily_snapshot_id,symbol)
      REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id,symbol)
);

-- TABLE: field10_event_intensity_shadow
CREATE TABLE field10_event_intensity_shadow (
    daily_snapshot_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    event_family TEXT NOT NULL,
    baseline_intensity REAL,
    current_excitation REAL,
    decay REAL,
    event_cluster_state TEXT,
    estimated_remaining_impact REAL,
    event_transition_warning TEXT,
    model_version TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    sample_count INTEGER NOT NULL,
    missing_reason TEXT,
    content_hash TEXT NOT NULL UNIQUE,
    created_system_time TEXT NOT NULL,
    PRIMARY KEY(daily_snapshot_id,symbol,event_family,model_version),
    FOREIGN KEY(daily_snapshot_id,symbol)
      REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id,symbol)
);

-- TABLE: field10_final_multi_symbol_outcome
CREATE TABLE field10_final_multi_symbol_outcome (
                outcome_id TEXT PRIMARY KEY,
                daily_snapshot_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                prediction_content_hash TEXT NOT NULL,
                horizon_hours INTEGER NOT NULL,
                realized_return_pct REAL,
                realized_direction TEXT,
                direction_correct INTEGER,
                realized_mfe_pct REAL,
                realized_mae_pct REAL,
                realized_net_return_pct REAL,
                evaluation_json TEXT NOT NULL,
                outcome_hash TEXT NOT NULL UNIQUE,
                settled_broker_time TEXT NOT NULL,
                created_system_time TEXT NOT NULL,
                FOREIGN KEY(daily_snapshot_id,symbol) REFERENCES field10_daily_final_multi_symbol_rank(daily_snapshot_id,symbol)
            );

-- TABLE: field10_forecast_ledger
CREATE TABLE field10_forecast_ledger (
    forecast_id TEXT PRIMARY KEY,
    daily_snapshot_id TEXT NOT NULL,
    parent_run_id TEXT NOT NULL,
    child_run_id TEXT,
    broker_day TEXT NOT NULL,
    symbol TEXT NOT NULL,
    horizon_hours INTEGER NOT NULL CHECK(horizon_hours IN (1,6,12,24)),
    completed_h1_candle TEXT NOT NULL,
    published_at_broker_time TEXT NOT NULL,
    outcome_due_broker_time TEXT NOT NULL,
    raw_direction_probability REAL,
    calibrated_direction_probability REAL,
    calibration_status TEXT NOT NULL,
    raw_expected_return REAL,
    expected_value REAL,
    net_expected_value REAL,
    risk_adjusted_expected_value REAL,
    expected_spread_cost REAL,
    expected_slippage_cost REAL,
    var_95 REAL,
    cvar_95 REAL,
    expected_mfe REAL,
    expected_mae REAL,
    probability_reach_expected_value REAL,
    sample_count INTEGER,
    effective_sample_size REAL,
    lower_interval REAL,
    median_prediction REAL,
    upper_interval REAL,
    target_coverage REAL,
    transition_probability REAL,
    entry_permission TEXT NOT NULL,
    formula_version TEXT NOT NULL,
    feature_version TEXT NOT NULL,
    model_version TEXT NOT NULL,
    calibration_version TEXT NOT NULL,
    source_id TEXT,
    source_hash TEXT,
    content_hash TEXT NOT NULL UNIQUE,
    missing_reason TEXT,
    publication_status TEXT NOT NULL,
    created_system_time TEXT NOT NULL,
    UNIQUE(daily_snapshot_id,symbol,horizon_hours,model_version,calibration_version),
    FOREIGN KEY(daily_snapshot_id,symbol)
      REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id,symbol)
);

-- TABLE: field10_hourly_quality
CREATE TABLE field10_hourly_quality (
                parent_run_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                broker_timestamp TEXT NOT NULL,
                rank INTEGER,
                data_quality_grade TEXT NOT NULL,
                data_quality_score REAL NOT NULL,
                higher_standard_regime TEXT,
                higher_standard_bias TEXT,
                less_risky_bias TEXT,
                trust_score REAL,
                reliability REAL,
                validation_status TEXT,
                quality_reason TEXT,
                broker_date TEXT,
                broker_hour TEXT,
                current_session TEXT,
                session_priority REAL,
                average_spread REAL,
                spread_quality TEXT,
                uncertainty REAL,
                error_percentage REAL,
                trade_permission TEXT,
                final_action TEXT,
                transition_risk_24h REAL,
                expected_return_12h REAL,
                rank_score REAL,
                rank_reason TEXT,
                run_id TEXT,
                source_id TEXT,
                created_at TEXT NOT NULL, expected_return_24h REAL, expected_return_36h REAL, transition_risk_6h REAL, expected_value_6h REAL, risk_adjusted_expected_value_6h REAL, probability_profit_1h REAL, probability_profit_6h REAL, probability_profit_12h REAL, probability_reach_ev_1h REAL, probability_reach_ev_6h REAL, probability_reach_ev_12h REAL, ev_target_1h REAL, ev_target_6h REAL, ev_target_12h REAL, tick_volume_12h REAL, volume_12h_z REAL, volume_source TEXT, ev_model_version TEXT, probability_calibration_status TEXT, unexpected_situation_status TEXT, unexpected_situation_severity REAL, validation_permission TEXT, evidence_sample_size INTEGER, metric_provenance_json TEXT, migration_version TEXT,
                PRIMARY KEY(parent_run_id, symbol, broker_timestamp)
            );

-- TABLE: field10_integrated_evidence_history
CREATE TABLE field10_integrated_evidence_history (
                parent_run_id TEXT NOT NULL,
                child_run_id TEXT NOT NULL,
                canonical_run_id TEXT,
                symbol TEXT NOT NULL,
                role TEXT,
                timeframe TEXT NOT NULL,
                broker_timestamp TEXT NOT NULL,
                broker_date TEXT,
                broker_hour INTEGER,
                rank INTEGER,
                current_session TEXT,
                technical_bias TEXT,
                technical_source TEXT,
                technical_reliability REAL,
                sentiment_bias TEXT,
                sentiment_source TEXT,
                sentiment_reliability REAL,
                sentiment_headline TEXT,
                sentiment_publication_time TEXT,
                sentiment_entity_match TEXT,
                session_bias TEXT,
                session_source TEXT,
                session_reliability REAL,
                regime_bias TEXT,
                regime_source TEXT,
                higher_standard_regime TEXT,
                regime_probability REAL,
                regime_entropy REAL,
                regime_posterior_margin REAL,
                expected_regime_duration REAL,
                data_mining_bias TEXT,
                data_mining_source TEXT,
                combined_evidence_bias TEXT,
                shadow_fusion_score REAL,
                evidence_available_count INTEGER,
                evidence_agreement REAL,
                conflict_index REAL,
                transition_risk_1h REAL,
                transition_risk_3h REAL,
                transition_risk_6h REAL,
                change_probability REAL,
                current_regime_run_length REAL,
                expected_stable_duration REAL,
                structural_break_status TEXT,
                drift_status TEXT,
                adaptive_window_size INTEGER,
                conformal_target_coverage REAL,
                conformal_coverage REAL,
                conformal_coverage_status TEXT,
                interval_width REAL,
                calibrated_reliability REAL,
                data_quality_grade TEXT,
                spread_quality TEXT,
                correlation_cluster TEXT,
                duplicate_exposure_penalty REAL,
                cvar_95 REAL,
                marginal_tail_risk REAL,
                suggested_risk_weight REAL,
                trade_permission TEXT,
                validation_permission TEXT,
                protected_final_action TEXT,
                outcome_settled INTEGER,
                actual_next_h1_direction TEXT,
                master_action_correct INTEGER,
                brier_score REAL,
                conditional_accuracy REAL,
                explanation TEXT,
                source_id TEXT,
                snapshot_hash TEXT NOT NULL,
                calculation_version TEXT NOT NULL,
                created_at TEXT NOT NULL, publication_status TEXT, transition_risk_24h REAL, expected_return_12h REAL, expected_return_24h REAL, expected_return_36h REAL, "expected_value_6h" REAL, "risk_adjusted_expected_value_6h" REAL, "probability_profit_1h" REAL, "probability_profit_6h" REAL, "probability_profit_12h" REAL, "probability_reach_ev_1h" REAL, "probability_reach_ev_6h" REAL, "probability_reach_ev_12h" REAL, "ev_target_1h" REAL, "ev_target_6h" REAL, "ev_target_12h" REAL, "tick_volume_12h" REAL, "volume_12h_z" REAL, "volume_source" TEXT, "ev_model_version" TEXT, "probability_calibration_status" TEXT, "unexpected_situation_status" TEXT, "unexpected_situation_severity" REAL, "evidence_sample_size" INTEGER, "metric_provenance_json" TEXT, "migration_version" TEXT,
                PRIMARY KEY (
                    parent_run_id, symbol, timeframe, broker_timestamp, child_run_id, snapshot_hash
                )
            );

-- TABLE: field10_model_validation_registry
CREATE TABLE field10_model_validation_registry (
                registry_id TEXT PRIMARY KEY,
                broker_day TEXT NOT NULL,
                symbol TEXT NOT NULL,
                method_name TEXT NOT NULL,
                model_version TEXT NOT NULL,
                formula_version TEXT NOT NULL,
                threshold_version TEXT NOT NULL,
                sample_count INTEGER NOT NULL DEFAULT 0,
                validation_status TEXT NOT NULL,
                promotion_status TEXT NOT NULL,
                p_value REAL,
                pbo_estimate REAL,
                result_hash TEXT NOT NULL,
                result_json TEXT NOT NULL,
                UNIQUE(broker_day, symbol, method_name, result_hash)
            );

-- TABLE: field10_news_event_outcome
CREATE TABLE field10_news_event_outcome (
                outcome_id TEXT PRIMARY KEY,
                daily_snapshot_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                event_id TEXT NOT NULL,
                horizon TEXT NOT NULL,
                original_forecast_hash TEXT NOT NULL,
                realized_return REAL,
                realized_direction TEXT,
                correct_direction INTEGER,
                settled_at_broker_time TEXT NOT NULL,
                outcome_json TEXT NOT NULL,
                outcome_hash TEXT NOT NULL UNIQUE,
                FOREIGN KEY(daily_snapshot_id, symbol, event_id)
                    REFERENCES field10_daily_news_event_rank(daily_snapshot_id, symbol, event_id)
            );

-- TABLE: field10_next_day_candidate
CREATE TABLE field10_next_day_candidate (
                candidate_id TEXT PRIMARY KEY,
                target_broker_day TEXT NOT NULL,
                source_broker_day TEXT NOT NULL,
                universe_hash TEXT NOT NULL,
                status TEXT NOT NULL,
                parent_run_id TEXT,
                latest_completed_h1 TEXT,
                candidate_hash TEXT NOT NULL UNIQUE,
                candidate_json TEXT NOT NULL,
                prepared_at_broker_time TEXT NOT NULL,
                activated_snapshot_id TEXT,
                UNIQUE(target_broker_day, universe_hash, status)
            );

-- TABLE: field10_outcome_ledger
CREATE TABLE field10_outcome_ledger (
    forecast_id TEXT NOT NULL,
    settlement_version TEXT NOT NULL,
    outcome_due_broker_time TEXT NOT NULL,
    settled_at_broker_time TEXT NOT NULL,
    realized_return REAL,
    realized_mfe REAL,
    realized_mae REAL,
    direction_outcome TEXT,
    expected_value_reached INTEGER,
    transition_occurred INTEGER,
    spread_cost REAL,
    slippage_cost REAL,
    net_realized_return REAL,
    outcome_source_id TEXT NOT NULL,
    outcome_source_hash TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    created_system_time TEXT NOT NULL,
    PRIMARY KEY(forecast_id,settlement_version),
    FOREIGN KEY(forecast_id) REFERENCES field10_forecast_ledger(forecast_id)
);

-- TABLE: field10_rank_confidence_shadow
CREATE TABLE field10_rank_confidence_shadow (
    daily_snapshot_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    original_rank INTEGER,
    candidate_utility REAL,
    probability_rank_1 REAL,
    probability_rank_le_4 REAL,
    median_rank REAL,
    rank_percentile_low REAL,
    rank_percentile_high REAL,
    rank_instability REAL,
    score_gap_to_next_symbol REAL,
    bootstrap_draws INTEGER NOT NULL,
    block_length INTEGER NOT NULL,
    bootstrap_seed TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    missing_reason TEXT,
    model_version TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    created_system_time TEXT NOT NULL,
    PRIMARY KEY(daily_snapshot_id,symbol,model_version),
    FOREIGN KEY(daily_snapshot_id,symbol)
      REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id,symbol)
);

-- TABLE: field10_regime_shadow
CREATE TABLE field10_regime_shadow (
    daily_snapshot_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    selected_regime TEXT,
    selected_regime_probability REAL,
    second_regime TEXT,
    second_regime_probability REAL,
    posterior_margin REAL,
    regime_entropy REAL,
    self_transition_probability REAL,
    transition_probability_1h REAL,
    transition_probability_6h REAL,
    transition_probability_12h REAL,
    transition_probability_24h REAL,
    regime_age INTEGER,
    expected_remaining_duration REAL,
    regime_model_version TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    evidence_sample_size INTEGER NOT NULL,
    missing_reason TEXT,
    content_hash TEXT NOT NULL UNIQUE,
    created_system_time TEXT NOT NULL,
    PRIMARY KEY(daily_snapshot_id,symbol,regime_model_version),
    FOREIGN KEY(daily_snapshot_id,symbol)
      REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id,symbol)
);

-- TABLE: field10_reliability_shadow
CREATE TABLE field10_reliability_shadow (
    daily_snapshot_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    calibration_reliability REAL,
    conformal_coverage_reliability REAL,
    sample_adequacy REAL,
    data_completeness REAL,
    source_identity_reliability REAL,
    regime_stability REAL,
    structural_stability REAL,
    rank_stability REAL,
    feature_availability REAL,
    outcome_settlement_completeness REAL,
    aggregate_reliability REAL,
    reliability_status TEXT NOT NULL,
    principal_reliability_weakness TEXT,
    reliability_explanation TEXT NOT NULL,
    effective_sample_size REAL,
    component_weights_json TEXT NOT NULL,
    reliability_version TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    created_system_time TEXT NOT NULL,
    PRIMARY KEY(daily_snapshot_id,symbol,reliability_version),
    FOREIGN KEY(daily_snapshot_id,symbol)
      REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id,symbol)
);

-- TABLE: field10_research_experiments
CREATE TABLE field10_research_experiments (
                experiment_id TEXT PRIMARY KEY,
                parent_run_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                model_version TEXT NOT NULL,
                canonical_run_id TEXT,
                broker_timestamp TEXT,
                candidate_count INTEGER NOT NULL DEFAULT 0,
                candidate_names_json TEXT NOT NULL,
                best_candidate TEXT,
                spa_statistic REAL,
                spa_p_value REAL,
                bootstrap_draws INTEGER,
                block_length INTEGER,
                settlement_verified INTEGER NOT NULL DEFAULT 0,
                out_of_sample_verified INTEGER NOT NULL DEFAULT 0,
                validation_start TEXT,
                validation_end TEXT,
                promotion_status TEXT NOT NULL,
                parameter_hash TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            , "parent_model_version" TEXT, "candidate_model_version" TEXT, "feature_version" TEXT, "formula_version" TEXT, "threshold_version" TEXT, "training_interval" TEXT, "validation_interval" TEXT, "test_interval" TEXT, "purging_interval" TEXT, "embargo_interval" TEXT, "parameter_values_json" TEXT, "evaluation_results_json" TEXT, "source_code_hash" TEXT, "data_hash" TEXT, "walk_forward_type" TEXT, "spa_p_value_v2" REAL, "pbo_probability" REAL, "deflated_sharpe_probability" REAL, "in_sample_metric" REAL, "out_of_sample_metric" REAL, "rank_correlation_stability" REAL, "regime_stability" REAL, "session_stability" REAL, "promotion_gate_status" TEXT, "promotion_reasons_json" TEXT);

-- TABLE: field10_research_model_registry
CREATE TABLE field10_research_model_registry (
                model_version TEXT PRIMARY KEY,
                calculation_version TEXT NOT NULL,
                shadow_mode INTEGER NOT NULL,
                feature_flags_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

-- TABLE: field10_research_validation
CREATE TABLE field10_research_validation (
                parent_run_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                broker_timestamp TEXT NOT NULL,
                research_rank INTEGER,
                rank_pool TEXT,
                production_action TEXT,
                research_action TEXT,
                research_permission TEXT,
                conflict_status TEXT,
                research_reliability REAL,
                data_quality_grade TEXT,
                data_quality_score REAL,
                regime_probability REAL,
                regime_entropy REAL,
                expected_regime_duration REAL,
                remaining_regime_duration REAL,
                transition_risk_1h REAL,
                transition_risk_3h REAL,
                transition_risk_6h REAL,
                structural_break_status TEXT,
                break_count INTEGER,
                break_strength REAL,
                drift_status TEXT,
                adaptive_window_size INTEGER,
                state_stability REAL,
                innovation_z REAL,
                brier_score REAL,
                log_loss REAL,
                calibration_error REAL,
                conformal_status TEXT,
                conformal_coverage REAL,
                interval_width REAL,
                dm_p_value REAL,
                dm_candidate_superior INTEGER,
                spa_p_value REAL,
                spa_superior INTEGER,
                correlation_cluster TEXT,
                duplicate_exposure_penalty REAL,
                cvar_95 REAL,
                tail_risk_grade TEXT,
                calculation_status TEXT,
                explanation TEXT,
                canonical_run_id TEXT,
                source_id TEXT,
                result_hash TEXT,
                model_version TEXT NOT NULL,
                result_json TEXT NOT NULL,
                elapsed_seconds REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                PRIMARY KEY(parent_run_id, symbol, broker_timestamp, model_version)
            );

-- TABLE: field10_schema_migration_audit_20260703
CREATE TABLE field10_schema_migration_audit_20260703 (
                migration_id TEXT PRIMARY KEY,
                migration_version TEXT NOT NULL,
                status TEXT NOT NULL,
                details_json TEXT NOT NULL,
                applied_at TEXT NOT NULL
            );

-- TABLE: field10_session_shadow
CREATE TABLE field10_session_shadow (
    daily_snapshot_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    session_name TEXT NOT NULL,
    session_rank INTEGER,
    session_normalized_volatility REAL,
    volatility_percentile REAL,
    abnormal_activity REAL,
    normalized_tick_volume REAL,
    normalized_spread REAL,
    expected_movement REAL,
    net_expected_value REAL,
    cvar_95 REAL,
    directional_hit_rate REAL,
    regime_compatibility REAL,
    entry_permission TEXT NOT NULL,
    sample_count INTEGER NOT NULL,
    data_completeness REAL,
    current_active_session INTEGER NOT NULL DEFAULT 0,
    next_session INTEGER NOT NULL DEFAULT 0,
    session_transition_risk REAL,
    formula_version TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    missing_reason TEXT,
    content_hash TEXT NOT NULL UNIQUE,
    created_system_time TEXT NOT NULL,
    PRIMARY KEY(daily_snapshot_id,symbol,session_name,formula_version),
    FOREIGN KEY(daily_snapshot_id,symbol)
      REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id,symbol)
);

-- TABLE: field10_shadow_incremental_state
CREATE TABLE field10_shadow_incremental_state (
                symbol TEXT NOT NULL,
                state_name TEXT NOT NULL,
                last_broker_timestamp TEXT,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(symbol, state_name)
            );

-- TABLE: field10_shadow_publication_audit
CREATE TABLE field10_shadow_publication_audit (
    audit_id TEXT PRIMARY KEY,
    daily_snapshot_id TEXT,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    details_json TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    created_system_time TEXT NOT NULL,
    FOREIGN KEY(daily_snapshot_id) REFERENCES field10_daily_snapshot(daily_snapshot_id)
);

-- TABLE: field10_structural_break_shadow
CREATE TABLE field10_structural_break_shadow (
    daily_snapshot_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    last_structural_break TEXT,
    structural_break_strength REAL,
    post_break_h1_count INTEGER,
    pre_post_parameter_distance REAL,
    changepoint_probability REAL,
    modal_run_length INTEGER,
    expected_run_length REAL,
    run_length_uncertainty REAL,
    post_break_validation_permission TEXT NOT NULL,
    break_components_json TEXT NOT NULL,
    model_version TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    missing_reason TEXT,
    content_hash TEXT NOT NULL UNIQUE,
    created_system_time TEXT NOT NULL,
    PRIMARY KEY(daily_snapshot_id,symbol,model_version),
    FOREIGN KEY(daily_snapshot_id,symbol)
      REFERENCES field10_daily_snapshot_symbol(daily_snapshot_id,symbol)
);

-- TABLE: schema_migrations
CREATE TABLE schema_migrations (
    migration_id TEXT PRIMARY KEY,
    checksum TEXT NOT NULL,
    description TEXT NOT NULL,
    applied_at_utc TEXT NOT NULL
);
