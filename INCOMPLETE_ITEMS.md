# Incomplete Items and Honest Reasons

- No live Finnhub articles were embedded in the delivered database because the build environment did not have the user's API key or authenticated network session. The production path is implemented and tested with mocked authenticated Finnhub rows.
- Optional FinBERT inference is not forced in this focused patch. The table labels it `UNAVAILABLE_NOT_RUN` and uses a deterministic fallback.
- Matched historical event-study abnormal returns and fitted Hawkes intensity were not added in this focused correction. Their fields remain `UNAVAILABLE`; deterministic exponential decay is used and labelled.
- This correction does not implement the separate eight-session table requested in the broader uploaded specification. It addresses the user's current request: authenticated Finnhub sentiment ranking and verified database migration.
