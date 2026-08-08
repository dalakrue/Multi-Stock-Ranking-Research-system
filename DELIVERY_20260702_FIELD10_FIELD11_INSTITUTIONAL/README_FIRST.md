# ADX Quant Pro — Field 10 + Field 11 Delivery

## Delivered build

This project preserves the existing immutable Field 10 daily-ranking production path and adds Lunch **Field 11 — Similar Path Simulator** as an additive, canonical-identity-guarded historical-analogue system.

Deployment entry point remains **`app.py`**. The compatibility entry point **`adx_dashpoard.py`** is retained.

### Implemented and verified

- Field 10 immutable morning snapshot, broker-time lock, live safety veto separation, settlement storage, and protected calculations remain intact.
- Field 11 is present in the authoritative Lunch selector and is closed by default.
- Field 11 is prepared only during the existing multi-symbol `Run Calculation + Open Lunch` transaction.
- Field 11 opening and selector changes do not call market APIs or recalculate Fields 1–10.
- Strict canonical/Field 10 identity checks fail closed on mismatched run, hash, candle, index version, or snapshot integrity.
- Completed-candle-only historical feature/index artifacts, constrained-DTW final matching, robust feature scaling, hybrid similarity, empirical path extraction, scenario clustering, effective sample size, bootstrap stability, drift guard, persistence, and idempotent outcome settlement are implemented.
- Streamlit health endpoint returned `ok`.
- All **295 collected tests pass in four isolated deterministic segments**. A monolithic one-process run stalls in a legacy Field 3 fixture after 70% because of accumulated cross-test process state; it does not report an assertion failure. This is explicitly not represented as a successful monolithic run.

### Read before production use

The uploaded Field 10 specification asks for a validated LambdaMART/LightGBM + CatBoost expected-pips production stack. The repository does not contain enough mature, settled, leakage-safe cross-sectional history to train and validate that stack in this environment. The existing transparent immutable Field 10 scorer remains production-authoritative. No unvalidated ML model was silently activated.

Field 11 uses real completed historical OHLC analogues. Timestamped historical regime, sentiment, news, spread and cross-market archives are not consistently present in the uploaded project. Those components remain neutral/UNAVAILABLE, reduce reliability, and are never fabricated. See `INCOMPLETE_ITEMS.md` and the requirement matrices.
