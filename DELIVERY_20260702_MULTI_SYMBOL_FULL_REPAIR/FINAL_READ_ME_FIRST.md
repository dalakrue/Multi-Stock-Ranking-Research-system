# Read Me First — Multi-Symbol Full Repair

## Start the application

The verified Streamlit entry point is:

```powershell
streamlit run app.py
```

Use Python 3.12, which is declared in both `runtime.txt` and `.python-version`.

## Main repaired behavior

- Settings now has one ordered Multi-Symbol Selector.
- The first selected symbol is the Main Core Symbol.
- Later selections are comparison symbols.
- Any successful run opens Lunch at Field 1 and keeps the other large fields closed.
- Lunch Fields 1–3, 10 and 11 restore the selected saved symbol snapshot before rendering.
- Field 10 uses independent, symbol-specific H1 evidence and audits repeated/static values.
- Field 3 Higher Standard Bias is the first directional authority for Field 10.
- Field 2 can recover a non-empty, clearly labelled active-symbol OHLC projection when the protected calibrated bundle is unavailable.
- Field 11 can rebuild a bounded analogue index from saved non-EURUSD symbol caches.
- Live session display is refreshed from the current clock rather than frozen to an old calculation candle.

## Data requirements

The repaired fallbacks do not invent prices or cross-borrow another symbol:

- Field 2 display fallback requires at least 24 valid completed candles for the selected symbol.
- Field 10 adaptive H1 evidence requires at least 80 valid completed candles for the row's symbol.
- If the provider returns no usable OHLC, the system reports the data problem instead of fabricating output.

## Verification

- Source compilation: passed.
- Project tests: 302 passed, 0 failed.
- New repair acceptance tests: 7 passed.

See `TEST_REPORT.md` and `IMPLEMENTATION_REPORT.md` for details.
