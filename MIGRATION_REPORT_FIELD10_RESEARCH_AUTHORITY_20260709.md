# Migration Report — Field 10 Research Authority 20260709

Migration file: `core/field10_research_migration_20260709.py`

Result: Applied successfully in the project database.

## Safety behavior
- Idempotent: can run repeatedly.
- Non-destructive: does not drop or rename existing tables.
- Repairs `schema_migrations` safely even when old schemas use `migration_id`, integer `version`, missing `applied_at`, missing `checksum`, or missing `status`.
- Creates `migration_lock` and `migration_audit` if missing.

## New/ensured tables
- `field10_unified_rank_snapshot`
- `field10_unified_rank_symbol`
- `field10_daily_session_rank`
- `field10_daily_news_event_rank`
- `field10_research_background_evidence`
- `field10_session_outcome`
- `field10_news_event_outcome`
- `field10_candidate_governance`
- `dinner_research_background_evidence`
- `visualization_view_materialized`
- `export_manifest`
- `mobile_download_audit`
- `background_function_registry`
- `migration_lock`
- `migration_audit`

## Startup integration
Both `app.py` and `adx_dashpoard.py` call `migrate_field10_research_authority(DB_PATH)` after the existing migrations.
