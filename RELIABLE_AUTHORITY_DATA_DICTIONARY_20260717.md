# Reliable Authority Data Dictionary — 2026-07-17

This contract is additive to the existing Field 10/Field 3 schemas. Field 10
remains the canonical rank publisher; Field 12 and Field 13 are read-only
display adapters.

## Snapshot identity

| Field | Meaning | Rule |
|---|---|---|
| `authority_key` | Hash of the complete publication identity | Changes when symbol, ordered universe, timeframe, candle, provider/source, revision, schema, model, or formula changes |
| `canonical_symbol` | Canonical primary symbol | Normalized uppercase symbol identity |
| `provider_symbol` | Symbol sent to the selected provider | Never silently substituted by another symbol |
| `timeframe` | Selected timeframe | `4H` and `H4` normalize to `H4` |
| `broker_timezone_policy` | Explicit broker/session-time policy | UTC is used internally; local device time is not a candle identity |
| `completed_broker_candle` | Selected-timeframe completed candle watermark | UTC-normalized and floored to the selected timeframe |
| `ordered_symbol_universe` | User-selected symbols in canonical order | Order is part of the authority identity |
| `universe_hash` | Hash of the selected universe | Supports exact restore checks |
| `provider`, `source_id` | Data provenance | A fallback provider must be recorded |
| `source_snapshot_hash`, `data_revision` | Point-in-time source identity | Prevents an untracked source revision from appearing identical |
| `feature_schema_hash` | Feature-column contract hash | Changes when feature inputs change |
| `model_version`, `formula_version` | Model and formula lineage | Required for promotion/audit |
| `cross_device_parity_status` | Whether a shared authority is configured | Local SQLite reports `CROSS_DEVICE_PARITY_UNVERIFIED` |

## Decision and risk fields

| Field | Meaning | Safe interpretation |
|---|---|---|
| `Direction Bias` | Directional display result | Not a trade permission |
| `Probability 100 Pip Move 4H` | Existing fixed 100-pip/H4 overlay | Legacy heuristic only; not a settled probability |
| `Probability Target Reached` | Estimated target-reach probability | Published only from settled future outcomes with sufficient sample |
| `Probability Target Reached Status` | Outcome evidence state | `INSUFFICIENT_SETTLED_OUTCOMES` remains research-only |
| `Expected MFE`, `Expected MAE` | Settled or explicitly supplied excursion evidence | Unavailable values remain unavailable |
| `Expected Net Value` | Cost-adjusted utility | Requires probability, MFE and MAE; spread/slippage/event/uncertainty penalties are separate inputs |
| `Uncertainty` | Forecast uncertainty | Never collapsed into a safe neutral value |
| `Event Risk`, `Event Risk Permission` | Scheduled event state and gate | CPI/PPI uncertainty, pre-event, unconfirmed release and shock windows block permission |
| `Data Quality Grade` | Data completeness/quality | Failed or unknown data cannot be trusted |
| `Can Trust Rank?` | Rank trust display | Separate from direction and trade permission |
| `Trade Permission` | Production/paper-trade gate | `BLOCK_RESEARCH_ONLY` when settled outcomes are insufficient |
| `No-Trade Reason` | Human-readable blocking reason | Must explain the active gate |
| `publication_mode` | `PRODUCTION_READY` or `RESEARCH_ONLY` | New research models remain shadow-only |

## Immutable publication rule

The authority snapshot and symbol rows are inserted append-only. An identical
republication is idempotent. A different payload using an existing immutable
snapshot identity is rejected and recorded as `CONFLICT_REJECTED`; the original
rows are not deleted or overwritten.
