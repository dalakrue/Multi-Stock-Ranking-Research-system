# ADX Quant Pro — Symbol Sync, Field 11, and Power BI Repair

## Fixed

- Removed the stale-symbol ownership conflict that could force the Settings connector back to `USDCHF`.
- Unified the Settings main symbol across the global selector, multi-symbol selector, connector profile, and run orchestrator.
- Protected the Settings main symbol while Lunch restores a secondary child snapshot.
- Added an explicit **Connect / Load [symbol]** control at the top of Lunch for Fields 1–3, Power BI Field 2, Field 10, and Field 11.
- Kept Field 10 and Field 11 symbol widgets synchronized with the loaded Lunch child snapshot.
- Repaired Field 10 checksum-representation drift without changing ranks, scores, decisions, timestamps, or other calculation values.
- Changed Field 11 to use the immutable Field 10 parent publication as its index identity instead of rejecting valid secondary-child candle differences.
- Field 11 now indexes all selected symbols that have sufficient completed historical data and exposes only successfully indexed symbols in its selector.
- Recovered Power BI from the selected child snapshot's saved path, synchronized identity aliases, and removed market candles newer than that child snapshot before integrity validation.
- Added three visible run buttons. Every mode passes through the same multi-symbol transaction and prepares the symbol-aware Lunch outputs, Field 10 publication, and Field 11 index.

## Use

1. In **Settings**, choose the main symbol and all additional symbols.
2. Press the Settings market **Connect** button. The selected main symbol remains authoritative and is not replaced by a prior `USDCHF` value.
3. Press one of the three calculation buttons:
   - **Run Calculation + Open Lunch**
   - **Full + Open Lunch**
   - **Super Quick + Open Lunch**
4. At the top of **Lunch**, choose a completed symbol and press **Connect / Load [symbol]**. Fields 1–3, Power BI Field 2, Field 10, and Field 11 then read the same saved child generation.

## Verification

- All **295 collected automated tests passed** when executed file-by-file.
- Field 10 persisted snapshot in the delivered project validates as `VALID` with 3 locked rows.
- All 978 Python source files parsed successfully with `ast.parse`.
- `compileall` completed successfully for `core`, `ui`, `tabs`, `services`, `research_quant`, and `tests`.
- Additional targeted checks passed for stale-USDCHF removal, Field 10 checksum repair, Field 11 child-candle mismatch handling, and Power BI child-snapshot alignment.

## Runtime note

Live MT5, Twelve Data, Finnhub, and broker-specific symbol availability require the user's own credentials and provider connection. The system does not fabricate results when a provider supplies no valid historical data; Field 11 lists only symbols with a successfully prepared historical index.
