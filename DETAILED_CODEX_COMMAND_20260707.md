# Detailed Command for a Future Codex Repository Repair and Quant Upgrade

Copy and paste the command below into Codex while the repository is open.

---

Perform a complete repository inspection, repair, validation, and packaging pass for this ADX Quant Pro Streamlit system. Work directly inside the current repository and implement actual code changes. Do not provide only a report.

## A. Non-negotiable preservation rules

1. Inspect the complete repository before editing. Trace the real `app.py` entry point, imports, page router, Settings run buttons, three multi-symbol selectors, load manager, calculation orchestrator, canonical snapshot flow, child publication, Field 1, Field 2, Field 3, Field 10, SQLite schema, caches, API connectors, and all renderers.
2. Preserve every existing calculation, ranking formula, model, column, table, chart, expander, download, history surface, research layer, database row, and API connector unless a change is required to fix a proven defect.
3. Do not delete, rename, weaken, simplify, or replace existing logic. Make additive, backward-compatible changes.
4. Do not fabricate candles, predictions, news, sentiment, reliability, expected return, or validation results.
5. Never borrow one symbol's OHLC, regime, reliability, or Field 10 row for another symbol.
6. Preserve the first selected/main symbol. Do not silently fall back to USDJPY or EURUSD when another canonical symbol is active.
7. Keep Python 3.12, Streamlit Cloud compatibility, mobile-safe rendering, and `app.py` as the primary entry point.
8. Do not add API keys, secrets, credentials, tokens, or local absolute paths to the repository.

## B. Inspect and merge the strongest uploaded implementations

1. Compare all supplied ZIP packages by content, not just filename or modification time.
2. Use the newest load-first/cumulative package as the architectural base.
3. Selectively restore the strict all-selected-symbol completion contract and the richer three-section Field 10 presentation from the earlier package that displayed more complete results.
4. Merge functions, schemas, and renderers at the code level. Do not replace the entire repository with an older version.
5. Produce a merge report identifying which implementation supplied each retained feature.

## C. Three selector load-first workflow

For First, Second, and Third Multi-Symbol Selector:

1. Keep a maximum of six symbols per selector.
2. Each selector must have its own `Load Selected Data` button.
3. Loading must normalize symbol and timeframe identity and fetch only genuine data for that exact symbol/timeframe.
4. Validate required completed-candle count, OHLC validity, duplicate timestamps, and selected-timeframe spacing.
5. Permit legitimate exchange-closure gaps only when every observed gap is at least one selected-timeframe candle.
6. Reject cross-symbol, cross-timeframe, synthetic, padded, or unvalidated cache data.
7. Use provider priority and unresolved-only fallback across supported connectors.
8. Add quota-safe batching and retry. For six-symbol loads, avoid firing all requests into an eight-credit rolling window. Temporarily pace requests, retry only unresolved symbols, then restore the user's previous runtime settings.
9. Perform a final exact local SQLite/cache recovery only when the cache has a valid identity and enough genuine candles.
10. Show a per-symbol load table containing symbol, provider, available candles, required candles, spacing status, data quality, loaded/rejected status, and exact reason.
11. The related calculation button must consume only that selector's successfully loaded universe. It must not start another hidden load or API call.
12. Preserve selected order. Do not silently remove selected symbols from the UI; show rejected symbols and reasons clearly.

## D. Strict calculation and publication contract

Implement or verify one strict completion contract for every run:

1. Every selected/loaded symbol must publish a complete child snapshot from the same parent run.
2. Every child must contain exact identity: parent run ID, child run ID, symbol, timeframe, generation ID, completed broker candle, source ID, and snapshot hash.
3. Child validation must recognize current production containers, including DataFrames and mappings that contain DataFrames.
4. Field 2 must contain a genuine production or causal fallback projection path.
5. Field 3 must contain genuine Lower, Middle, and Higher Standard evidence. Preserve all raw history tables.
6. Field 10 must contain exactly one usable visible row for every selected symbol. Each row needs rank, direction/bias, data quality, reliability, and valid status.
7. Persist completion audit and latest-run rows transactionally in SQLite.
8. Report 100% only after all selected symbols and all required publication components pass and persistence succeeds.
9. When incomplete, cap progress at 99%, set status `PARTIAL`, keep Lunch closed, preserve the latest previous complete snapshot, and show exact symbol/component failure reasons.
10. Do not display “completed successfully” while any selected symbol is missing, rejected, insufficient, stale, or unvalidated.

## E. Field 2 / Power BI integrity

1. Trace every Power BI cache alias and child bundle.
2. Treat a production `main` DataFrame as a valid path when nonempty and correctly identified.
3. Reject bundles with no genuine path.
4. Select OHLC from the active exact child/canonical snapshot, not merely the freshest alias.
5. Trim candidate OHLC to the canonical completed broker candle and require the final candle to match exactly.
6. Synchronize Field 2 candle time with Fields 1, 3, and 10 through the shared broker-time provider.
7. Retain all existing chart paths, bands, metrics, controls, and history.
8. Display integrity diagnostics when a mismatch remains. Never silently relabel stale data as current.

## F. Field 3 integrity

1. Preserve Lower, Middle, and Higher Standard raw tables and histories.
2. Keep exact-symbol evidence; never borrow another symbol's row.
3. Make data-quality, sample count, regime probability, reliability, transition risk, expected return, evidence source, and completed candle visible.
4. `INSUFFICIENT LOCAL HISTORY` must appear only when the exact required history is genuinely absent, with available/required counts.
5. Ensure child publication recognizes real DataFrames and nested DataFrame containers.
6. Keep all selected completed symbols in the all-symbol Higher-Standard table.

## G. Restore full Field 10 without deleting newer behavior

Additively restore these read-only sections from the strongest earlier package:

1. Complete Latest-Run Ranking Table with one row per selected symbol and visible validation.
2. Legacy Four-Source Fusion + Technical/Fundamental Ranking, including persisted technical evidence, news/sentiment/absorption, eight-session evidence, crowd psychology, reliability, and failure status.
3. Combined Advanced Ranking and Decision Field, including rank history, high-impact news, absorption, validation, reliability, risk protection, and shadow-candidate audit.

Also retain the newest package's cumulative selector behavior, active-symbol hourly Higher-Standard history, all charts, downloads, research layers, and Dinner remainder.

Field 10 must remain read-only in Lunch. It may load persisted data but must not call an API, recalculate Fields 1–9, or fabricate absent child rows.

## H. Canonical symbol and time identity

1. Maintain one canonical snapshot per completed run.
2. When stale widget state conflicts with the canonical child, promote the canonical symbol to main and active while preserving the user's previously selected universe.
3. Every Field 1/2/3/10 row and chart must carry or resolve to the same run ID, generation ID, timeframe, symbol, and completed broker candle.
4. Prevent stale state from one symbol contaminating another child activation.

## I. Advanced quant research architecture — shadow only

Implement scaffolding and reports, not automatic production influence, for:

1. Hamilton Markov-switching regime probabilities.
2. Engle Dynamic Conditional Correlation.
3. Corsi HAR-RV volatility term structure.
4. Rough-volatility shock/roughness estimation.
5. Hansen–Lunde–Nason Model Confidence Set.
6. Weighted conformal prediction under covariate shift.
7. Probability of Backtest Overfitting / CSCV.
8. Deflated Sharpe Ratio.
9. Almgren–Chriss-inspired execution-cost and permission layer.
10. Hierarchical Risk Parity.

Each module must:

- read only completed canonical snapshots;
- use no future data;
- write separate versioned shadow tables;
- declare assumptions, sample size, source IDs, timestamps, and failure reasons;
- have no production effect by default;
- include walk-forward, purging/embargo, calibration, PBO, DSR, MCS, and rollback evidence before promotion.

## J. Database and migration requirements

1. Use additive, idempotent migrations.
2. Use WAL, busy timeout, transactions, and indexes for run/symbol/time lookups.
3. Never drop or rewrite historical tables.
4. Add completion-audit and exact latest-run-result tables when absent.
5. Run `PRAGMA integrity_check` and report the result.
6. Ensure schema initialization works on a clean Streamlit Cloud deployment.

## K. Testing and acceptance criteria

Create or update tests proving all of the following:

1. Exact-symbol valid cache is accepted after a transient provider failure.
2. Cross-symbol and cross-timeframe cache is rejected.
3. Insufficient candle history is rejected with available/required counts.
4. Valid nested Field 3 DataFrames pass publication validation.
5. Explicit unavailable Field 3 markers fail.
6. A production Power BI `main` path passes validation.
7. A fresher OHLC alias cannot override an exact canonical completed candle.
8. Field 10 incomplete/fallback rows fail the strict contract.
9. One complete row per selected symbol passes the contract.
10. Progress is 100% only when every selected symbol passes.
11. Previous complete snapshot remains available after a partial run.
12. Canonical symbol repair preserves prior selected symbols and makes the canonical symbol main/active.
13. The restored three-section Field 10 and newer cumulative surfaces both remain present.
14. Python compile validation succeeds.
15. Existing targeted multi-symbol, Field 3, Field 10, selector, quota, and instant-run tests pass.

Do not hide failed tests. Distinguish application failures from missing test-environment dependencies.

## L. Required deliverables

Produce:

1. A fully repaired ZIP of the complete repository.
2. `FINAL_REPAIR_REPORT_YYYYMMDD.md`.
3. `TEN_ADVANCED_QUANT_RESEARCH_PAPERS_YYYYMMDD.md`.
4. `DETAILED_CODEX_COMMAND_YYYYMMDD.md`.
5. `CHANGED_FILES_FINAL_REPAIR_YYYYMMDD.txt`.
6. `TEST_RESULTS_FINAL_REPAIR_YYYYMMDD.txt`.
7. A SHA-256 manifest for all changed and added files.
8. A secret scan result.

Before packaging, remove `__pycache__`, `.pytest_cache`, `.pyc`, temporary files, and any real secrets. Keep `.streamlit/secrets.example.toml` only.

At completion, state precisely what was changed, what passed, what could not be live-tested, and why. Do not claim that external APIs will always succeed; guarantee only that the system retries safely, validates exact evidence, preserves complete snapshots, and never reports missing data as success.
