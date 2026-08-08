# API Credit Reduction Report

## Implemented

- MT5 remains the intended bulk source for broker H1 OHLC, bid/ask, broker spread, tick volume, symbol availability, and completed-candle identity.
- Twelve Data receives a token bucket with three-credit capacity, two usable credits per minute, and one reserved safety credit.
- HTTP/provider failures containing `429`, quota, or credit-exceeded signals are classified as `QUOTA_EXHAUSTED` and are not immediately retried.
- Exact completed-candle requests are deduplicated in session.
- Traceable multi-symbol parent runs may reuse a persistent SQLite exact-candle cache keyed by provider, canonical/provider symbol, timeframe, completed candle, requested bars, and profile fingerprint.
- Standalone callers preserve the prior first-fetch/session-dedup behavior and cannot accidentally inherit unrelated database history.
- API request audit records provider/category/symbol hash/credits/cache/dedup/status/candle/time/duration/retry without storing credentials.
- Finnhub news can be fetched once, normalized, URL/headline-deduplicated, TTL-cached, then mapped locally to multiple symbols.
- Field 10 displays a compact API budget summary.

## Verified

- Token bucket test: first two credits allowed; third request enters cooldown.
- Exact-candle test: first fetch calls provider once; second request is an in-session cache hit; force refresh calls provider again.
- Persistent cache round-trip test passes.
- Shared-news test stores two unique records from three inputs and removes one duplicate.
- Secret scan found no secret-shaped values or persisted secret columns.

## Limitation

The existing connector returns `(frame, ok, source, message)` and does not expose raw HTTP headers. Therefore `api-credits-used` and `api-credits-left` are represented in the audit schema but live header ingestion is not claimed as completed.
