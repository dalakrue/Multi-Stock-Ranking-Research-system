# API Selector and Publication Repair — 2026-07-07

## Scope

This repair addresses the reported H1 multi-symbol failure in which one symbol reached `COMPLETED` while other exact-symbol children stopped at `PARTIAL 97 / FAILED_VALIDATION`, despite having 597 of 600 genuine completed candles. It also repairs selector staleness reporting, adds the two requested six-pair choices to both the First and Second selectors, and makes Finnhub the first/default API source while retaining Twelve Data.

## Root causes found

1. **Secondary Field 3 evidence was calculated but not serialized before publication.** The child runtime snapshot contained only a summary marker, while the immutable Field 10 child bundle required Lower, Middle and Higher standard frames.
2. **Field 1 validation did not recognize current publication aliases.** Valid current artifacts such as `lunch_metric_result_published_20260618` were ignored by the reload validator.
3. **The validation result hid the exact failed gate.** All component failures collapsed into the generic `Failed publication validation` message.
4. **A pure selector-order change was treated like a data-identity change.** Exact symbol/timeframe frames were needlessly marked stale.
5. **The displayed cumulative universe mixed current validated selector data with historical completed-symbol discovery.** Old EURUSD/XAUUSD records could appear in the current selector summary.
6. **The API source selector and legacy startup path still preferred/forced Twelve Data.** A saved Twelve key could override a Finnhub selection.

## Production repairs

- Persist exact-symbol Field 1 Table 4 and the exact-symbol local Field 3 three-standard snapshot before saving each child runtime cache.
- Accept current Field 1 publication aliases during child validation.
- Consume the saved local Field 3 sidecar in the immutable child generation contract without fetching or recalculating during rendering.
- Publish `component_gates` and `failed_components` diagnostics for every failed validation.
- Preserve adaptive H1 eligibility: 597/600 is `ADAPTIVE_PARTIAL_HISTORY`, not fabricated full history.
- Reconcile selector-order-only changes without provider calls; membership or timeframe changes still require an explicit reload.
- Display the current validated loaded universe separately from the historical completed-symbol archive.
- Add exact requested preset arrays to both First and Second selectors.
- Route API priority from `connector_mode`; Finnhub is first/default, Twelve Data remains selectable and may serve as an explicit fallback.
- Stop secure startup from forcing Twelve Data over the selected provider.
- Route the legacy Finnhub connector through the same canonical `MarketDataOrchestrator` used by multi-symbol loading.

## Safety properties retained

- No symbol borrows another symbol's candles.
- No missing candles are padded or cloned.
- Exact symbol and exact timeframe remain part of cache/database identity.
- A run is not marked complete when a mandatory child publication is absent.
- Provider fallback and adaptive coverage remain visible in provenance/status.
- Heavy calculations remain owned by Settings run controls; tab rendering remains read-only.

## Verification

- Focused provider/selector/publication test: 7 passed.
- Broader multi-symbol/connector/publication regression selection: 112 passed, 0 failed.
- Deterministic ten-symbol H4 acceptance remains green.
- Deterministic H1 597/600 child publication now survives cache serialization and reload validation with all Field 1/2/3/10 gates passing.
- `streamlit run app.py --server.headless=true` started successfully.

## Live-provider limitation

No user API key was used in the build environment. Provider behavior is verified through deterministic adapter tests and the production Finnhub/Twelve request paths, but live entitlement, plan coverage, and current provider availability must be confirmed with the user's own credentials.
