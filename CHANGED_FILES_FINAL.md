# Changed Files — Final

## Modified source files

- `app.py` — retains the deployment entry point and runs the additive database migration before the UI.
- `core/field10_adaptive_regime_metrics_20260702.py` — timeframe-aware sample windows and horizon conversion.
- `core/field10_daily_outcome_settlement_20260702.py` — selected-timeframe settlement and explicit bars/hours semantics.
- `core/field10_daily_snapshot_contract_20260702.py` — removes runtime H1/600 dependence while retaining legacy aliases.
- `core/field10_institutional_shadow_20260704.py` — selected-timeframe shadow windows and duration-safe horizons.
- `core/field10_integrated_evidence_20260702.py` — passes selected timeframe into shared metrics.
- `core/field10_unified_migration_20260703.py` — timeframe-aware compatibility migration wiring.
- `core/field10_v3_candidate_orchestrator_20260705.py` — selected-timeframe propagation into the shadow candidate path.
- `core/field3_multi_symbol_fallback_20260703.py` — shared timeframe requirements for exact-symbol fallback validation.
- `core/lunch_h1_data_quality_v13.py` — legacy module name retained; runtime windows are timeframe-aware.
- `core/multi_symbol_field10_20260701.py` — durable per-symbol state machine, complete publication gate, exact-symbol restore, all-symbol continuation, Time/Timeframe table identity, and separate display/settings authorities.
- `core/runtime_selection_20260705.py` — separates settings, connector, calculation, Lunch display and active snapshot authorities.
- `core/runtime_state_cache_20260628.py` — persists complete child/Field 2/Field 10 state without secrets.
- `core/system_continuous_validation_20260702.py` — timeframe-aware validation propagation.
- `ui/lunch_field10_multi_symbol_20260701.py` — pinned Time/Timeframe/mobile identity fields and controlled missing/float formatting.
- `ui/lunch_four_core_fields_20260619.py` — dynamic actual-row table heights, selected-child Field 2 bundle and concise incident UI.
- `ui/lunch_multi_symbol_selector_20260704.py` — explicit form-based `Load Selected Symbol` behavior for Fields 1 and 2.

## New source files

- `core/timeframe_window_contract_20260706.py` — one M1/M5/M15/M30/H1/H4/D1 window and duration contract.
- `core/powerbi_child_bundle_20260706.py` — exact-symbol Field 2 publication and truthfully labeled causal fallback.
- `core/child_snapshot_publication_20260706.py` — complete child validation, persistence and reload gate.
- `core/timeframe_identity_migration_20260706.py` — idempotent migration and backup logic.
- `core/field10_shadow_research_candidates_20260706.py` — ten `NOT_PROMOTED` time-ordered shadow research candidates.
- `core/h4_acceptance_workflow_20260706.py` — deterministic offline ten-symbol H4 integration workflow.
- `scripts/run_h4_acceptance_20260706.py` — command-line acceptance runner.
- `tests/test_complete_h4_child_publication_20260706.py` — twenty required repair tests.

## Database files

- `data/multi_symbol_field10_20260701.sqlite3` — migrated in place; legacy rows retained; deterministic fixture rows excluded.
- `backups/multi_symbol_field10_20260701.pre_20260706_timeframe_identity_child_publication_v1.sqlite3` — pre-migration backup.

Transient SQLite `-wal` and `-shm` files are intentionally excluded from the delivery because they are process-local journal files, not authoritative database records.

## Reports and evidence

- `CHANGED_FILES_FINAL.md`
- `ROOT_CAUSE_REPORT.md`
- `DATABASE_MIGRATION_REPORT.md`
- `TEST_REPORT.md`
- `DEPLOYMENT_INSTRUCTIONS.md`
- `REAL_DATA_AVAILABILITY_REPORT.md`
- `test_artifacts/database_migration_verification_20260706.json`
- `test_artifacts/h4_acceptance_20260706/h4_acceptance_result.json`
- `test_artifacts/h4_acceptance_console_20260706.txt`

## Protection confirmation

No protected production decision formula or threshold was intentionally removed or changed. The protected Field 1 renderer files were restored to their uploaded versions, and the protected-hash tests pass.
