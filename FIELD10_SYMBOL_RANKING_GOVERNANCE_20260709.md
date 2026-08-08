# Field 10 Symbol Ranking Governance Upgrade — 2026-07-09

## What changed

This upgrade makes the Field 10 symbol ranking section more stable, reliable, and future-proof without deleting existing production logic.

### 1. One trusted ranking authority

The trusted table remains:

**Open / Close — Field 10 Unified Institutional Daily Rank Authority**

This table is now explicitly ranked by a governed **Authority Score**, not by competing legacy rank tables. Older ranks are preserved as **Legacy Rank** for audit only.

### 2. Future-proof ranking contract

A new configuration-first governance module was added:

`core/field10_rank_governance_20260709.py`

Future ranking tuning should be done by changing `RANK_GOVERNANCE_CONFIG` weights and aliases, not by rewriting UI or Field 10 rendering code.

### 3. Authority Score components

Each symbol now receives transparent scoring columns:

- Authority Score
- Reliability Grade
- Can Trust Rank?
- Trust Status
- Authority Placement
- Risk Control Gate
- Data Completeness %
- Transition Safety %
- Event/Tail Safety %
- Calibration Quality %
- Unique Opportunity %
- Cross-Section Rank Reason
- Rank Freeze Reason
- Rank Governance Version
- Formula Version

The Authority Score uses a stable weighted formula:

- Data quality
- Reliability / calibrated probability
- Expected return / utility evidence
- Transition safety across 1H, 3H, 6H, 12H, 24H, 36H
- Tail and high-impact event safety
- Calibration quality
- Duplicate exposure / uniqueness
- Session robustness

### 4. H4 and selected-timeframe lock

The ranking still uses the selected timeframe refresh gate. If H4 is selected, the trusted ranking is locked to the completed H4 candle and does not change every H1 candle.

The completed-candle detector was improved to avoid freezing the snapshot from the first stale row. It now uses the latest valid row candle and then floors it to the selected timeframe boundary.

### 5. Better placement in the section

The top authority table now shows the governance columns near the front so you can quickly see:

- which symbol is ranked first,
- whether the rank can be trusted,
- whether it is only caution/review,
- why it was ranked there,
- and when it is allowed to refresh.

### 6. Supporting evidence stays supporting only

The second Field 10 table is still only for evidence, vetoes, entry timing, news absorption, session choice, and risk explanation. It cannot override the authority table.

## Files changed

- `core/field10_rank_governance_20260709.py` — new future-proof governance and scoring module.
- `core/field10_unified_authority_20260709.py` — authority ranking now uses governed Authority Score, preserves Legacy Rank, improves completed-candle detection, and adds trust columns.
- `ui/lunch_field10_multi_symbol_20260701.py` — authority table placement improved; governance columns are displayed near the front; visualization options include Authority Score.
- `core/current_result_sync_20260708.py` — current-result visualization now includes Authority Score and trust columns.

## Validation

Passed:

```bash
python -m py_compile core/field10_rank_governance_20260709.py core/field10_unified_authority_20260709.py ui/lunch_field10_multi_symbol_20260701.py core/current_result_sync_20260708.py
pytest -q tests/test_field10_authority_20260709.py tests/test_mobile_export_panel_20260709.py -q
```

Result: `6 passed`.
