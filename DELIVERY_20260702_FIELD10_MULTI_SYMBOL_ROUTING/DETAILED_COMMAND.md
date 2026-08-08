# Copy-and-Paste Development Command

Inspect and upgrade the attached complete Streamlit project. Work directly on the project and return a fully tested ZIP. Preserve every existing protected calculation, decision, table, metric, chart, export, canonical snapshot, run ID, broker-time rule, database and AI behavior unless this command explicitly changes routing or display behavior.

## Primary objective

Convert the system into a flexible but resource-controlled multi-symbol architecture:

1. The symbol selected as **Main Symbol** in Settings owns the complete production calculation.
2. Quick mode must calculate Fields 1–9 + AI only for the main symbol.
3. Full mode must calculate Fields 1–9 + thesis + AI only for the main symbol.
4. Every secondary selected symbol must calculate only Fields 1–3 plus Field 10.
5. Super Quick must calculate Fields 1–3 plus Field 10 for all selected symbols.
6. Never repeat Fields 4–9 or AI for secondary symbols.
7. Use the existing protected `LUNCH_CORE` / Fields 1–3 path for secondary symbols. Do not fake the scope by running everything and hiding rows afterward.
8. Run the main symbol first, cache every child symbol separately, then restore the main symbol when the batch is complete.
9. Publish a scope matrix proving the calculated fields for every symbol.

## Settings requirements

Add or retain these always-visible controls:

- Main calculation symbol selector.
- Additional multi-symbol selector.
- Initial Lunch display symbol selector.
- Quick, Full and Super Quick run-mode choices.
- One authoritative **Run Calculation + Open Lunch** button.

The main symbol must support every valid configured instrument, including symbols other than EURUSD and XAUUSD such as GBPJPY, USDJPY, NAS100 and US500. Provider aliases must resolve only at the connector boundary while canonical identity uses the normalized symbol.

## Connector requirements

For Twelve Data and MT5/Doo bridge:

1. Add **Connect Once Using Saved Settings**.
2. If connector mode, main symbol, selected symbols, timeframe, candle count, API key/bridge endpoint and safe-demo state are unchanged and data is already connected, reuse the saved connection and make no duplicate API request.
3. Add a separate **Refresh Main Feed** action that explicitly forces a new request.
4. A changed API key, bridge URL or token must invalidate reuse and make one fresh connection.
5. Never store or display raw secret values. A transient one-way per-secret digest may be used only to build a composite fingerprint; do not persist raw secrets or standalone per-secret digests.
6. A temporary Lunch symbol switch must never redirect the connector away from the Settings main symbol.
7. Keep duplicate-click protection and persistent connected/error state.

## Lunch symbol selector

Place one authoritative symbol selector at the very top of Lunch, immediately after the Lunch heading and before copy/export controls.

- It must list only completed saved symbol generations.
- Switching must load the compressed saved snapshot and must not call an API or start a calculation.
- Fields 1, 2, 3 and Field 10 must follow the Lunch-selected symbol.
- Fields 4–9 and AI must remain owned by the Settings main symbol.
- When the user leaves Lunch, restore the main-symbol canonical generation before rendering any other page.
- Remove duplicate symbol selectors from Field 10.
- Show main symbol, Lunch display symbol, saved-symbol count and scope status.

## Field 3 requirement

Fix the issue where Field 3 is empty for symbols other than EURUSD or XAUUSD.

- Field 3 must use canonical symbol identity dynamically.
- Remove hardcoded symbol labels from chart titles and export filenames.
- Publish the lifecycle monitor for every selected symbol from its frozen canonical snapshot.
- Reuse an exact-candle Field 3 cache when available instead of forcing a recalculation.
- Add an automated test with GBPJPY as the main symbol and assert that Field 3 status is AVAILABLE and its 25-day history is populated.

## Field 1 Table 5 upgrade

Keep the existing integrated Table 5 calculation unchanged as the source of truth. Add a display-only institutional layer:

- Symbol column.
- Row count, broker-day count, symbol, latest Master Action and average-agreement metrics.
- Search across all columns.
- Master Action filter.
- Display-row limit.
- Column groups: Decision Core; Bias Agreement; Reliability & Outcome; Identity & Audit; Full Audit.
- Master-Action Distribution chart.
- Reliability Through Time chart.
- UTF-8 CSV export.

All filters, charts and downloads must operate on copies. Never mutate protected calculations or source frames.

## Field 10 upgrade

Field 10 must include:

- Main symbol and active Lunch symbol metrics.
- Multi-Symbol Calculation Scope Matrix.
- Run/validation summary.
- Locked Higher-standard regime, rank, data quality and less-risky bias for today.
- Cross-Symbol Allocation and Entry Readiness table.
- Data-quality and reliability comparison visualization.
- Search for run summary, daily rank and hourly history.
- Broker-date, session, regime, data-quality, bias, final-action and rank filters.
- Symbol-specific widget keys to prevent cross-symbol Streamlit state conflicts.
- CSV exports for run summary, daily rank and active-symbol 25-day hourly history.
- Resource report: elapsed time, RSS delta, CPU-time proxy, cache size and fields calculated per symbol.
- Honest failures: never fabricate an empty successful row.

## Performance requirements

- Heavy calculation only after the Settings run button.
- Lunch switching is cache-only.
- Secondary symbols must skip NLP, similar-day intelligence, Fields 4–9 research and AI.
- Reuse exact-candle caches.
- Keep tables lazy/open-close where appropriate.
- Do not add uncontrolled threading or duplicate provider requests.
- Record time, memory, CPU and cache size by symbol.

## Canonical integrity requirements

- One canonical snapshot per child symbol and one parent multi-symbol run ID.
- Preserve symbol, timeframe, completed broker candle, source ID, run ID and snapshot hash.
- Never use local PC time or `datetime.utcnow()` for displayed market identity.
- All displayed history must use the shared broker-time conversion.
- A secondary Lunch selection must not leak into Fields 4–9, AI, Settings connection or another page.

## Testing requirements

Add tests that prove:

1. An arbitrary main symbol runs first with requested scope.
2. Every secondary symbol receives `LUNCH_CORE`.
3. Main symbol scope is Fields 1–9 + AI for Quick/Full.
4. Secondary scope is Fields 1–3 + Field 10 only.
5. Main symbol is restored after the batch.
6. The top Lunch selector is rendered before copy controls.
7. Field 10 has no duplicate symbol selector.
8. Field 1 Table 5 filters, charts and CSV are wired.
9. Connector reuse and forced refresh are separate.
10. Credential or bridge-endpoint rotation invalidates connection reuse without storing secrets.
11. GBPJPY Field 3 publishes populated history.
12. Existing Field 10, Field 3, deployment-guard and syntax tests pass.

Run:

```powershell
python -m compileall -q .
$env:PYTHONPATH = (Get-Location).Path
pytest -q tests/test_field10_multi_symbol_20260701.py tests/test_field3_regime_lifecycle_monitor_20260701.py tests/test_multi_symbol_routing_20260702.py tests/test_deployment_runtime_guards_20260702.py --disable-warnings --maxfail=1
```

If Streamlit is unavailable in the repair container, state that limitation honestly and still run all non-UI logic and static wiring tests.

## Research roadmap

Provide 10 exact advanced quantitative research papers covering:

- Markov regime switching.
- Bayesian online changepoints.
- Adaptive conformal inference.
- Adaptive windows / concept drift.
- Conditional predictive ability.
- Superior Predictive Ability testing.
- Probability of Backtest Overfitting.
- Deflated Sharpe Ratio.
- CVaR optimization.
- Hierarchical Risk Parity.

For every paper provide exact title, authors/year, core concept, mathematical structure, detailed integration into this system, expected benefit and safety/validation guardrail. Treat these as shadow research until chronological out-of-sample promotion gates are passed.

## Delivery

Return:

- Fully upgraded project ZIP.
- Implementation report.
- Test report with exact commands and results.
- Ten-paper research guide.
- Changed-files list.
- SHA-256 manifest.
- No API keys, tokens, passwords, `.streamlit/secrets.toml`, runtime cache, database, `__pycache__` or `.pytest_cache` in the delivered ZIP.
