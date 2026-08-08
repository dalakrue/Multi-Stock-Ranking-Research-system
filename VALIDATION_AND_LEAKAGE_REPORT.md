# Validation and Leakage Report

## Passed controls

- Finnhub rows are persisted only after `connection_status().connected` is true.
- Provider is stored as `FINNHUB`; credentials are not accepted by the new module.
- No API-key, password, secret, credential, or access-token columns exist in the new tables.
- Future-dated articles beyond a five-minute tolerance are rejected.
- Event age is nonnegative.
- Impact remaining and absorption are bounded to 0–100.
- Fallback impact remaining is monotonic when no new event arrives.
- Positive base/quote currency mapping is tested in both directions.
- Missing actual/consensus/surprise fields remain unavailable.
- Lunch rendering calls only the read-only loader/schema verifier.
- The authoritative daily rank table is not modified by news evidence.

## Limitations

- Live Finnhub network access was not available in the build environment.
- FinBERT is not forced; the deterministic fallback is labelled honestly.
- Hawkes fitting and matched event-study estimates are not implemented in this focused patch; fields remain unavailable rather than fabricated.
- Provider timestamps are converted using the persisted snapshot timezone when available. When the snapshot is UTC, broker-time display remains UTC.
