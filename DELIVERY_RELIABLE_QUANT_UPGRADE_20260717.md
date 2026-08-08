# Reliable Quant Upgrade Delivery — 2026-07-17

## Result

The supplied project now has a canonical, deterministic Field 10 authority
contract. H4 and 4H resolve to one timeframe identity; all completed-candle
identity is UTC-based; Field 10 publishes append-only snapshots; Field 12,
Field 13 and Dinner load the saved authority instead of recalculating it while
their screens are opened.

## Reliability controls added

- Exact ordered symbol-universe and completed-candle identity.
- No padding, future rows, incomplete candles, duplicate candles or invalid OHLC in the contract validator.
- Settled target labels use only future completed candles; unresolved targets remain unsettled.
- Insufficient settled outcomes publish `UNAVAILABLE` / `SHADOW_ONLY`, never a fabricated probability or promotion.
- CPI/PPI-style missing timing, missing actual or missing consensus blocks trade permission.
- Expected net value includes spread, slippage, event, uncertainty, tail and dependency penalties.
- Paper-trade entry identity is frozen; later updates append events and cannot mutate the selector/timeframe/candle identity.
- Cross-device parity is explicitly `CROSS_DEVICE_PARITY_UNVERIFIED` unless a shared authority URI is configured.

## Verification

- `python -m compileall -q .` — PASS.
- Contract smoke checks — PASS.
- H4/4H same-candle restore with changed source — PASS.
- Append-only duplicate/conflict behavior — PASS.
- Read-only display-path checks — PASS.
- Settled labels, event gate, ranking, promotion and trade identity checks — PASS.
- Full `pytest` suite — not run because `pytest` is not installed in the supplied runtime.

## Data and deployment limitations

The supplied database has no settled Field 10 outcomes or promotion decisions
in the inspected current tables. Accordingly, this delivery makes no claim of
accuracy, profitability, calibration, PBO, SPA, Deflated Sharpe or production
readiness. Install the declared dependencies and run the full test suite in the
deployment environment before release.

See `RELIABLE_AUTHORITY_VALIDATION_REPORT_20260717.md` and
`CHANGED_FILES_RELIABLE_QUANT_20260717.md` for the evidence and file manifest.
