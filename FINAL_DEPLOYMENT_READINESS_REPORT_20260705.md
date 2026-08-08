# ADX Quant Pro — Final Repair and Deployment-Readiness Report

**Build:** `ADX_QUANT_PRO_DEPLOYMENT_READY_20260705`  
**Main Streamlit entry file:** `app.py`  
**Compatibility entry:** `adx_dashpoard.py`  
**Database:** `data/multi_symbol_field10_20260701.sqlite3`  
**Deployment schema version:** `2026070501`

## 1. Delivered architecture

The project now uses one Settings-owned, quota-safe collection and calculation path. Market data is requested only by the explicit calculation/refresh workflow and then reused by Lunch, Fields 1–3, Field 10, inner sections, exports and the AI Assistant through persisted normalized candles and one canonical run identity.

Provider priority is fixed as:

1. Twelve Data — primary / Plan A
2. MT5 — Plan B
3. Finnhub — Plan C
4. Alpha Vantage — Plan D
5. Valid local candle cache and the latest valid canonical snapshot

MT4 was not added.

## 2. Files added

- `core/runtime_selection_20260705.py`
- `core/data/deployment_migrations_20260705.py`
- `core/data/twelve_data_quota_manager.py`
- `core/data/candle_repository.py`
- `core/data/market_data_orchestrator.py`
- `core/data/multi_symbol_scheduler.py`
- `core/data/__init__.py`
- `core/calculation/run_orchestrator.py`
- `core/calculation/__init__.py`
- `core/connectors/credential_vault.py`
- `core/sentiment/news_repository.py`
- `core/sentiment/news_orchestrator.py`
- `core/sentiment/eurusd_sentiment_engine.py`
- `core/sentiment/__init__.py`
- `core/fundamental/fred_macro_provider.py`
- `core/fundamental/__init__.py`
- `ui/provider_health_panel_20260705.py`
- `ui/optional_provider_connectors_20260705.py`
- `scripts/run_deployment_migrations.py`
- `tests/test_deployment_readiness_upgrade_20260705.py`

## 3. Files changed

- `.gitignore`
- `requirements.txt`
- `core/app/refresh.py`
- `core/app/runner.py`
- `core/canonical_data_validation_20260621.py`
- `core/complete_repair_20260705.py`
- `core/connectors/data_parts/session.py`
- `core/field10_research_common_20260705.py`
- `core/field3_regime_lifecycle_store_20260701.py`
- `core/finnhub_connector.py`
- `core/multi_symbol_api_runtime_20260702.py`
- `core/multi_symbol_field10_20260701.py`
- `core/secure_api_startup_20260619.py`
- `core/startup_lunch_orchestrator_20260704.py`
- `core/streamlit_safe_dataframe.py`
- `core/system_continuous_validation_20260702.py`
- `tabs/ai_assistant_compact_20260619.py`
- `tabs/antd_page_router_20260615.py`
- `ui/lunch_field10_multi_symbol_20260701.py`
- `ui/lunch_four_core_fields_20260619.py`
- `ui/multi_symbol_settings_20260701.py`
- `ui/sidebar_fallback_panel.py`
- `tests/test_deployment_runtime_guards_20260702.py`
- `tests/test_field10_upgrade_20260704.py`

## 4. Table repairs

- Repaired `available_published_symbols()` compatibility so Lunch Fields 1 and 2 no longer fail with the unexpected-keyword error shown in the supplied screenshots.
- Added display-only duplicate-row removal without changing stored evidence or calculation results.
- Normalized `NaN`, positive/negative infinity and invalid scalar rendering to an em dash instead of exposing `nan` cards.
- Added safe container-width and column-width behavior.
- Preserved desktop tables and added bounded mobile cards; long Field 10 history defaults to compact mode and no longer renders hundreds of large cards on first open.
- Added canonical run ID, selected timeframe and selected symbol-scope columns to Field 10 output frames so mixed-run output is visible and prevented.
- Preserved all existing stored columns, calculation columns, exports and detail views.

## 5. API connector repairs

- Added a central market-data orchestrator; direct Field 10 renderer fetches were removed from active paths.
- Added encrypted credential persistence using a local Fernet vault. The vault path and key are excluded from Git/ZIP delivery, and database rows contain only a non-secret fingerprint.
- Startup and Streamlit reruns restore connector configuration and credentials without making a network call.
- Explicit Connect, Validate, Refresh and Settings Run actions use the central orchestrator.
- API keys remain masked and are excluded from logs, cache keys, database request ledgers and user-facing errors.
- Provider health and connection state are persisted separately from secrets.
- HTTP 429 handling uses `Retry-After` when available, bounded retry, cooldown state and fallback activation.
- Permanent credential/symbol/client errors are not retried in loops.

## 6. Twelve Data quota control

- Rolling 60-second ledger implemented.
- Account default: 8 credits/minute.
- Safe default: 6 credits/minute.
- Reserve: 2 credits.
- Daily account default: 800 credits.
- Daily safe ceiling: 700 credits.
- Request cost is reserved before a call and persisted.
- Quota state survives process restart.
- A ten-symbol run can use no more than six successful Twelve Data requests in the rolling safe window; unresolved symbols move to the next provider or valid cache without blocking the Streamlit render thread.

## 7. Top 10 symbol implementation

The first-load and packaged deployment default is:

`EURUSD, USDJPY, AUDUSD, GBPUSD, USDCAD, USDCHF, EURJPY, GBPJPY, EURGBP, NZDUSD`

- Added the **Top 10 Currency Pairs** preset in Settings.
- The packaged database preference is reset to this Top 10 H1 profile.
- User changes are persisted after the first-load profile is established.
- Selection is synchronized to Settings, connector scope, multi-symbol calculation, Field 10, canonical snapshot and export identity.

## 8. H4 synchronization

- Central runtime accepts and persists H4.
- Twelve Data interval mapping uses `4h`.
- Finnhub resolution uses `240`.
- MT5 uses `TIMEFRAME_H4` through the existing connector mapping.
- H4 completed-candle boundaries, settlement delay, cache keys, normalized candle records and canonical identity are aligned to four-hour boundaries.
- Field 10 now gives the selected runtime timeframe precedence over a stale legacy H1 identity when storing child runs, loading tables and registering generations.
- Continuous validation loads the selected-timeframe child publication instead of hardcoded H1.
- Canonical snapshot identity, per-symbol output, provider provenance and table identity use the same H4 selection.
- Existing H1 operation remains the default and is preserved.
- Optional research candidates whose formulas are explicitly defined in H1 bars are fail-closed under H4 rather than silently treating one H4 bar as one hour. They show an honest unavailable reason and cannot contaminate H4 production ranks.

## 9. Lunch selector placement

- `Choose the Lunch Field to Open` is now the first interactive Lunch control.
- It appears before Lunch metrics, cards, tables and inner sections.
- The obsolete lower duplicate was removed.
- Selecting or opening a field is display-only and does not invoke market providers or heavy calculation.

## 10. Synchronization and canonical snapshot repairs

The completed run envelope now contains:

- run ID, generation, created/expiry time, broker time, selected symbols, timeframe, latest completed candle, schema/calculation versions and snapshot hash;
- per-symbol provider, fallback status, freshness, quality and validation state;
- protected technical, regime, session, expected-return, transition-risk, probability, sentiment, macro, crowd-psychology, uncertainty, reliability, bias and actionability evidence when actually published;
- provider health for Twelve Data, MT5, Finnhub, Alpha Vantage, GDELT and FRED;
- quota state and fallback events;
- final ranking outputs and the Field 10 evidence-source inventory.

Missing evidence remains `None`/unavailable. No fake zero market values are generated.

## 11. Database migration repairs

Idempotent migration support was added for clean and existing databases. Added or repaired tables include:

- `deployment_schema_migrations`
- `runtime_preferences`
- `api_connection_state`
- `api_request_ledger`
- `provider_health`
- `daily_quota_usage`
- `candles`
- `news_articles`
- `sentiment_results`
- `macro_observations`
- `canonical_snapshots`
- `fallback_events`
- `calculation_runs`

Indexes were added for provider/time, run ID, symbol/timeframe/candle timestamp, news hashes/time, sentiment run, macro series, snapshot scope and fallback runs. Existing valid project data was preserved. The migration was run twice successfully against the delivered database and is safe to rerun.

## 12. NLP, sentiment and macro integration

- News priority: GDELT, Finnhub market news, Alpha Vantage news within allowance, local repository, cached data.
- Added article hashing, duplicate grouping, TF-IDF/cosine grouping, novelty, relevance, source quality, freshness, event importance and reliability fields.
- Added currency-aware EUR/USD direction conversion rather than a generic positive/negative label.
- Added local VADER and rule-based fallback; FinBERT remains optional when installed and practical.
- Added cached FRED macro observations and a normalized USD/EURUSD macro-pressure object.
- NLP output is keyed to the article dataset hash so unchanged news is reused.

## 13. Architecture repairs

- One central data collection path now feeds the existing calculation engine.
- Heavy calculation remains owned by Settings; Lunch startup and deferred refresh are read-only.
- Streamlit reruns, field expansion, navigation, exports, copy buttons and AI Assistant opening do not initiate provider calls.
- Import wrappers and package initializers were added for the new data, calculation, sentiment and fundamental modules.
- The Field 3 lifecycle payload uses faster deterministic compression to avoid CPU stalls on constrained deployments.

## 14. Validation performed

- Python compilation: **PASS** (`python -m compileall -q .`)
- Import audit: **PASS**, 16 primary runtime modules imported
- Existing database migration: **PASS**, run twice
- Clean/legacy migration tests: **PASS**
- Automated tests: **467 passed**, executed in three isolated batches to keep peak scientific-library memory bounded
  - Batch 1: 209 passed
  - Batch 2: 157 passed
  - Batch 3: 101 passed, 3 non-failing scikit-learn single-class warnings
- Streamlit headless startup: **PASS**
- HTTP readiness check: **200 OK**
- Streamlit log traceback check: **PASS**, no traceback
- Streamlit AppTest: **PASS**, no application exceptions
- Packaged runtime preference: **Top 10 symbols + H1**
- H4 boundary, persistence, provider normalization and no-H1-mixing tests: **PASS**

## 15. Genuine remaining limitations

1. No real API secrets were supplied in the repair environment. Live credential acceptance and real account quota values could not be tested against Twelve Data, MT5, Finnhub, Alpha Vantage, GDELT or FRED. Provider order, quota rejection, retry, fallback, normalization, persistence and cache behavior were tested with injected provider adapters and local data.
2. A fully interactive physical-phone browser session was not available. Mobile behavior was validated by the supplied screenshots, static responsive-layout checks and automated UI tests; the headless application started successfully.
3. H1-only optional shadow research models are intentionally unavailable in H4 mode unless their horizon definitions are separately redesigned for four-hour bars. They are excluded with a clear reason rather than mixed into H4 production evidence.

## 16. Deployment command

```bash
streamlit run app.py
```

For Streamlit Cloud, set the main file path to `app.py`, keep Python 3.12 as specified by `.python-version` and `runtime.txt`, and configure provider secrets through Streamlit Secrets rather than committing them to the repository.
