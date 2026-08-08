# Known Limitations and Unverified Items

1. The execution environment had Python 3.13.5 and did not have the `streamlit` package installed. `python -m compileall -q .` passed, deployment guard tests passed, and the full 218-test repository suite passed with a temporary test-only Streamlit import shim. A real `streamlit run` process was not launched here. The project still declares `streamlit>=1.35,<2` and `runtime.txt`/`.python-version` target Python 3.12.
2. No live API credentials or network provider calls were used. Provider aliases and live HTTP/MT5 status behavior are covered by adapters/unit tests but are not claimed as live-verified.
3. PBO and Deflated Sharpe are not newly implemented as computed metrics in this scope. No values are fabricated; the report clearly leaves them incomplete.
4. Conformal, Brier, conditional accuracy, SPA and portfolio-risk fields remain `UNAVAILABLE` until sufficient identity-matched settled history exists.
5. The complete filtered CSV export is bounded by the retained 600 rows per symbol; it is not an unlimited database dump.
6. Device heat cannot be measured by Streamlit Cloud. The existing CPU-time proxy remains the only heat-related audit.
