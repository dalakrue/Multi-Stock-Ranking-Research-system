# Streamlit State, H4, API Auto-Connect, and Quota-Pacing Repair

## Implemented repairs

- Fixed `StreamlitAPIException` for `multi_symbol_searchable_selector_widget_20260701` by separating canonical symbol selection from the widget-owned session key. Widget values are now staged only before `st.multiselect` is instantiated.
- Removed the second hidden mutation path in runtime selection synchronization.
- Fixed the same likely hidden failure pattern in Lunch Previous/Next navigation. The selectbox now consumes a pending selection before widget creation instead of changing its own key after rendering.
- Audited the active Settings and Lunch renderers for literal/dynamic widget-key writes after widget instantiation; no remaining matches were found in the active files.
- Changed the first-load/runtime/default connector timeframe from H1 to H4. Older persisted selection profiles are upgraded through a new profile version so a stale H1 preference cannot override the new first-load H4 default.
- Changed fresh Guest/account login routing to Settings. Startup no longer forces Lunch or starts a heavy calculation.
- Added authenticated, idempotent startup connection for deployment-secret Twelve Data and Finnhub credentials. Twelve Data is connected as Twelve Data (not a stale prior connector mode), and Finnhub uses its existing validate/connect path. Raw secrets are not copied into UI output or saved profiles.
- Added real quota-safe live-provider pacing for Super Quick: at most five Twelve Data attempts in a rolling 60-second batch, then the next five. Exact-candle cache hits do not consume a live request slot.
- Added a two-to-four-minute orchestration target for a live 10-symbol Super Quick run. The four-minute boundary is a safety budget: if provider/network or existing calculations exceed it, remaining symbols are preserved as partial/deferred instead of allowing an uncontrolled long or duplicate provider run.
- Propagated H4 through Settings, connection validation, market-data preparation, the multi-symbol calculation transaction, canonical identity, Lunch Fields 1–3, Field 10/11 orchestration, and Field 3 regime windows.
- Preserved 1-day / 5-day / 25-day regime meaning on H4 by using 6 / 30 / 150 H4 candles instead of H1's 24 / 120 / 600 candles.
- Fixed a hidden Field 3 fallback bug where an empty canonical mapping could suppress a valid stored symbol snapshot.

## Validation

- 480 project tests passed in split regression groups.
- 3 existing scikit-learn single-label warnings were emitted; no test failed.
- Focused tests cover the exact widget exception, Lunch navigation state safety, H4 startup, Guest secret auto-connect idempotence, five-plus-five pacing, and H4 6/30/150 regime windows.
- All changed Python files compile successfully.
- Tests used a lightweight Streamlit import stub because Streamlit is not installed in the repair container; the project requirements still contain the production Streamlit dependency.

## Timing note

The code enforces quota pacing and a 120–240 second safety window for live 10-symbol Super Quick runs. No application can guarantee that every external API request and every existing calculation finishes inside four minutes under provider outages, throttling, or slow network conditions. In that case the run fails safely or marks remaining work partial instead of silently violating quota controls.
