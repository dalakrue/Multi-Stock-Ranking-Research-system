# Exact Changed Files

| Change | File | Purpose |
|---|---|---|
| ADDED | `core/field10_integrated_evidence_20260702.py` | Table 4 publication bridge, integrated SQLite history/current loaders, Table 5 enrichment, shadow validation adapters, heatmap preparation. |
| ADDED | `core/multi_symbol_api_runtime_20260702.py` | Exact-candle provider request key, bounded retry classification, shared-profile reuse and secret-free request audit. |
| MODIFIED | `core/multi_symbol_field10_20260701.py` | Runs API dedup preparation, publishes Table 4 after each frozen symbol snapshot, syncs ranks/research, records request/cache/database metrics. |
| MODIFIED | `core/field10_ten_paper_research_20260701.py` | Moves the documented trigger from Field 10 opening to the explicit Run Calculation transaction; rendering remains read-only. |
| MODIFIED | `ui/lunch_next_hour_bias_history_20260626.py` | Extracts reusable protected Table 4 publisher; adds copy-only Table 5 quant validation, metrics, filters and enriched CSV. |
| MODIFIED | `ui/lunch_field10_multi_symbol_20260701.py` | Adds current integrated table, paginated 25-day history and one Plotly evidence-alignment heatmap; removes calculation from Field 10 rendering. |
| ADDED | `tests/test_field1_table5_quant_enrichment.py` | Protected-source immutability, unresolved-outcome and 25-day tests. |
| ADDED | `tests/test_field10_table4_publication_bridge.py` | Publisher reuse and duplicate-rejection tests. |
| ADDED | `tests/test_field10_integrated_evidence_history.py` | Persistence, pagination, schema and index tests. |
| ADDED | `tests/test_field10_evidence_heatmap.py` | Copy-only encoding, null handling and rank-order tests. |
| ADDED | `tests/test_secondary_symbol_shared_sentiment.py` | Shared-news projection labeling and unavailable-evidence tests. |
| ADDED | `tests/test_multi_symbol_api_request_deduplication.py` | Exact-candle cache, force refresh, profile invalidation and retry-classification tests. |

No protected file was deleted or renamed. Runtime databases, cache files and Python bytecode are excluded from delivery.