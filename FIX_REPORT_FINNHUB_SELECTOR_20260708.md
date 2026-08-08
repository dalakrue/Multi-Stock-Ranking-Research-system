# Finnhub Active Provider + Three-Selector Repair — 2026-07-08

## Implemented provider policy

- Finnhub is the configured active market-data provider.
- Twelve Data is retained as the first live fallback provider.
- Legacy saved `connector_mode=twelve` profiles are migrated to Finnhub-first routing rather than promoting Twelve Data back to active.
- Configured provider roles are stored separately from the provider actually used for a request. A successful Twelve fallback therefore does not overwrite the active-provider setting.
- MT5, Alpha Vantage, and exact-symbol validated local cache remain downstream fallbacks.

## Multi-symbol selector repair

- First Multi-Symbol Selector capacity: **12 symbols**.
- Second Multi-Symbol Selector capacity: **6 symbols**.
- Third Multi-Symbol Selector capacity: **6 symbols**.
- UI controls, session state, persisted preferences, load records, retry records, cumulative universe logic, and calculation activation now use the same explicit 12/6/6 limits.
- Removed the hidden shared six-symbol truncation that could discard First-selector symbols and destabilize Second/Third selector loads.
- Second and Third selectors retain their own widget-owned order and no longer restore stale/deleted selections on rerun.

## Faster loading

- Finnhub-primary multi-symbol loads no longer use Twelve Data's forced 60-second quota stagger.
- Load-only collection uses two bounded rounds for Finnhub instead of four.
- Each provider receives one attempt before fallback during explicit selector loading, while exact-symbol validation and unresolved-only retry behavior are preserved.
- Twelve Data requests are still quota-managed and paced only when Twelve is actually used as fallback.
- All calculations, ranking formulas, publication rules, and exact symbol/timeframe identity checks remain unchanged.

## Validation

- Python compile check passed for live core, UI, tabs, and tests.
- V9 reconstructed Settings router source compiled successfully.
- Focused regression suite: **27 passed**.
- Tests cover Finnhub primary success, Twelve fallback, legacy provider migration, 12/6/6 capacity, exact Second/Third selector loading, no Finnhub stagger, reduced fetch rounds, state cleanup, and cumulative group behavior.
