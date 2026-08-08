# ADX Quant Pro — Three-Selector, H4, Database and Consolidated Field 10 Repair

Date: 2026-07-07
Preferred Streamlit entry point: `app.py`
Backward-compatible entry point: `adx_dashpoard.py` (same `core.app_shell.run_app()` runtime)

## Completion boundary

This repair changes selector ownership, explicit load/reload behavior, normalized persistence, exact symbol/timeframe publication validation, and the user-facing Field 3/Field 10 consolidation. Existing quantitative formulas, calculation engines, ML/regime/research logic, histories and evidence-producing database tables remain in place. Duplicate rendering was removed from the active user path; useful source calculations were retained.

No live API credentials were used during verification. The 18-symbol recovery scenario used controlled deterministic H4 OHLC fixtures to test orchestration and identity safety; it is not evidence that a live provider plan supports every requested symbol.

## Root causes found

1. **Explicit empty selections were treated as missing.** Selector initialization and legacy persistence used truthiness (`current or persisted or defaults`). Clearing/deselecting a group therefore revived defaults or stale persisted symbols on a later rerun.
2. **The selectors did not have a true failed-only retry contract.** Repeated Load operations could fetch all symbols again, lose valid frames, and did not expose a dedicated `Reload Failed Symbols` action.
3. **Current selection, loaded universe and previously completed universe were conflated.** Field 10 built its symbol spine from combinations of selected, loaded and historical/completed symbols and could force the main symbol into the table. That allowed stale or unselected symbols to reappear.
4. **Selector/load persistence was JSON/audit-centric rather than normalized.** There was no durable per-group position, per-symbol/per-timeframe attempt, normalized candle identity, or atomic per-symbol Field 10 publication table.
5. **Timeframe identity was not enforced at every boundary.** Legacy restoration may not contain a trustworthy timeframe, and the publication validator did not reject mixed H1/H4 rows for the same generation.
6. **A single hard history preference was being used as a completion proxy.** Genuine adaptive calculations with the real module minimum could be rejected merely for missing the preferred history length.
7. **Optional evidence was over-coupled to technical completion.** Missing optional reliability/news fields could blank or reject otherwise valid technical rows.
8. **The three calculation buttons could trigger data loading implicitly.** This violated the requested compute-only run contract and could hide selector ownership errors.
9. **The active Field 10 UI still exposed multiple/redundant presentation paths.** The authoritative table, source cards, search, ranking/audit surfaces and charts were not constrained to one user-facing exact-symbol surface.
10. **Fresh deployment DDL contained a duplicated `selected_symbols_json` declaration.** The duplicate was removed from the canonical deployment migration.

## Modified and added files

### Production code

- `app.py`
- `adx_dashpoard.py`
- `core/data/deployment_migrations_20260705.py`
- `core/normalized_multi_symbol_migration_20260707.py` (new)
- `core/multi_symbol_run_groups_20260706.py`
- `core/multi_symbol_load_manager_20260707.py`
- `core/multi_symbol_completion_contract_20260706.py`
- `tabs/antd_page_router_20260615.py`
- `ui/multi_symbol_settings_20260701.py`
- `ui/lunch_field10_multi_symbol_20260701.py`

### Tests updated for the new non-duplicated UI/ownership contract

- `tests/test_deployment_readiness_upgrade_20260705.py`
- `tests/test_deployment_runtime_guards_20260702.py`
- `tests/test_field10_all_selected_repair_20260707.py`
- `tests/test_field3_field10_multi_symbol_sync_20260703.py`
- `tests/test_final_repair_20260707.py`
- `tests/test_load_first_generation_fix_20260707.py`
- `tests/test_multi_symbol_routing_20260702.py`
- `tests/test_three_selector_consolidation_20260707.py` (new)

## Database migration

Migration ID/version: `normalized_three_selector_publication_v1` / `2026070704`.

The additive migration creates or upgrades:

- `selector_groups`
- `selector_selections`
- `selector_load_attempts`
- `candle_store`
- `symbol_calculation_snapshots`
- `canonical_runs`
- `field10_symbol_rows`
- `news_sentiment_evidence`
- `legacy_identity_quarantine`
- `normalized_schema_migrations`

Important migration behavior:

- Uses explicit `first`, `second`, `third` group IDs.
- Stores order and timeframe per current selection.
- Distinguishes a fresh/uninitialized group from an intentionally empty group through `current_state_initialized`.
- Uses unique current position and current symbol constraints within each group.
- Uses `(symbol, timeframe, completed_open_time)` as the normalized candle identity.
- Adds indexes for group/current state, symbol/timeframe attempts, latest candles, run/generation and latest publication lookup.
- Backfills only identities that can be determined safely.
- Restores legacy selector rows without guessing their timeframe; unknown legacy timeframe is stored as `UNKNOWN` until an explicit H4/H1 load replaces it.
- Quarantines invalid legacy selector JSON instead of assigning guessed symbols.
- Runs in transactions and records a completion checksum.
- Is idempotent.
- `migrate_deployment_schema()` creates a pre-normalized database backup before applying the normalized schema.
- Startup invokes the migration without starting market calculation.

Migration smoke test against the original uploaded database:

- First migration: PASS
- Second/idempotent migration: PASS
- Required normalized tables: PASS
- 18 current selections represented without symbol columns: PASS
- Exact order restored: PASS
- All current selection timeframes: `H4`
- Completion checksum recorded: `31dae26a5184a6060f99ae9eccab246882cde5ca4fde7835fb1a9e4daa63f5f2`

## Corrected selector/load/reload flow

1. Settings initializes one canonical timeframe, defaulting to H4 when no valid saved timeframe exists.
2. Three reusable selector instances use immutable ownership IDs: `FIRST`, `SECOND`, `THIRD` in session state and `first`, `second`, `third` in normalized storage.
3. Each selector has independent widget/state/load keys, exact selected order, loaded/failed sets, retry counts, provider evidence, row counts and failure reasons.
4. Widget-backed keys are seeded before widget construction and are never mutated after instantiation. Preset/clear operations use pending/draft state and rerun.
5. `Load Selected Data` sends exactly that selector's current symbols and current canonical timeframe to the market-data orchestrator.
6. Every returned payload is checked for exact symbol and timeframe identity, genuine completed rows, spacing and module minimum.
7. A partial attempt remains `PARTIAL_READY` and keeps valid exact-symbol frames.
8. `Reload Failed Symbols` retries only the latest selected failed/rejected symbols for that selector/timeframe, filters any unselected provider result, and merges recovered symbols without refetching valid symbols.
9. Structured failures are retained (`PROVIDER_RATE_LIMIT`, `SYMBOL_NOT_SUPPORTED`, `TIMEFRAME_NOT_SUPPORTED`, `NO_GENUINE_CANDLES`, `BELOW_MODULE_MINIMUM`, `IDENTITY_MISMATCH`, `VALIDATION_WARNING`).
10. The cumulative loaded universe is deduplicated by normalized exact symbol while preserving first/second/third appearance order.
11. All three calculation buttons consume that same cumulative loaded universe. The button changes only depth (`LUNCH_CORE`, `QUICK`, `FULL`).
12. Calculation buttons are disabled until at least one exact current selector load is valid, and they never fetch an API.

## Data sufficiency behavior

- H4 module minimum: 100 genuine completed candles for the existing adaptive technical path.
- Preferred H4 history: 150 candles.
- A symbol with 100–149 genuine completed H4 candles can be calculation-ready in adaptive/degraded mode with a warning/quality reduction.
- Preferred-history shortfall does not become a hard failure when the module's genuine minimum is met.
- Required technical publication rows remain mandatory.
- Optional news/sentiment evidence may be `Not available` / `OPTIONAL_NEWS_UNAVAILABLE` without blanking a valid technical row.
- A run cannot report success when a required exact-symbol row is missing, duplicated, cross-symbol, stale or mixed-timeframe.

## Canonical synchronization and publication transaction

The repaired completion contract validates and publishes one exact generation identity:

- `run_id`
- `generation`
- ordered universe hash
- exact symbol
- exact timeframe
- latest completed candle
- calculation depth
- row checksum
- run checksum
- schema version

Publication flow:

1. Calculate into the existing staging/runtime structures.
2. Validate selected/loaded/completed symbol coverage.
3. Require exactly one Field 10 row for every calculation-ready symbol.
4. Reject duplicate rows and mixed H1/H4 identities.
5. Preserve valid technical rows when optional news is unavailable.
6. Write `field10_symbol_rows`, `symbol_calculation_snapshots` and `canonical_runs` in one database transaction.
7. Mark the run `PUBLISHED` only after validation succeeds.
8. A failed staging generation is not persisted as the new canonical generation; the previous valid generation remains available and must be labeled as previous/stale when used.

Lunch and the consolidated Field 3/10 surface read already-published data. Opening Lunch does not call providers or start calculations.

## Active UI result

Settings now has one authoritative three-selector block inside:

`🔌 Twelve Data Automatic Lunch Connection — Always Visible`

Each selector shows:

- current ordered symbols
- `Load Selected Data`
- `Reload Failed Symbols`
- selected/loaded/failed counts
- genuine row count
- timeframe
- provider
- latest completed candle
- structured failure code/reason
- retry count

The duplicate calculation-profile/explanation block is no longer rendered. The actual three run buttons remain.

The one active Lunch section is:

`Field 3 Higher-Standard Multi-Symbol Bias + Consolidated Field 10 — All Loaded Settings Symbols`

It is closed by default and contains:

- one exact-symbol wide table
- one interactive visualization built from the same DataFrame
- one CSV export of the exact visible table
- one row per loaded symbol
- no separate Field 10 symbol selector
- no active search/cards/duplicate ranking surfaces
- pinned decision-critical columns
- whole-row highlighting for top eligible ranks
- BUY/SELL/WAIT, status, EV, risk, reliability and unavailable-evidence conditional formatting

## Removed-surface to consolidated-column mapping

| Previous visible surface | Reused output in the consolidated table |
|---|---|
| Section 1 latest-run ranking | Final Rank, Higher/less-risky bias, expected returns, combined score, safety veto, calculation status |
| Section 2 four-source technical/fundamental fusion | Technical Score, Fundamental Score, Combined Score, Technical/Fundamental Agreement, Evidence Source |
| Section 3 advanced ranking/decision | Regime Probability, Reliability, transition risks, Expected Value, unexpected status |
| Technical/Fundamental ranking expander | Technical Score, Fundamental Score, Combined Score, agreement/conflict fields |
| Sentiment/high-impact news/absorption rank | Headline, published time, impact, relevance, surprise, absorption status/score, NLP bias/score |
| Crowd psychology rank | Crowd Psychology Bias and conflict/protect evidence |
| Validation/reliability/candidate evidence | Validation Status, Failure Code, Data Quality Grade, Required Minimum, Preferred Rows, Notes |
| Publication transaction diagnostics | Publication Generation, Run ID, Snapshot Checksum Status, Previous Valid Generation Used |
| API budget/provider diagnostics | Provider, Retry Count, Loaded Status, Data Age, failure/retry reason |
| Field 3 quick-look / higher-standard history | Higher-Standard Regime, Higher-Standard Bias, Sample Count, transition risks, reliability |
| Research/integrity registries | Existing evidence remains stored/callable; only decision-useful validated outputs feed the table rather than rendering separate research panels |

The old source builders and evidence tables were retained where they still produce useful data. Their separate user-facing rendering is not called by the active Lunch path.

## Verification commands and results

### Focused regression suite

```bash
PYTHONPATH=. python -m pytest -q tests/test_three_selector_consolidation_20260707.py
```

Result: `16 passed`.

This includes the exact 18-symbol controlled scenario, transient failures, failed-only reload, exact order, no unselected insertions, H4 identity, same loaded universe for all three depths, normalized migration, exact consolidated rows, optional-news behavior and atomic publication.

### Complete test inventory

```bash
PYTHONPATH=. python -m pytest --collect-only -q
```

Result: 558 executable tests across 59 test files.

The repository suite was executed in bounded batches/file-isolated groups because a few legacy research tests retain process resources after completion when many files are chained into one process. Test assertions themselves completed successfully:

- Files 1–10: `96 passed`
- Files 11–20: `146 passed`
- Files 21–30: `111 passed`
- Files 31–40: `79 passed`
- Files 41–50: `72 passed`
- Files 51–59 after the final scenario addition: `54 passed`

Total: `558 passed`, zero assertion failures.

After the final table-formatting change, the affected selector/Field 10 UI subset was rerun:

```bash
PYTHONPATH=. python -m pytest -q \
  tests/test_three_selector_consolidation_20260707.py \
  tests/test_field10_all_selected_repair_20260707.py \
  tests/test_consolidated_field10_settings_repair_20260707.py
```

Result: `26 passed`.

### Repository-wide syntax parsing

Custom AST parse of every Python source file.

Result: `1,256 Python files parsed; 0 failures`.

### Streamlit startup smoke

```bash
streamlit run app.py --server.headless true --server.port 8765 --browser.gatherUsageStats false
```

Result: Streamlit/Uvicorn started successfully and exposed `http://localhost:8765`; no startup import exception was recorded before controlled shutdown.

### Migration smoke

Run twice against a temporary copy of the original uploaded legacy SQLite database, then persist/restore all 18 H4 selections.

Result: PASS; idempotent; all required tables present; 18 exact ordered current rows; H4 identity retained.

### Package integrity

The final ZIP is checked with `unzip -t` and SHA-256 after packaging. The checksum is supplied beside the download link.

## Genuine provider limitations

These cannot be removed by application code:

- Twelve Data quota, endpoint entitlement and supported-symbol coverage depend on the live plan.
- A Finnhub news connection does not prove candle endpoint support for every forex cross, metal or index.
- MT5 requires a running terminal/session, broker symbol availability and correct broker-specific aliases.
- Alpha Vantage has independent quotas and instrument/endpoint restrictions.
- Metals and indices may require provider-specific aliases or exchange-qualified symbols; `NAS100`, `XAUUSD` and `XAGUSD` are not universally accepted in the same form.
- Backoff/batching can respect and recover from transient quota errors; it cannot bypass a provider's plan or unsupported instrument/timeframe.
- The safe demo fallback remains excluded unless explicitly enabled by the user.

When a live provider rejects a symbol, the repaired app retains the selected symbol, records the exact structured failure, leaves successful symbols intact and exposes `Reload Failed Symbols`.

## Security confirmation

- No live secrets were added to source, widgets, logs, exports or the package.
- `.streamlit/secrets.toml` is excluded by `.gitignore` and is not packaged.
- `.streamlit/secrets.example.toml` contains placeholders only.
- The consolidated CSV excludes credential/session secret fields.
- Security regression tests pass.
