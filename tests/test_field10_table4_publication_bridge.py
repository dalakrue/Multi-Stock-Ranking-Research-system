from __future__ import annotations

import sqlite3
import sys
import types
import pandas as pd

sys.modules.setdefault("streamlit", types.ModuleType("streamlit"))

from core.field10_integrated_evidence_20260702 import (
    TABLE_NAME, publish_field1_table4_to_field10,
)


def test_field10_table4_publication_bridge_reuses_existing_publisher(monkeypatch, tmp_path):
    calls = {"count": 0}
    table4 = pd.DataFrame({
        "Broker Candle Time": pd.to_datetime(["2026-07-01T10:00:00Z"]),
        "Technical Bias for Next H1": ["BUY"],
        "Sentiment Bias for Next H1": ["SELL"],
        "Session Bias for Next H1": ["BUY"],
        "Regime Bias for Next H1": ["BUY"],
        "Data Mining Bias for Next H1": [None],
        "Combined Next-Hour Direction": ["BUY"],
    })

    def publisher(state, canonical):
        calls["count"] += 1
        return table4.copy(deep=True), "TEST_EXISTING_PUBLISHER"

    monkeypatch.setattr("ui.lunch_next_hour_bias_history_20260626.build_field1_table4_publication", publisher)
    monkeypatch.setattr("core.field10_integrated_evidence_20260702._field3_values", lambda *a: {})
    monkeypatch.setattr("core.field10_integrated_evidence_20260702._quality_values", lambda *a: {"grade": "A", "score": 95.0})
    monkeypatch.setattr("core.field10_integrated_evidence_20260702._execution_values", lambda *a: {"current_session": "LONDON", "spread_quality": "GOOD", "trade_permission": "ALLOW", "final_action": "BUY"})
    monkeypatch.setattr("core.field10_integrated_evidence_20260702._incremental_changepoint", lambda *a: {"status": "STABLE"})
    monkeypatch.setattr("core.field10_integrated_evidence_20260702._adwin_bundle", lambda *a: {"drift_status": "STABLE", "effective_window": 64})
    canonical = {
        "symbol": "GBPJPY", "timeframe": "H1", "run_id": "RUN-GJ-1", "source_id": "SRC-GJ",
        "snapshot_hash": "HASH-GJ", "completed_broker_candle": "2026-07-01T10:00:00Z",
        "final_decision": {"final_decision": "BUY", "trade_permission": "ALLOW"},
    }
    state = {"symbol": "GBPJPY", "multi_symbol_main_symbol_20260701": "GBPJPY"}
    db = tmp_path / "test.sqlite3"
    report = publish_field1_table4_to_field10(
        state=state, canonical=canonical, parent_run_id="PARENT-1", child_run_id="PARENT-1:GBPJPY",
        symbol="GBPJPY", path=db,
    )
    assert calls["count"] == 1
    assert report["ok"] is True
    assert report["inserted"] is True
    assert report["table4_source_status"] == "TEST_EXISTING_PUBLISHER"
    with sqlite3.connect(db) as conn:
        row = conn.execute(f"SELECT technical_bias,sentiment_bias,data_mining_bias,combined_evidence_bias FROM {TABLE_NAME}").fetchone()
    assert row == ("BUY", "SELL", None, "BUY")


def test_publication_bridge_rejects_duplicate_identity(monkeypatch, tmp_path):
    table4 = pd.DataFrame({
        "Broker Candle Time": pd.to_datetime(["2026-07-01T10:00:00Z"]),
        "Technical Bias for Next H1": ["BUY"],
        "Combined Next-Hour Direction": ["BUY"],
    })
    monkeypatch.setattr("ui.lunch_next_hour_bias_history_20260626.build_field1_table4_publication", lambda **_: (table4.copy(), "TEST"))
    monkeypatch.setattr("core.field10_integrated_evidence_20260702._field3_values", lambda *a: {})
    monkeypatch.setattr("core.field10_integrated_evidence_20260702._quality_values", lambda *a: {"grade": "B", "score": 80.0})
    monkeypatch.setattr("core.field10_integrated_evidence_20260702._execution_values", lambda *a: {})
    monkeypatch.setattr("core.field10_integrated_evidence_20260702._incremental_changepoint", lambda *a: {})
    monkeypatch.setattr("core.field10_integrated_evidence_20260702._adwin_bundle", lambda *a: {})
    canonical = {"symbol": "USDJPY", "timeframe": "H1", "run_id": "R", "source_id": "S", "snapshot_hash": "H", "completed_broker_candle": "2026-07-01T10:00:00Z"}
    state = {"symbol": "USDJPY", "multi_symbol_main_symbol_20260701": "USDJPY"}
    kwargs = dict(state=state, canonical=canonical, parent_run_id="P", child_run_id="P:USDJPY", symbol="USDJPY", path=tmp_path / "d.sqlite")
    first = publish_field1_table4_to_field10(**kwargs)
    second = publish_field1_table4_to_field10(**kwargs)
    assert first["inserted"] is True
    assert second["status"] == "DUPLICATE_REJECTED"
    assert second["inserted"] is False
