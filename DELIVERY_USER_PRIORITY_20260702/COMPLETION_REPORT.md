# User-Priority Completion Report

## Priority workflow

Expected flow:

1. Open Settings.
2. Select multiple symbols in order.
3. Connect APIs once.
4. Click Quick Run + Open Lunch.
5. Calculate every selected symbol in the intended scope.
6. Restore the first selected symbol as Main Core Symbol.
7. Open Lunch automatically with Field 1 expanded.
8. Open Field 10 and see today's ranked selected-symbol table first.

## Root causes repaired

1. **Stale Main Core override** — the batch runner previously obtained the main symbol from saved state after reading the selected list. A stale saved value could take authority over the first current selection.
2. **Blocked rows had no visible rank** — the locked `Daily Rank` is intentionally safety-gated, so blocked symbols could appear unranked or disappear from “best” selection.
3. **Missing selected rows** — the previous display overlay repaired only rows already present in the immutable publication; a selected symbol missing from that publication was not appended from its local child cache.
4. **Incomplete priority columns** — lower/higher bias, comparative rank, transition-probability aliases, safety-web status, evidence coverage, and explicit snapshot status were not consistently available in the first table.
5. **Blank/generic unavailable cells** — the prior full displayed frame could still contain blank, `N/A`, or `UNAVAILABLE` cells after partial recovery.
6. **Numeric display edge case** — explicit missing-evidence text could reach `float(...)` formatting in the top Field 10 metrics.
7. **Outdated scope labels** — secondary scope text still said Field 10 only even though Field 11 preparation is included after the multi-symbol transaction.

## Implemented behavior

- The first item in `multi_symbol_selected_20260701` is now authoritative for the run and is synchronized back into Main Core state.
- The immutable `Daily Rank` remains visible as **Eligible Rank**.
- A new **Rank** orders every selected symbol comparatively, including safety-blocked rows.
- Hard safety vetoes remain hard blocks; no global arbitrary threshold reduction was applied.
- Stable Daily Bias and Less-Risky Bias recover from the same symbol's higher-standard evidence when the stored result is WAIT/missing and no hard safety veto exists.
- Missing advanced metrics recover from that symbol's own saved local H1 cache.
- A selected symbol with no usable API or local history remains visible and ranked with a precise **Insufficient Local History** status; numeric values are never fabricated as zero.
- Every visible Field 10 cell is explicit in the display overlay.
- The locked production publication is never mutated by display recovery.
- Today's selected-symbol ranking is rendered before older Field 10 sections.

## Requirement matrix

| Requirement | Status | Evidence |
|---|---|---|
| Change only missing/broken priority behavior | PASS | Seven targeted source/test files changed; protected models untouched. |
| First selected symbol is Main Core | PASS | Routing test verifies stale saved GBPJPY cannot replace first selected EURUSD. |
| Quick/Full/Super Quick use selected multi-symbol list | PASS (core) | Orchestration tests verify main and secondary calls/scopes. |
| Secondary failure does not erase valid symbols | PASS (core) | Existing isolation tests passed. |
| Successful run restores Main Core context | PASS | Routing state assertions passed. |
| Successful run targets Lunch Field 1 open | PASS (code contract) | Navigation source test passed; browser click automation not available. |
| Field 10 shows today's table first | PASS | Updated renderer heading and execution order. |
| Every selected symbol appears | PASS | Eight-symbol validation: 8/8 present. |
| Every selected symbol has a rank | PASS | Comparative Rank 1–8; Eligible Rank preserved separately. |
| Higher-standard bias is prioritized and synchronized | PASS | Symbol-local shared bias recovery and tests. |
| Stable/less-risky bias does not remain unexplained WAIT | PASS | Recovered from higher-standard evidence unless hard safety block applies. |
| All required Field 10 columns are present | PASS | Automated required-column assertion. |
| No blank/N/A/UNAVAILABLE in visible priority table | PASS | Zero blank visible cells in validation report. |
| Use local saved data when live data is absent | PASS (code/core) | Per-symbol compressed child cache recovery path tested. |
| Do not fabricate numeric evidence | PASS | Missing numeric evidence uses explicit status text, never zero. |
| Preserve original locked publication | PASS | Deep-copy immutability assertion and report flag false. |
| Field 10 columns are independently calculated | PASS (synthetic evidence) | All 14 advanced metric columns varied across eight symbols. |
| API connects once / deduplicates requests | PASS (core) | API exact-candle deduplication test passed with test-only UI shim. |
| Live API/MT5 credentials and broker data | PARTIAL | Requires user's external services and terminal; not available in sandbox. |
| Full browser Streamlit E2E | PARTIAL | Source/state contracts and core tests pass; no browser runtime in sandbox. |
| Streamlit Cloud clean deployment | PARTIAL | Runtime/dependency guards pass; actual cloud deployment was not performed. |

## Files changed

See `CHANGED_FILES.md`.

## Tests executed

See `TEST_REPORT.md`.

## Remaining limitations

- A truthful numeric metric cannot be produced when both the live source and that symbol's local saved H1 history are absent. The row remains complete and explicit with `Insufficient Local History` rather than a fake value.
- Live connector authentication, broker symbol aliases, spread/tick behavior, and deployment UI responsiveness must be verified with the user's actual credentials and MT5 environment.

## Deployment

1. Upload the full repaired project.
2. Use `app.py` as the Streamlit entry point.
3. Keep `runtime.txt` as `python-3.12`.
4. Install `requirements.txt`.
5. Add API credentials only through Streamlit secrets/settings; do not hard-code keys.
6. Start the app, select symbols in the desired order, connect each provider once, and click the desired **Open Lunch** calculation button.
7. Confirm Lunch opens with Field 1 expanded, then open Field 10 and verify the **Today First — Ranked Multi-Symbol Decision Table**.
