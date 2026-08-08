# Changed Files — Reliable Quant Upgrade — 2026-07-17

This manifest identifies the files changed for the deterministic Field 10
authority, H4/4H identity, Field 12/13 read-only behavior, append-only
publication, settled-outcome gating, event-risk protection and paper-trade
identity repair.

## Runtime and persistence

- `core/reliable_quant_contract_20260717.py` — canonical symbol/timeframe/candle identity, candle validation, settled target labels, event-risk state, cost-aware expected value, deterministic ranking, promotion gates and immutable trade identity.
- `core/trade_identity_store_20260717.py` — append-only paper-trade identity/event persistence.
- `core/field10_research_migration_20260709.py` — additive schema repair, identity/hash columns, conflict tracking and trade tables.
- `core/field10_unified_authority_20260709.py` — canonical authority identity, read-only restore path, research-only outcome fields and append-only publication.
- `core/system_contract.py` — explicit `INSUFFICIENT_DATA` and `RESEARCH_ONLY` publication statuses.

## Display surfaces

- `ui/lunch_field10_multi_symbol_20260701.py` — Field 10 navigation uses the saved authority/cached display and does not recalculate.
- `ui/lunch_field12_higher_regime_rank.py` — Field 12 is a read-only authority adapter with event, uncertainty, parity and publication status.
- `tabs/field456789_page_20260626.py` — Dinner is a read-only authority adapter.

## Tests and documentation

- `tests/test_reliable_quant_contract_20260717.py` — contract, identity, label, event, ranking, promotion, persistence, display and trade-identity checks.
- `RELIABLE_AUTHORITY_DATA_DICTIONARY_20260717.md` — output and status definitions.
- `RELIABLE_AUTHORITY_FORMULA_REGISTRY_20260717.md` — formula and gate registry.
- `RELIABLE_AUTHORITY_VALIDATION_REPORT_20260717.md` — validation evidence and limitations.
- `DELIVERY_RELIABLE_QUANT_UPGRADE_20260717.md` — delivery summary and verification commands.

## Explicit non-claims

The repair does not create synthetic market data, macro consensus, settled
outcomes, calibration evidence or profitability. Research/model modules remain
shadow-only until their promotion gates are met.
