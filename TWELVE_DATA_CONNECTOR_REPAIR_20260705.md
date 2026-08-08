# Twelve Data Connector Repair — 2026-07-05

Implemented code repairs:

- Fixed the market connection state transition: the UI imported a nonexistent `connect` function instead of the real `succeed` transition.
- Unified pasted keys, Streamlit Secrets, environment variables, and encrypted saved credentials into one resolver.
- Added support for canonical `[api_keys] second_api` plus common Twelve Data secret aliases.
- A pasted replacement now overrides an older secret immediately; a vault-restored old key no longer shadows a newer Streamlit Secret.
- The Twelve Data connect button now works with a blank paste field when a Streamlit Secret is configured.
- Added separate `Twelve Key`, `Twelve Connection`, `Candle Rows`, credential source, and actionable failure status metrics.
- Fixed encrypted credential persistence SQL (`secret_fingerprint`).
- Persisted configured/connected state correctly even when the key comes from Streamlit Secrets rather than the local vault.
- Improved Twelve Data HTTP/API error handling for rejected keys, rate limits, server failures, empty data, invalid JSON, and timeouts.
- Restores validated local candles and connector status after Streamlit reruns without making a duplicate API request.
- Failed refreshes now clear misleading live-connected state while preserving the last immutable calculation output.

Validation:

- Python compile-all passed for app, core, UI, tabs, services, and tests.
- 29 targeted deployment/connector tests passed.
