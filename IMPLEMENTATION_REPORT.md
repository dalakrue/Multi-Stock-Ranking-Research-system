# Field 10 Institutional Upgrade — Implementation Report

## Production truth preserved

The authoritative immutable morning ranking remains:

1. `field10_daily_snapshot`
2. `field10_daily_snapshot_symbol`

The new subsystem publishes only normalized child evidence. It never replaces or reranks the parent, and the live safety layer can only downgrade entry permission.

## Runtime call graph

```text
app.py / adx_dashpoard.py
  → core.app.runner.run_app
  → Settings router: tabs/antd_page_router_20260615.py
  → core.multi_symbol_field10_20260701.run_selected_symbols
  → exact selected-symbol calculations and shared candle reuse
  → authoritative parent publisher
       field10_daily_snapshot
       field10_daily_snapshot_symbol
  → settle_matured_forecasts (append-only outcomes)
  → publish_institutional_shadow (versioned child evidence)
  → Lunch renderer
       load_current_daily_snapshot (read-only parent)
       load_shadow_evidence (read-only exact child join)
```

## Implemented architecture

- Canonical identity row keyed to the parent snapshot.
- Append-only forecast and outcome ledgers.
- Hamilton-style support probabilities synchronized to Field 3 regime identity.
- Structural-break and online-change evidence.
- Eight DST-aware session windows using `zoneinfo`.
- Purged chronological Platt/isotonic candidates.
- Split adaptive marginal conformal intervals.
- Versioned experiment registry and blocked promotion state.
- Net EV, risk-adjusted EV, VaR, CVaR, MFE, MAE and reach probability.
- Ledoit–Wolf shrinkage dependence and duplicate-exposure penalty.
- Ten-component reliability with weighted geometric aggregation.
- Deterministic bootstrap rank confidence while preserving original parent rank.
- Mobile-first parent table and exact-status display for blocked/insufficient symbols.

## Requirement classification

| Requirement | Classification | Evidence |
|---|---|---|
| Source/runtime/database audit | **IMPLEMENTED_AND_VERIFIED** | Both entry files resolve to core.app.runner.run_app; call graph and SQLite inventory verified from source/database. |
| Single production authority | **IMPLEMENTED_AND_VERIFIED** | field10_daily_snapshot and field10_daily_snapshot_symbol remain authoritative; no parent row/rank/bias was rewritten. |
| Canonical identity child contract | **IMPLEMENTED_AND_VERIFIED** | New child publications reference daily_snapshot_id, run, broker day/candle, universe and hashes. |
| Immutable forecast ledger | **IMPLEMENTED_AND_VERIFIED** | Append-only table, unique identity, update/delete abort triggers, exact parent foreign key. |
| Immutable outcome ledger | **IMPLEMENTED_AND_VERIFIED** | Separate one-settlement-per-definition ledger with append-only triggers. |
| Hamilton regime support | **SHADOW_ONLY** | Implemented as supporting probabilities synchronized to the parent higher-standard regime; never becomes independent regime truth. |
| Structural-break/changepoint protection | **SHADOW_ONLY** | Causal split/change evidence implemented; severe recent breaks can block new entry without changing morning direction. |
| Eight DST-aware sessions | **SHADOW_ONLY** | ZoneInfo market-local windows and persisted session evidence implemented. |
| Platt/isotonic calibration | **SHADOW_ONLY** | Purged chronological train/validation/test logic implemented; no production promotion. |
| Production calibration evidence | **INSUFFICIENT_HISTORY** | Only two parent broker days and zero settled institutional outcomes are available. |
| Adaptive marginal conformal intervals | **SHADOW_ONLY** | Purged residual calibration and realized test coverage logic implemented; explicitly not conditional-coverage guarantee. |
| Production conformal coverage evidence | **INSUFFICIENT_HISTORY** | No sufficient immutable settled OOS sequence exists. |
| SPA / PBO / Deflated Sharpe | **INSUFFICIENT_HISTORY** | Experiment registry fields and promotion blocking are present; no valid multi-candidate settled trial matrix exists. |
| Net EV / VaR / CVaR / MFE / MAE | **SHADOW_ONLY** | Per-horizon calculation/persistence implemented; net EV stays NULL when spread/slippage evidence is unavailable. |
| Ledoit–Wolf dependence | **SHADOW_ONLY** | Shrinkage covariance, clusters, exposure and duplicate-exposure penalties implemented. |
| Crowd/order-flow proxies | **IMPLEMENTED_NOT_FULLY_VALIDATED** | Existing proxy layer retained and explicitly remains proxy evidence, not institutional positioning. |
| FinBERT/event extraction/event memory | **IMPLEMENTED_NOT_FULLY_VALIDATED** | Existing news/sentiment surfaces retained; the new normalized institutional child contract does not claim full FinBERT/event-memory validation. |
| Hawkes-style event intensity | **INSUFFICIENT_HISTORY** | Schema and explicit insufficient-history records implemented; no intensity is estimated without aligned history. |
| Component reliability architecture | **SHADOW_ONLY** | Ten components plus registered weighted geometric aggregation; missing components are not imputed. |
| Hierarchical candidate utility/rank confidence | **SHADOW_ONLY** | Eligibility, risk penalties, data-quality penalty and deterministic bootstrap confidence implemented; original parent rank preserved. |
| Dedicated migration and rollback | **IMPLEMENTED_AND_VERIFIED** | BEGIN IMMEDIATE, backup/hash/integrity, idempotency and rollback tests passed. |
| Read-only Lunch render | **IMPLEMENTED_AND_VERIFIED** | Render/load paths no longer migrate, fit models, fetch APIs, settle outcomes or publish rows. |
| Incremental/cached heavy-run efficiency | **IMPLEMENTED_NOT_FULLY_VALIDATED** | Exact 600-row bounded input and reuse paths are enforced; no comparable live-provider before/after run was available. |
| Accuracy/profitability improvement | **INCOMPLETE** | No such claim is made because real OOS outcomes are insufficient. |

## Research-method mapping

- Hamilton regime switching: supporting regime persistence/transition probabilities.
- Bai–Perron-style splits and Bayesian online change evidence: structural safety gating.
- Brier score/decomposition, Platt scaling and isotonic regression: probability calibration.
- Adaptive conformal prediction: marginal return intervals and coverage monitoring.
- Hansen SPA, CSCV/PBO and Deflated Sharpe: promotion governance; currently blocked by history.
- Ledoit–Wolf shrinkage: stable multi-symbol covariance/dependence.
- Hawkes-style intensity: reserved shadow schema, not estimated without event history.

## Promotion standard

No candidate was promoted. Promotion requires immutable settled OOS outcomes, registered thresholds, no identity/leakage/integrity issue, adequate subgroup evidence, and successful SPA/PBO/Deflated-Sharpe/calibration/coverage gates.

---

# 2026-07-07 API Selector and Child Publication Repair Addendum

This pass repaired the reported 597/600 H1 secondary-child publication failure without changing protected rank formulas. Exact-symbol Field 1 and all three local Field 3 standards are now saved before the runtime snapshot is published; child validation recognizes current Field 1 aliases and reports per-component gates. Selector order-only changes no longer force a reload, while membership/timeframe changes still do. Finnhub is the first/default selectable market-data source and Twelve Data remains available as a selected provider or fallback.

Detailed evidence: `API_SELECTOR_PUBLICATION_REPAIR_20260707.md`.
