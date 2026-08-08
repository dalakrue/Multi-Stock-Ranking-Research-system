# Architecture — Canonical Multi-Symbol Ranking

## Execution path

`app.py` → `core.app.runner.run_app` → Settings selectors/load manager → shared market-data orchestrator → per-symbol child calculation → immutable child publication → canonical Field 10 ranking/history → read-only tab renderers.

## Universe contract

The calculation universe is the ordered unique union of the three **currently loaded and validated** selector records. Configuration alone is not calculation eligibility. Each child carries symbol, timeframe, provider symbol, completed candle, source identity, snapshot hash, generation and calculation status.

## Provider layer

`core/data/market_data_orchestrator.py` owns normalized exact-symbol candles. The selected API source controls primary ordering. Finnhub is the default primary; Twelve Data, MT5, Alpha Vantage and the exact local cache remain explicit alternatives/fallbacks. All returned frames are normalized and persisted under symbol+timeframe identity.

## Publication layer

Each child saves the already-calculated Field 1, Field 2 and Field 3 evidence before immutable publication. The child publication validator exposes each gate separately. Field 10 publication is database-backed and reload-safe. Renderers restore persisted snapshots and do not refetch or calculate on navigation.

## Completion rule

Processing percentage and publication completion are separate. A child can be 100% processed but remain failed/degraded if a required artifact is absent. The parent run completes only when every loaded symbol has an explicit final publication status and no mandatory child is silently omitted.

## Degraded history

A statistically eligible partial history is published as adaptive/degraded evidence with reduced coverage. It is never presented as 600/600 and never created from another symbol.
