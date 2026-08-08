-- FIELD10_SCHEMA.sql

-- Extracted after migration field10-rank-ev6-probability-volume12-20260704-v1

PRAGMA journal_mode=WAL;

PRAGMA busy_timeout=8000;

BEGIN;

CREATE TABLE api_request_audit_20260704 (
            request_id TEXT PRIMARY KEY,
            parent_run_id TEXT,
            provider TEXT NOT NULL,
            endpoint_category TEXT NOT NULL,
            symbol_count INTEGER NOT NULL,
            requested_symbols_hash TEXT NOT NULL,
            credits_used REAL,
            credits_left REAL,
            cache_hit INTEGER NOT NULL,
            deduplicated INTEGER NOT NULL,
            response_status TEXT NOT NULL,
            completed_h1_identity TEXT NOT NULL,
            requested_at TEXT NOT NULL,
            duration_ms REAL NOT NULL,
            retry_count INTEGER NOT NULL
        );

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
            );

CREATE TABLE field10_research_model_registry (
                model_version TEXT PRIMARY KEY,
                calculation_version TEXT NOT NULL,
                shadow_mode INTEGER NOT NULL,
                feature_flags_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

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

CREATE TABLE field10_schema_migration_audit_20260703 (
                migration_id TEXT PRIMARY KEY,
                migration_version TEXT NOT NULL,
                status TEXT NOT NULL,
                details_json TEXT NOT NULL,
                applied_at TEXT NOT NULL
            );

CREATE TABLE field10_shadow_incremental_state (
                symbol TEXT NOT NULL,
                state_name TEXT NOT NULL,
                last_broker_timestamp TEXT,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY(symbol, state_name)
            );

CREATE TABLE market_data_candle_cache_20260704 (
            request_key TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            canonical_symbol TEXT NOT NULL,
            provider_symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            completed_broker_candle TEXT NOT NULL,
            requested_bar_count INTEGER NOT NULL,
            adjusted_status TEXT NOT NULL,
            provider_profile_fingerprint TEXT NOT NULL,
            source TEXT NOT NULL,
            frame_json TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            stored_at TEXT NOT NULL
        );

CREATE TABLE shared_news_cache_20260704 (
            cache_key TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            normalized_url TEXT,
            headline_hash TEXT NOT NULL,
            headline TEXT NOT NULL,
            published_at TEXT,
            source TEXT,
            payload_json TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            stored_at TEXT NOT NULL
        );

CREATE INDEX idx_api_audit_parent_provider_20260704
          ON api_request_audit_20260704(parent_run_id,provider,requested_at);

CREATE INDEX idx_f10_audit_snapshot
                ON field10_daily_snapshot_audit(daily_snapshot_id, observed_at_broker_time DESC);

CREATE INDEX idx_f10_candidate_target
                ON field10_next_day_candidate(target_broker_day DESC, status);

CREATE INDEX "idx_f10_daily_broker_20260704" ON "field10_daily_higher_lock"(broker_day);

CREATE INDEX "idx_f10_daily_permission_20260704" ON "field10_daily_higher_lock"(validation_permission);

CREATE INDEX "idx_f10_daily_unexpected_20260704" ON "field10_daily_higher_lock"(unexpected_situation_status);

CREATE INDEX "idx_f10_hourly_parent_rank_20260704" ON "field10_hourly_quality"(parent_run_id,rank);

CREATE INDEX "idx_f10_hourly_permission_20260704" ON "field10_hourly_quality"(validation_permission);

CREATE INDEX "idx_f10_hourly_symbol_broker_20260704" ON "field10_hourly_quality"(symbol,broker_timestamp);

CREATE INDEX "idx_f10_hourly_unexpected_20260704" ON "field10_hourly_quality"(unexpected_situation_status);

CREATE INDEX idx_f10_outcome_day_status
                ON field10_daily_outcome(broker_day DESC, settlement_status, symbol);

CREATE INDEX idx_f10_safety_latest
                ON field10_daily_safety_event(broker_day DESC, symbol, observed_at_broker_time DESC);

CREATE INDEX idx_f10_snapshot_day_status
                ON field10_daily_snapshot(broker_day DESC, publication_status);

CREATE INDEX idx_f10_snapshot_symbol_day_rank
                ON field10_daily_snapshot_symbol(broker_day DESC, daily_rank, symbol);

CREATE INDEX idx_f10_snapshot_symbol_status
                ON field10_daily_snapshot_symbol(eligibility_status, symbol, broker_day DESC);

CREATE INDEX idx_f10_snapshot_universe
                ON field10_daily_snapshot(universe_hash, broker_day DESC);

CREATE INDEX idx_f10_validation_method
                ON field10_model_validation_registry(method_name, broker_day DESC, symbol);

CREATE INDEX idx_market_cache_identity_20260704
          ON market_data_candle_cache_20260704(provider,canonical_symbol,timeframe,completed_broker_candle);

CREATE TABLE IF NOT EXISTS fx_spread_observation_20260704 (
 account_fingerprint TEXT NOT NULL, canonical_symbol TEXT NOT NULL, provider_symbol TEXT NOT NULL,
 spread_points REAL NOT NULL, observed_at TEXT NOT NULL, tradeable INTEGER NOT NULL,
 history_bars INTEGER NOT NULL DEFAULT 0, tick_volume_evidence INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY(account_fingerprint,provider_symbol,observed_at));

CREATE INDEX IF NOT EXISTS idx_fx_spread_obs_symbol_time_20260704
 ON fx_spread_observation_20260704(account_fingerprint,canonical_symbol,observed_at DESC);

CREATE TABLE IF NOT EXISTS fx_top15_qualification_20260704 (
 account_fingerprint TEXT NOT NULL, canonical_symbol TEXT NOT NULL, provider_symbol TEXT NOT NULL,
 rank INTEGER, qualified INTEGER NOT NULL, current_spread REAL, median_spread REAL, p95_spread REAL,
 observation_count INTEGER NOT NULL, spread_freshness_seconds REAL, history_bars INTEGER NOT NULL,
 tick_volume_evidence INTEGER NOT NULL, quality_score REAL NOT NULL, reason TEXT NOT NULL,
 evaluated_at TEXT NOT NULL, expires_at TEXT NOT NULL, version TEXT NOT NULL,
 PRIMARY KEY(account_fingerprint,canonical_symbol));

COMMIT;

