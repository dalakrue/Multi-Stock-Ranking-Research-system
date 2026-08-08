# ADX Quant Pro — Root Cause Report

Date: 2026-07-06 (Asia/Yangon)

## Executive result

The repair was implemented at code, database, UI, orchestration, test and packaging levels. Existing protected production decision formulas, thresholds, weights and protected Field 1 renderers were not replaced. The repair adds timeframe-aware contracts and publication gates around the existing authoritative calculations.

## Root causes found

### 1. Split timeframe authority

Field 10 accepted an H4 runtime selection, but several publishers and validators still used H1 constants and a fixed 600-row gate. This caused valid 150-candle H4 data to be rejected, mislabeled and occasionally treated as six hours when it represented six H4 bars (24 hours).

**Repair:** `core/timeframe_window_contract_20260706.py` is now the shared contract for bars per day, required lower/middle/higher windows, timeframe seconds, spacing validation and bar/hour conversion. H1 remains 24/120/600; H4 is 6/30/150; D1 is 1/5/25.

### 2. Lunch selector changed state before an explicit load

Fields 1 and 2 used selector state that could be mutated during the same Streamlit rerun as widget creation. They also did not consistently restore a full exact-symbol child publication.

**Repair:** the shared selector now uses a Streamlit form. Selection alone is inert. `Load Selected Symbol` performs a read-only atomic child restore and never invokes a provider or heavy calculation. Widget-owned keys are initialized only before widget creation and are not written afterward.

### 3. Field-10-only rows were treated as if they were full child snapshots

A persisted ranking row could be surfaced even when Field 1 history or Field 2 projection evidence was missing. This produced incomplete canonical identity and cross-symbol display mismatches.

**Repair:** `core/child_snapshot_publication_20260706.py` enforces a full child gate. A Field-10-only row remains available only as the explicitly labeled `PERSISTED_FIELD10_VIEW_READY` partial state. It cannot become a full canonical Field 1/2 publication.

### 4. Worker completion was confused with publication completion

A worker could return and drive progress to 100% while its publication remained partial or invalid.

**Repair:** processing percentage and publication status are separate. The durable symbol state machine records WAITING through COMPLETED/HARD_SOURCE_UNAVAILABLE/FAILED_VALIDATION. COMPLETED now requires exact-symbol data, timeframe validation, Field 1/2/3/10 publication, complete identity, SQLite persistence and successful cache reload validation.

### 5. Field 2 publication was not exact-symbol isolated

After a Lunch symbol switch, the renderer could retain the first symbol's projection bundle. In other cases, Field 2 had no complete run/generation/hash/source identity.

**Repair:** `core/powerbi_child_bundle_20260706.py` freezes a selected-symbol production bundle when present. A fallback is permitted only from the selected symbol's real completed candles, is stored with complete identity, and is explicitly `CAUSAL_DISPLAY_FALLBACK / NOT_CALIBRATED`. Missing provider volume is stored as null, never zero.

### 6. Child restore preserved stale child and Field 10 state

The restore path preserved the previous child-run key and selected-symbol Field 10 frames, causing a newly loaded child to fail exact-symbol reload validation.

**Repair:** atomic restoration no longer carries the previous child identity or selected-symbol Field 10 frames across a child switch. After validation, all Lunch display authorities are synchronized while Settings main symbol and connector symbol remain unchanged.

### 7. Database identity did not isolate timeframes

Legacy tables did not consistently include timeframe, completed candle and full child/canonical identity. H1 and H4 records could collide in older lookup patterns.

**Repair:** the idempotent migration adds timeframe-aware identity aliases and creates dedicated child, Field 2, state-machine and shadow-research tables. Legacy H1 rows are retained and labeled H1 where evidence supports that compatibility alias.

### 8. Field 1 table height was independent of actual row count

This could render a large blank grid when only one or a few legitimate rows existed.

**Repair:** Field 1 display height is based on actual rows. No empty rows are synthesized. Wide tables remain horizontally scrollable and mobile detail cards retain complete values.

### 9. Raw integrity exceptions leaked into the UI

Canonical and projection failures could expose internal exception text.

**Repair:** technical details are logged internally. The UI now shows concise incident references and truthful availability states.

## Protected production logic

The repair does not promote research candidates into production decisions. The ten new research candidates persist only `NOT_PROMOTED` shadow evidence. Existing protected hash tests pass, including the protected Field 1/table verification tests.
