# ADX Quant Pro — Final Multi-Symbol Repair Report

**Delivery date:** 2026-07-07  
**Primary entry point:** `app.py`  
**Runtime target:** Python 3.12 (`.python-version` and `runtime.txt`)  
**Repair strategy:** newest load-first/cumulative package retained as the base; strict all-selected-symbol completion and the richer three-section Field 10 surfaces were selectively restored from the stronger earlier package. Existing calculations, ranking formulas, research layers, tables, charts, and data were retained.

## 1. Problems visible in the supplied screenshots

The screenshots showed a consistent publication-chain failure rather than one isolated table defect:

1. The run reached **97%**, but displayed **0 completed / 6 failed** and repeated `Failed publication validation`.
2. A six-symbol selector admitted only one symbol and rejected five, so the calculation never had a valid six-symbol input universe.
3. Field 2 selected an OHLC cache ending at 15:00 while the canonical completed candle was 11:00, causing the production chart to be blocked as stale.
4. Field 3 contained genuine Higher-Standard rows, but several rows were classified as `INSUFFICIENT LOCAL HISTORY`; the child publication validator also failed to recognize valid Field 3 DataFrame/nested-DataFrame containers.
5. Field 10 displayed fallback/L7 cards or missing child tables because successful publication was not proven for every selected symbol from the same parent run.
6. The progress layer could report a nearly complete or successful state without a strict one-row-per-selected-symbol validation gate.
7. The latest package had the stronger load-first workflow but a less complete Field 10 presentation than an earlier uploaded package.

## 2. Implemented repairs

### 2.1 Strict all-selected-symbol completion contract

Added `core/multi_symbol_completion_contract_20260706.py` and integrated it into the run-finalization path.

A run is now successful only when all of these are true:

- every selected symbol has child status `COMPLETED`;
- every selected symbol has an exact-symbol saved runtime cache;
- Field 10 contains one usable row for every selected symbol;
- each Field 10 row has validated rank, direction, quality, and reliability evidence;
- the strict completion result is persisted successfully.

When any condition fails:

- progress is capped at **99%**, never 100%;
- the run remains `PARTIAL`;
- Lunch auto-open is blocked;
- exact symbol-level failure reasons are retained;
- the latest previously complete snapshot is preserved rather than overwritten by partial output.

When all conditions pass, the final state becomes `COMPLETED`, failed count becomes zero, and the exact Field 10 rows are persisted for deterministic reload.

### 2.2 Database migration and deterministic reload

Updated `core/data/deployment_migrations_20260705.py` to schema version `2026070701` and created:

- `multi_symbol_completion_audit_20260706`
- `field10_latest_run_result_20260706`

These tables store the parent run identity, selected universe, child completion counts, visible Field 10 rows, validation status, and exact failure report. The migration is additive and does not delete previous tables or rows.

### 2.3 Multi-symbol loading and quota-safe retry

Updated `core/multi_symbol_load_manager_20260707.py` so each selector load:

- normalizes the requested timeframe consistently;
- validates exact symbol and timeframe identity;
- rejects cross-symbol or cross-timeframe cache reuse;
- requires enough genuine completed candles;
- validates spacing while permitting legitimate market-closure gaps;
- accepts an exact local cache only when it carries an explicit valid-cache status;
- performs unresolved-symbol-only retry rounds;
- temporarily enables quota-safe pacing for multi-symbol loads and restores prior settings afterward;
- performs a final exact SQLite/cache recovery without padding, synthetic rows, or borrowed symbol data.

This directly addresses the screenshot pattern where only the first symbol loaded and the other five were rejected after a provider quota window was exhausted.

### 2.4 Child publication validator repairs

Updated `core/child_snapshot_publication_20260706.py`:

- Field 3 publication validation now recognizes real DataFrames, mappings containing DataFrames, and supported sequences.
- Explicit `FAILED`, `UNAVAILABLE`, `MISSING`, or `INSUFFICIENT` markers still fail.
- No empty or fabricated object is accepted as a valid publication.

This removes false `Failed publication validation` results when Field 3 had genuinely published its standard tables.

### 2.5 Power BI / Field 2 exact-candle repair

Updated `core/powerbi_child_bundle_20260706.py` and `ui/powerbi_cached_renderer_20260619.py`:

- a production `main` DataFrame now counts as a valid projected path;
- causal fallback bundles explicitly carry `ok=True` and a status marker;
- a stored bundle is accepted only when it contains a genuine path;
- the renderer prioritizes the current child bundle and exact canonical completed candle;
- future/fresher aliases are trimmed to the canonical cutoff rather than being selected merely because they are newer;
- canonical cutoff aliases are handled consistently.

The supplied 15:00-versus-11:00 mismatch is therefore resolved by selecting or trimming to the exact 11:00 canonical candle.

### 2.6 Field 10 complete presentation restored

Updated `ui/lunch_field10_multi_symbol_20260701.py` additively. The latest load-first/cumulative interface remains, and the richer earlier Field 10 view is restored as three read-only sections:

1. **Complete Latest-Run Ranking Table** — exact selected-symbol rows from one strict-complete run, plus visible per-symbol validation.
2. **Legacy Four-Source Fusion + Technical/Fundamental Ranking** — technical rank, persisted news/sentiment, eight-session evidence, crowd psychology, reliability, and failure status.
3. **Combined Advanced Ranking and Decision Field** — decision, validation, reliability, risk protection, rank-1 history, high-impact news, absorption, and shadow-candidate audit.

The active-symbol hourly Higher-Standard history, charts, research layers, downloads, and Dinner remainder are still retained below these restored sections.

### 2.7 Progress reporting repair

Updated the progress surface and `core/instant_run_engine_20260705.py` so metrics are recomputed from symbol publication state. The UI now exposes:

- selected, completed, failed, and remaining counts;
- exact publication status;
- available/required candles;
- data-quality result;
- elapsed time;
- validation or failure reason for each symbol.

A stale top-level percentage cannot override an incomplete symbol contract.

### 2.8 Symbol-universe identity repair

Updated `core/multi_symbol_field10_20260701.py` so stale EURUSD widget state cannot replace a newly active canonical symbol. During first-use/fallback identity recovery:

- the canonical symbol becomes main and active;
- the previously selected universe is preserved instead of silently deleted;
- no automatic USDJPY fallback is introduced.

## 3. Files changed

See `CHANGED_FILES_FINAL_REPAIR_20260707.txt` and `SHA256_MANIFEST_FINAL_REPAIR_20260707.json` for the exact list and hashes.

## 4. Validation performed

- Python compile validation for `app.py`, `adx_dashpoard.py`, `core`, `ui`, `tabs`, `services`, `research_quant`, and tests: **passed**.
- Targeted regression suite covering loading, instant runs, multi-symbol routing, selector accumulation, H4 quota behavior, Field 3/Field 10 sync, Power BI exact-candle selection, strict Field 10 row validation, and restored UI: **42 passed**.
- New final-repair tests: **6 passed**.
- SQLite `PRAGMA integrity_check`: **ok**.
- Schema version: **2026070701**.
- Required completion tables: **present**.
- Secret scan over application/config source: no embedded live API key pattern found; only `.streamlit/secrets.example.toml` is included.

The full historical test suite could not be collected in this repair container because the container does not have the `streamlit` package installed. Five UI test modules stopped at import collection for that environmental reason. This is recorded rather than represented as an application failure. The repository requirements still declare Streamlit for deployment.

## 5. Operational behavior after deployment

1. Choose up to six symbols in the relevant selector.
2. Press that selector's **Load Selected Data** button.
3. The loader fetches/reuses only exact-symbol, exact-timeframe evidence and retries unresolved symbols with quota-safe pacing.
4. Review `Loaded & Valid` and rejection reasons. A calculation button consumes only the validated loaded universe.
5. Run the corresponding calculation.
6. The run remains below 100% until every selected symbol has a complete child publication and a usable Field 10 row.
7. On strict success, the complete snapshot is persisted and Lunch can open with the restored full Field 10 surfaces.

## 6. Honest limitation

No software change can guarantee that a third-party provider will return data when an API key is invalid, a market symbol is unsupported, a quota is exhausted, or the provider is unavailable. This repair makes those conditions recoverable and explicit: it retries safely, uses only genuine exact caches, preserves the previous complete snapshot, and reports the exact reason. It never fabricates candles or marks missing evidence as success.
