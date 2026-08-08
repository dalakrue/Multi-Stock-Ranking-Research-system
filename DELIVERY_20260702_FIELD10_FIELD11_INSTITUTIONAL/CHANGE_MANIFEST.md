# Change Manifest

No existing production file was deleted.

| Status | File | Purpose |
|---|---|---|
| ADDED | `core/field11_similar_path_simulator_20260702.py` | Historical index, identity guard, constrained-DTW hybrid matching, scenario clustering, persistence and settlement. |
| ADDED | `ui/lunch_field11_similar_path_20260702.py` | Field 11 local-state selectors, mobile-first metrics, Plotly projector and audit/history tables. |
| ADDED | `tests/test_field11_similar_path_simulator_20260702.py` | 24 Field 11 contract, leakage, state, persistence, settlement and mobile tests. |
| MODIFIED | `ui/lunch_four_core_fields_20260619.py` | Adds Field 11 to the authoritative Lunch selector; preserves closed-first behavior and Fields 1, 2, 3 and 10. |
| MODIFIED | `core/multi_symbol_field10_20260701.py` | Invokes Field 11 index preparation and matured-outcome settlement only after authoritative Field 10 publication in the existing Settings-owned run. |
| MODIFIED | `tests/test_requested_acceptance_20260626.py` | Updates the obsolete four-field assertion to the requested five authoritative Lunch fields and verifies Field 11. |
| MODIFIED | `VERSION.txt` | Adds the additive Field 10 + Field 11 build identifier while retaining the prior version record. |
| ADDED | `DELIVERY_20260702_FIELD10_FIELD11_INSTITUTIONAL/*` | Architecture, schemas, manifests, validation, tests, deployment, rollback and disclosure. |

### Preserved production path

`app.py` → existing router/settings calculation → canonical shared result → multi-symbol Field 10 transaction → immutable Field 10 publication → Field 11 prepared index. The Field 11 renderer is read-only with respect to market acquisition and Fields 1–10.
