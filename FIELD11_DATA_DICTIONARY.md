# Field 11 Data Dictionary

Field 11 is the persisted historical-similarity/path surface. The existing implementation is read from `core/field11_similar_path_simulator_20260702.py` and rendered by `ui/lunch_field11_similar_path_20260702.py`.

| Field | Meaning |
|---|---|
| Symbol / Timeframe | Exact child market identity. |
| Qualified Analogue Count | Historical windows surviving causal filters. |
| Best / Median / Weighted Similarity | Similarity evidence across qualified paths. |
| Effective Sample Size | Weight-adjusted amount of usable analogue evidence. |
| Direction Agreement | Weighted agreement of analogue endpoints; not a guaranteed probability. |
| Regime / Session Match | Compatibility with current regime and session context. |
| Endpoint P10/P25/P50/P75/P90 | Weighted endpoint distribution quantiles. |
| Weighted Median Endpoint | Central analogue endpoint estimate. |
| Median MFE / MAE | Typical favorable/adverse excursion of matched paths. |
| Path Dispersion | Uncertainty across analogue paths. |
| Reliability / Feature Coverage | Evidence completeness and stability. |
| Drift Status | Whether current features are outside stable historical support. |
| Analogue Rank | Relative analogue opportunity inside the persisted universe. |

A chart selector may change the displayed symbol, but it must not change which symbols were calculated.
