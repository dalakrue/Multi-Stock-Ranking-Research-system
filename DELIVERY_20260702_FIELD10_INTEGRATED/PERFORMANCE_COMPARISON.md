# Performance Comparison

## Existing required-suite regression timing

| Build | Result | Wall time |
|---|---:|---:|
| Uploaded baseline | 39 passed | 13.88 s |
| Upgraded build, same five required files | 39 passed | 13.32 s |
| Upgraded build + six dedicated suites | 51 passed | 13.56 s |

These test timings are environment observations, not guaranteed production speedups. The scoped feature did not regress the required suite in this run.

## New-feature microbenchmarks

Measured locally with Python 3.13.5; deployment target remains Python 3.12.

| Operation | Measured mean/time |
|---|---:|
| Copy-only Table 5 enrichment, 600 rows | 11.011 ms |
| Heatmap frame preparation, 20 symbols | 7.482 ms |
| SQLite paginated query, 200 of 12,000 rows | 23.046 ms |
| Complete filtered export, 12,000 rows | 236.85 ms |

Baseline values for these exact operations are N/A because the uploaded build did not contain these features. The UI uses closed expanders, bounded visible rows and database pagination. The Plotly figure itself is rebuilt from a cached/prepared copy rather than cached with stale Streamlit state.
