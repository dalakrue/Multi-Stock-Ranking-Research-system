# Top-15 Spread Qualification Report

## Contract

- Automatically excluded: `EURUSD`, `USDJPY`, `GBPUSD`.
- No pair is assumed to have a spread below 20 broker points.
- Broker suffixes/prefixes are normalized by locating a supported canonical six-letter FX pair inside the provider symbol.
- Qualification requires a tradeable symbol, enough spread observations, rolling median spread `<= 20` broker points, and a fresh observation.
- Stored evidence includes current spread, rolling median, p95, count, freshness, H1 bars, tick-volume evidence, quality score, reason, account fingerprint, evaluated time, and expiry.
- Ranking combines a liquidity prior, spread quality, spread stability, and data completeness.
- If fewer than 15 qualify, the startup state becomes Plan B; no unqualified pair is inserted.

## Validation

A synthetic broker-observation test created more than 15 candidates, included excluded majors, and injected an 80-point outlier. The selected 15 contained none of the excluded pairs and every selected rolling median was `<=20`.

## Live limitation

MetaTrader5 is unavailable in the current Linux execution environment. Live account fingerprint, symbol visibility, trade mode, current bid/ask, and real STP spread qualification were not testable.
