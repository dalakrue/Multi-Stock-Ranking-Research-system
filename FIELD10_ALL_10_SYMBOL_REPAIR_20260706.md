# Field 10 — All 10 Selected Symbols Repair

## Implemented repair

This package fixes the failure mode where the Instant Run Engine reached 100% but Field 10 showed a usable row for only one symbol and `INSUFFICIENT LOCAL HISTORY` for the others.

### Root causes repaired

1. **H4 child data was validated as H1.**
   Multi-symbol child calculations now use the exact activated child symbol and selected timeframe. The protected standalone EURUSD/H1 path is unchanged.

2. **A short current cache could suppress the full history request.**
   Cache reuse now requires both freshness and enough candles for the selected-timeframe Higher Standard contract.

3. **Fresh API pages were not combined with older validated local history before publication.**
   After each successful provider response, the exact-symbol repository is reloaded and the complete validated history is passed to Fields 1–3, Power BI, and Field 10.

4. **Quota pacing depended too heavily on a transient UI flag.**
   For an explicit run whose selected universe exceeds the live-request window, compliant quota-safe pacing is now automatically enabled even if a Streamlit rerun loses the UI flag. Existing explicit settings still take precedence.

5. **The requested history size could be below the selected-timeframe contract.**
   The Settings-owned run now always requests at least the real-candle Higher Standard requirement plus a small indicator/de-duplication buffer.

## Data-integrity rule

No candle, price, expected return, reliability value, or ranking input is fabricated. Every symbol uses only its own live or validated cached history. When a provider is temporarily rate-limited, the one-click run waits and retries unresolved symbols instead of completing the job after only the first provider window.

## Verification

- 35 targeted H4, multi-symbol, publication, quota, repository-merge, and Field 10 tests passed.
- 38 additional instant-run, routing, regression, and user-repair tests passed.
- All `core`, `ui`, `tabs`, `app.py`, and `adx_dashpoard.py` Python files compiled successfully.
- Main Streamlit entry point remains `app.py`.
- No real API key or `secrets.toml` is included.
