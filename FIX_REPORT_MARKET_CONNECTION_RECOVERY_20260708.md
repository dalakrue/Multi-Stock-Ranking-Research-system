# Market Connection Recovery Repair — 2026-07-08

## Problem reproduced from the uploaded screenshot

The Settings market connector could show all of the following at the same time:

- Finnhub credential/news validation: connected and available.
- Main candle connector: ERROR.
- Market API: NONE.
- Loaded Rows: 0.
- Generic message: no trustworthy live or cached candle series.

The two statuses were measuring different capabilities. A key could validate against Finnhub's news/symbol route while the selected candle route failed. When Finnhub and Twelve Data both failed, the old provider chain had no cloud-safe keyless live candle source and stopped at zero rows.

## Implemented repair

1. **Added a real keyless live market-data fallback**
   - Provider order is now:
     `FINNHUB → TWELVE_DATA → YAHOO_FINANCE → MT5 → ALPHA_VANTAGE → LOCAL_VALID_CACHE`.
   - Yahoo Finance is used only after Finnhub and Twelve Data fail.
   - It does not generate synthetic prices.
   - It supports direct FX chart symbols such as `EURUSD=X`, crypto symbols, common index aliases, and explicit provider-symbol provenance.

2. **Repaired H4 collection**
   - Finnhub H4 continues to use genuine H1 candles aggregated into H4.
   - Twelve Data H4 now also uses one H1 request and aggregates genuine rows into H4, avoiding plan/endpoint-specific 4h failures.
   - Yahoo Finance H4 uses genuine H1 rows aggregated into H4.

3. **Removed the zero-row credential gate**
   - The Connect Once flow no longer stops before the orchestrator when both saved API keys are missing.
   - It continues to the keyless live fallback.

4. **Corrected misleading status presentation**
   - Finnhub credential/news status and Finnhub candle capability are now shown separately.
   - The panel shows the actual candle provider used and validated row count.
   - Failed/skipped provider attempts are available in a closed expander with actionable reasons.

5. **Improved failure diagnostics and security**
   - The generic final error now includes a short provider-route summary.
   - API tokens and secret values are redacted from attempt messages and UI diagnostics.

6. **Preserved canonical and exact-timeframe publication flow**
   - Frames still pass through the existing normalization, completed-candle validation, repository upsert, exact symbol/timeframe identity, and cumulative multi-symbol load contracts.
   - The keyless provider was added to the trusted validated-provider allowlist.

## Validation completed

- Full Python compile pass for `core`, `ui`, `tabs`, `tests`, `app.py`, and `adx_dashpoard.py`.
- Focused regression suite: **12 passed**.
- New tests cover:
  - Provider ordering.
  - FX/index Yahoo symbol routing.
  - Recovery after Finnhub and Twelve Data fail.
  - Genuine H1-to-H4 aggregation.
  - Secret redaction and provider-route diagnostics.
  - Existing Finnhub H4 behavior.
  - Finnhub-primary and Twelve-fallback behavior.

## Deployment note

Keep the existing Streamlit Secrets. The repaired connector will still prefer Finnhub, then Twelve Data. The new keyless source activates only when those routes cannot deliver a validated candle series.
