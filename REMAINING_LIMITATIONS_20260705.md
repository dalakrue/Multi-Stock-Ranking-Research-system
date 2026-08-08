# Remaining Limitations — 2026-07-05

1. **Live-provider end-to-end verification:** Twelve Data and Finnhub were not called with the user's private keys in this isolated environment. The package includes the repaired one-click/session-reuse, retry, priority and fallback logic, but the first real deployment run must confirm the account-specific quota and symbol entitlements.
2. **Current packaged history depth:** The supplied database contains limited completed Field 10/11 history for several symbols. Until a valid provider run fills those histories, the UI intentionally shows explicit fallback/provenance labels rather than invented numbers.
3. **Physical-device verification:** Mobile tables were rebuilt as responsive cards/compact tables, but no real iPhone browser automation was available here.
4. **Research promotion gates:** The project already contains Hamilton/regime, covariance, calibration, conformal, drift and forecast-comparison research layers. GAIN-style learned imputation is not promoted to raw market-price repair, and no research candidate is promoted without chronological out-of-sample evidence. This is intentional safety behavior, not a silent omission.
5. **Market outcome claims:** Passing software tests does not establish trading profitability or forecast accuracy. Those require settled future outcomes and production walk-forward monitoring.
