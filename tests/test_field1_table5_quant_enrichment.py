from __future__ import annotations

import pandas as pd

from core.field10_integrated_evidence_20260702 import enrich_table5_quant_validation


def test_field1_table5_quant_enrichment_copy_and_unresolved_outcome():
    source = pd.DataFrame({
        "Broker Candle Time": pd.to_datetime(["2026-07-01T10:00:00Z", "2026-07-01T09:00:00Z"]),
        "Technical Bias for Next H1": ["BUY", None],
        "Sentiment Bias for Next H1": ["SELL", None],
        "Session Bias for Next H1": ["BUY", None],
        "Regime Bias for Next H1": ["BUY", None],
        "Data Mining Bias for Next H1": ["BUY", None],
        "Combined Next-Hour Direction": ["BUY", None],
        "Available Sources": [5, 0],
        "Directional Agreement": [4, None],
        "Master Action": ["BUY", "WAIT"],
        "Outcome Status": ["PENDING", "SETTLED"],
        "Decision Correct": [True, False],
        "Actual Direction": ["BUY", "SELL"],
    })
    before = source.copy(deep=True)
    canonical = {
        "symbol": "GBPJPY", "run_id": "RUN-1", "source_id": "SRC-1",
        "snapshot_hash": "HASH-1", "completed_broker_candle": "2026-07-01T10:00:00Z",
    }
    result = enrich_table5_quant_validation(
        source, state={"multi_symbol_parent_run_id_20260701": "PARENT-1"},
        canonical=canonical, field10_validation=pd.DataFrame(),
    )
    pd.testing.assert_frame_equal(source, before)
    assert result is not source
    assert result.loc[0, "Technical Bias"] == "BUY"
    assert pd.isna(result.loc[1, "Technical Bias"])
    assert result.loc[1, "Technical Bias"] != "WAIT"
    assert bool(result.loc[0, "Outcome Settled"]) is False
    assert pd.isna(result.loc[0, "Master Action Correct"])
    assert pd.isna(result.loc[0, "Actual Next-H1 Direction"])
    assert bool(result.loc[1, "Outcome Settled"]) is True
    assert result.loc[1, "Master Action Correct"] is False or result.loc[1, "Master Action Correct"] == False
    assert result.loc[1, "Actual Next-H1 Direction"] == "SELL"


def test_table5_keeps_latest_25_broker_days_only():
    times = pd.date_range("2026-05-01", periods=30, freq="D", tz="UTC")
    source = pd.DataFrame({
        "Broker Candle Time": times,
        "Master Action": ["WAIT"] * len(times),
        "Outcome Status": ["PENDING"] * len(times),
    })
    result = enrich_table5_quant_validation(
        source, state={}, canonical={"symbol": "USDJPY"}, field10_validation=pd.DataFrame(),
    )
    assert pd.to_datetime(result["Broker Candle Time"], utc=True).dt.date.nunique() == 25
    assert pd.to_datetime(result["Broker Candle Time"], utc=True).is_monotonic_decreasing
