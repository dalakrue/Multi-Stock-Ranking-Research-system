# Known Limitations

1. **INSUFFICIENT_HISTORY:** only two parent broker days and zero institutional settled outcomes.
2. **No accuracy/profitability claim:** calibration, coverage, SPA, PBO, DSR and net performance are unproven.
3. **One legacy source-identity defect:** a historical USDJPY parent row has missing source ID/hash and remains blocked.
4. **Spread/slippage availability:** net EV and net realized return remain NULL when exact cost evidence is absent.
5. **Event intensity:** no Hawkes parameters are estimated; explicit insufficient-history rows are used.
6. **FinBERT/event memory:** existing sentiment/news functionality is preserved, but full institutional normalized event extraction and event-study validation are not complete.
7. **Conditional conformal coverage:** not claimed; implemented evidence is marginal OOS coverage.
8. **Session/regime subgroup calibration:** requires larger subgroup samples.
9. **Live-provider performance:** no safe comparable before/after MT5/API heavy-run benchmark was available.
10. **One legacy test conflict:** auto-heavy startup is intentionally disabled to preserve Settings-only ownership.
11. **Environment runtime:** tests executed in Python 3.13 with explicit Python 3.12 syntax compatibility checks; deployment files target Python 3.12.
12. **Shadow promotion:** all new candidates remain shadow-only until preregistered OOS gates pass.

13. **Finnhub live entitlement not tested here:** deterministic adapters and the production endpoint path were tested, but the user's plan may restrict specific forex candle symbols/resolutions.
14. **597/600 remains partial:** it is calculation-eligible adaptive history with 99.5% coverage, not a claim of full 600-candle evidence.
15. **Provider availability varies:** when Finnhub is selected but unavailable, the system may transparently use an explicitly configured fallback and records that provenance.
