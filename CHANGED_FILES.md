# Changed Files

The list below contains files added or modified for this delivery. Historical parent calculations and tables were retained.

| File | Purpose | SHA-256 |
|---|---|---|
| `core/field10_institutional_shadow_20260704.py` | Institutional child calculations/publication/settlement/read loader. | `87983e88fd822e48134fa95ded12716d65b51ca32e7e2df3e3c8853ffeb174db` |
| `core/sqlite_readonly_20260704.py` | Fail-closed SQLite read-only helper. | `ab2956ae8907c59693c5ce160df461d3a5db77c5d91ceffce9e3c7a2df743bb0` |
| `scripts/migrate_field10_institutional_20260704.py` | Dedicated transactional migration and verification CLI. | `6a376e2f3a2bd7f91db9555e1894ecdf26cb676dd83f317be741a5d4188076d0` |
| `tests/test_field10_institutional_shadow_20260704.py` | Twenty new causal, integrity and immutability tests. | `046c6235a75edb6608568cced44c834eebcc31839c642b9231f8563a329c5b58` |
| `core/field10_daily_snapshot_contract_20260702.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `4c6ae5360c59c52ba0d178694a2c62359595ff989dfe82be2f5cd7de98bb7bc0` |
| `core/child_generation_contract_20260702.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `2f3d1c0a86ead3f9a40f2a57294e34cc380a1c82e936417e57de98b4da799f74` |
| `core/field10_daily_outcome_settlement_20260702.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `2a00d378d51d452aee31eca4792eff8a3b380b405d69c51e13873b4eda2b6112` |
| `core/field10_integrated_evidence_20260702.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `67b9623b672a9d418815531ed6a160a3ce5917defbb39d46cb43e828127f9fa1` |
| `core/field10_live_safety_veto_20260702.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `120db19607629ec264468dddf680ea07c344d766a4e199278f2344320503b7a5` |
| `core/field10_ten_paper_research_20260701.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `3b0cd8e2039a647f08ee2be29a7b21e01de722e06e5c65f940cd958733eb1e45` |
| `core/multi_symbol_field10_20260701.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `bce02683f20055fab5d74007e2d0e4febb0b4c1de1e0a301c775be99037c7d05` |
| `core/multi_symbol_api_runtime_20260702.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `7176df90f326c109b8ee2e0e88a00a20d01d64116e8c6822aa637bde701fe5c6` |
| `core/startup_lunch_orchestrator_20260704.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `846fb54ed69cf1507b457f61f092fe91dd2d111b273d7a739dab1fac87094b95` |
| `core/field10_crowd_final_20260704.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `85a4a07eb560028940e0ad2ed8dcb16ec789994b228d0978dfe6762c471314b5` |
| `core/field11_similar_path_simulator_20260702.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `2a9778ae28c8d0c116a9a88bda02dd45d5b64fc6f55cd3244c2095c590c8f2f2` |
| `core/similar_day_intelligence_20260619.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `83640e0413dbf043c288c13120140372c4f9853518e58b55afb182066ab002ec` |
| `ui/lunch_field10_multi_symbol_20260701.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `2e563228618e1611cf6d82fbbe187d680d67fa65a364a55b4383e5bd3db86468` |
| `ui/lunch_four_core_fields_20260619.py` | Read/write boundary, orchestration, synchronization, UI or compatibility update. | `ce4b7c495899c0b1fcabb2670a1f74e64c0765d89721df69d1ddee6e2ddf051d` |
| `data/multi_symbol_field10_20260701.sqlite3` | Non-destructively migrated production database. | `cc1e2560d278ce83474eb7eadbe7f5ea1302bb8d02ff83e77e8a29f5ce45a947` |

---

## 2026-07-07 API selector/publication repair

- `core/data/market_data_orchestrator.py` — selected-provider priority, Finnhub-first routing, truthful fallback status.
- `ui/sidebar_fallback_panel.py` — Finnhub-first source choice, provider-aware connection state and saved-profile signature.
- `tabs/antd_page_router_20260615.py` and compatibility source part — Finnhub-first emergency source choice.
- `ui/multi_symbol_settings_20260701.py` — two exact six-pair choices in First and Second selectors; current validated universe separated from historical archive.
- `core/multi_symbol_load_manager_20260707.py` — order-only reconciliation without refetch; explicit stale-change details.
- `core/multi_symbol_field10_20260701.py` — persist exact Field 1 and Field 3 child evidence before runtime-cache save; richer rejection diagnostics.
- `core/child_generation_contract_20260702.py` — consume persisted exact-symbol local Field 3 standards.
- `core/child_snapshot_publication_20260706.py` — current Field 1 aliases and component-gate diagnostics.
- `core/connectors/data_parts/session.py` — Finnhub legacy surface routed through canonical orchestrator.
- `core/secure_api_startup_20260619.py` — no forced Twelve override; selected-provider key resolution.
- `core/app/refresh.py` — Finnhub/Twelve provider status and credential restore tracking.
- `tests/test_api_selector_publication_repair_20260707.py` — deterministic regression coverage.
- New/updated architecture, contract, data dictionary, governance, test and repair reports.
