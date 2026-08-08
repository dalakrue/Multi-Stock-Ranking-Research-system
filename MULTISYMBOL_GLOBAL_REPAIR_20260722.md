# Multi-Symbol Global Repair — 2026-07-22

## Implemented behavior

- One loaded-symbol display authority now controls Settings, Lunch, Research, AI Assistant, Field 3, Field 12, and Field 13.
- Symbol selectors list completed/loaded symbols only. Configured defaults are not injected into the selector.
- Loading a display symbol synchronizes all tab mirrors and legacy display keys without fetching market data or recalculating.
- Settings includes a global loaded-symbol selector. Its **Load selected symbol across all tabs** action changes the active symbol everywhere.
- Field 3 and Field 13 filter their published multi-symbol regime evidence to the selected symbol.
- Field 12 is now a fundamental-only multi-symbol news/NLP ranking. It uses symbol relevance, news freshness, absorption, sentiment strength, and conflict protection. It does not use Field 10 technical scores.
- Field 12 is read-only when opened. It is published during the Settings calculation and does not trigger an API call from the tab.
- AI Assistant routes “best symbol to enter now” and selected-symbol entry questions to Field 10 multi-symbol evidence, with Field 12 news context. It no longer uses Field 1 as the authority for these questions.
- AI Assistant can validate a saved Field 10 institutional publication even when the legacy single-symbol Field 1 bundle is absent.
- Terminal calculation states release all known run locks so Super Quick, Quick, and Full runs do not leave one another disabled.
- Saved timeframe and active display symbol take precedence during a fresh process start. The same completed-candle publication is restored rather than silently replacing H1 with the seeded H4 default.
- Runtime cache coverage now includes the global display symbol, selected timeframe, Field 12, and Field 13 publications.

## Important operating rule

Changing the display symbol switches among the evidence already produced by the latest completed calculation. It does not silently fetch or recalculate. To add a new symbol to the selector, load and complete it through Settings first.

## Verification

- Focused repair suite: **29 passed**.
- Python syntax/compile checks passed for the changed modules.
- ZIP integrity is verified during packaging.

## Validation boundary

Live provider calls, Streamlit browser rendering, and credential-dependent execution could not be exercised in this isolated environment. The full legacy test collection also contains unrelated pre-existing failures and requires Streamlit, which is not installed here. The focused tests cover the repaired state propagation, persistence, Field 12, AI routing, and run-lock behavior.
