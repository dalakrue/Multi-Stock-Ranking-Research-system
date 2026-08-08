# ADX Quant Pro — Multi-Symbol Full Repair Report

Build date: 2026-07-02  
Repair base: `ADX_QUANT_PRO_SYMBOL_SYNC_FIELD11_POWERBI_FIXED_20260702`

## Delivered outcome

The Settings instrument controls now use one ordered multi-symbol selector. The first selected instrument is the Main Core Symbol. Every later selection is a comparison/secondary symbol. The old separate instrument-library dropdown, separate typed-symbol box, and independent main-symbol widget are no longer allowed to become competing symbol authorities.

The repair preserves the protected production pipeline and adds bounded recovery around it. It does not silently present fallback evidence as a calibrated production forecast.

## Requirement traceability

| Requirement | Implementation | Result |
|---|---|---|
| Replace Global Instrument Selection | `ui/multi_symbol_settings_20260701.py` provides one ordered multiselect; `ui/global_symbol_selector_20260629.py` is now a compatibility facade | Completed |
| First symbol is Main Core | `_publish_selection()` writes the first ordered selection to `MAIN_SYMBOL_KEY` and connector/main state | Completed |
| Remove symbol locking | No independent main-symbol dropdown can overwrite the first ordered selection; legacy `selected_symbol`/`ws_symbol` writes were removed | Completed |
| Hide duplicate symbol inputs/buttons | Sidebar connector defaults to `show_symbol_selector=False`; Settings renders each connector section once | Completed |
| All selected symbols get saved child states | Multi-symbol orchestrator preserves ordered selection and treats complete or usable partial child caches as available | Completed |
| Lunch symbol switching | Lunch lists only physically readable saved symbol caches and restores the selected child before rendering Fields 1–3, 10 and 11 | Completed |
| Field 3 ↔ Field 10 bias sync | Field 10 recursively reads the same child state's Field 3 Higher Standard Bias before any adaptive fallback | Completed |
| No WAIT everywhere | WAIT/blocked publication evidence no longer erases valid OHLC-derived direction; safety remains a separate permission/veto layer | Completed |
| Field 10 advanced columns | New causal H1 layer computes probability, entropy, posterior margin, age, duration, remaining duration, transitions, calibration, Brier and 1H/3H/6H validation | Completed |
| No repeated constants | Every adaptive value is calculated independently from each symbol's own completed H1 data; variability is audited | Completed |
| Lower over-blocking | Valid identity + at least 80 completed H1 candles can publish evidence; unavailable optional research layers lower confidence instead of forcing every row to BLOCKED | Completed |
| Preserve safety | Actual checksum, identity mismatch, severe instability, unusable spread and safety veto remain hard protections | Completed |
| Quick/Calculate/Open Lunch navigation | Successful Settings run routes to Lunch Field 1; other large fields remain closed | Completed |
| Current session not frozen | Auto session uses current UTC minute and publishes current broker-session display separately from the completed candle | Completed |
| BFD/SFD flexibility | Thresholds were relaxed so directional history can produce Allowed, Hold and Protect, or Wait Pullback instead of permanent No Trade | Completed |
| Field 11 all-symbol support | Missing indices are rebuilt from readable selected-symbol caches without MT5/API calls or Field 10 reranking | Completed |
| Field 2 Power BI non-empty recovery | Missing calibrated bundle falls back to a six-hour causal active-symbol OHLC path with bands, future candles and historical references | Completed |
| Continuous validation | Validation runs after Settings completion and before Lunch rendering; it checks symbol order, cache readiness, navigation, session and Power BI availability | Completed |
| Immutable publication protection | Field 10 display repair creates auditable `Stored ...` columns and never mutates the immutable daily SQLite publication | Completed |

## Field 10 evidence behavior

The new adaptive H1 layer derives the following from each symbol independently:

- Stable Daily Bias and Less-Risky Bias, with Field 3 Higher Standard Bias as the first authority.
- Regime Probability and normalized Regime Entropy.
- Posterior Margin between the top two regime states.
- Regime Persistence, current Regime Age, Expected Regime Duration and Estimated Remaining Duration.
- Transition Risk for 1H, 3H and 6H.
- Calibrated Bias Probability based on causal historical directional performance and current signal strength.
- Brier Score and walk-forward Forecast Accuracy for 1H, 3H and 6H.

Missing API/research bundles therefore no longer create blank columns when a valid completed H1 history exists. API-derived or protected research values still take precedence when they are finite and valid.

## Power BI fallback contract

When the calibrated exact-run path exists, Field 2 uses it unchanged. When it does not exist, Field 2 builds a clearly labelled display/research fallback from the active symbol's own completed OHLC:

- Six future H1 central points.
- Realized-volatility square-root-of-time upper/lower bands.
- Future candle bodies derived from the same central path.
- Historical causal reference paths.
- No future actual values and no cross-symbol borrowing.

A valid fallback requires at least 24 usable completed candles. If the connector returns no usable OHLC, the application reports that data failure rather than fabricating prices.

## Continuous validation contract

"Continuous" means every Settings completion and every Lunch render in Streamlit. It is not a background thread. The validator:

1. Reasserts first selected = Main Core Symbol.
2. Selects a readable Lunch child cache if stale state points to an unavailable child.
3. Restores Field 1 as the post-run landing field.
4. Recovers the active symbol's Power BI bundle/fallback once per generation fingerprint.
5. Refreshes current session evidence.
6. Exposes a visible validation table in Lunch.
7. Applies an auditable Field 10 display overlay for old same-day publications without changing the immutable database.

## Important safety distinction

Lowering a display or publication threshold does not automatically mean a trade is safe. Direction, forecast evidence, entry permission, spread quality and safety veto remain separate. An adaptive directional result can be shown while `Entry Permission` remains `CAUTION` or a genuine safety veto remains blocked.
