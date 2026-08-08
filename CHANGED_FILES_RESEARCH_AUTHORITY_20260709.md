# Changed Files — Field 10 Research Authority Repair 20260709

## New files
- `core/background_function_registry.py` — registers the requested 20 research foundations as visible background functions and lightweight persisted outputs.
- `core/field10_research_migration_20260709.py` — idempotent, non-destructive schema migration and `schema_migrations` repair.
- `core/field10_unified_authority_20260709.py` — authoritative Field 10 Unified Daily Locked Rank Table builder, supporting session/news/dinner/viz/export tables, and DB persistence.
- `core/view_model_sync.py` — snapshot hash guard for Field 10, Dinner, Data Visualization, and Export.
- `core/background_orchestrator.py` — staged materialization facade for the authority layer.
- `core/run_saga.py` — recoverable saga ledger helper.
- `ui/color_system.py` — central BUY/SELL/WAIT/CAUTION/BLOCKED/quality/risk styling with text labels and top-four row highlighting.
- `ui/mobile_export_panel.py` — mobile-safe CSV/ZIP export expander with Exit Download Mode and no modal trap.
- `exports/export_builder.py` — materialized snapshot export payload builder.
- `observability/system_health.py` — Settings health table for API/DB/snapshot/background/sync/mobile/deployment readiness.
- `tests/test_field10_authority_20260709.py` — authority, migration, sync, background-registry tests.
- `tests/test_mobile_export_panel_20260709.py` — full snapshot ZIP test.
- `tests/conftest.py` — adds project root to `sys.path` for normal `pytest` runs.

## Modified files
- `core/system_contract.py` — preserved legacy facade and added RunSnapshot, SymbolSnapshot, PublicationStatus, DataQualityStatus, ProviderStatus, Field10ViewModel, DinnerViewModel, VisualizationViewModel, ExportManifest, MobileLayoutState.
- `app.py` — startup now also runs the Field 10 research authority migration.
- `adx_dashpoard.py` — legacy entry point now runs the same migration.
- `ui/lunch_field10_multi_symbol_20260701.py` — Field 10 now displays the trusted Unified Daily Locked Rank Table first, then session/news/background evidence, sync guard, and phone export panel.
- `core/current_result_sync_20260708.py` — current-result CSV and Data Visualization now include the unified authority table and snapshot.
- `tabs/field456789_page_20260626.py` — Dinner now shows same-snapshot research evidence and sync status.
- `tabs/antd_page_router_20260615.py` — Settings now includes system health/sync/deployment readiness panel.
- `data/multi_symbol_field10_20260701.sqlite3` — migration applied additively; no existing tables were dropped or renamed.

## Non-deletion guarantee
No existing Field 10, Field 3, Dinner, ML, history, export, copy-button, tab, or database logic was removed. The new layer is additive and sits above existing tables as the authority/sync/export layer.
