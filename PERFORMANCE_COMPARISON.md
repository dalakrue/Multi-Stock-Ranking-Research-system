# Performance Comparison

## Honest classification

**IMPLEMENTED_NOT_FULLY_VALIDATED.** No end-to-end efficiency improvement is claimed because a comparable pre-change live-provider heavy run was not instrumented.

## Measured read benchmarks

| Measurement | Median | p95 | Peak traced Python memory |
|---|---:|---:|---:|
| Pre-migration direct parent query | 3.188 ms | 5.242 ms | 26222 B |
| Post-migration direct parent query | 3.816 ms | 4.293 ms | 47313 B |
| Post parent contract loader | 20.511 ms | 24.083 ms | 332181 B |
| Post institutional child loader | 49.823 ms | 58.451 ms | 568934 B |

## Verified efficiency controls

- Maximum 600 completed H1 rows per production candidate calculation.
- Exact cache key includes symbol/candle/version/source identity.
- Provider/symbol/time-range reuse remains Settings-owned.
- Child writes are batched in one transaction.
- Lunch performs persisted reads only.
- Large diagnostic models are not loaded by ordinary render reruns.

Heavy-run duration, provider request delta and full-process peak RAM remain **BLOCKED_BY_ENVIRONMENT** because no safe live API/MT5 run was available.

---

## 2026-07-07 operational change

A pure selector-order change now reuses validated exact-symbol/timeframe frames instead of triggering another provider load. Provider source changes are included in the saved-profile signature, preventing reuse of a profile created under a different API source. Finnhub and Twelve Data use the same normalized repository/cache path, so tab renderers do not duplicate provider requests.
