# Performance Benchmark

Environment: Python 3.13.5, synthetic/local data, no live MT5/API.

## Measured

- Causal Field 10 metrics on 1,600 H1 rows: median **14.80 ms**, mean **17.42 ms** across 20 runs.
- Top-15 qualification over synthetic spread observations: median **18.41 ms**, mean **18.57 ms** across 20 runs.
- First provider-adapter fetch: **5.534 ms**.
- Exact-candle in-session cache hit: **0.538 ms**.
- Local measured cache speedup: **10.29x**; one provider request avoided in the two-call scenario.
- Persistent SQLite cache read median: **4.17 ms**.
- Persistent SQLite cache write median: **3.94 ms**.
- First temp-database migration: **30.08 ms**; idempotent second run: **15.27 ms**.

## Interpretation

The cache benchmark demonstrates that repeated exact-candle work can be avoided. It does **not** prove a 30–50% end-to-end improvement under live network, Streamlit, MT5, or mobile conditions. The project therefore reports measured component timings only.
