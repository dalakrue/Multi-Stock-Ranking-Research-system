from __future__ import annotations

from pathlib import Path

import pandas as pd


def _source() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Symbol": "EURUSD", "Load Status": "READY", "Sample Count": 250,
            "Data Quality Grade": "A", "Higher-Standard Regime Bias": "BUY",
            "Regime Probability": 82, "Expected Return 6H": 1.2,
            "Transition Risk 6H": 18, "Entry Permission": "ALLOW",
        },
        {
            "Symbol": "GBPUSD", "Load Status": "READY", "Sample Count": 260,
            "Data Quality Grade": "B", "Higher-Standard Regime Bias": "SELL",
            "Regime Probability": 70, "Expected Return 6H": -0.8,
            "Transition Risk 6H": 25, "Entry Permission": "ALLOW",
        },
    ])


def test_durable_h4_authority_is_reused_for_same_completed_candle(tmp_path, monkeypatch):
    monkeypatch.setenv("ADX_FIELD10_AUTHORITY_DB_PATH", str(tmp_path / "field10.sqlite3"))
    from core.field10_unified_authority_20260709 import build_unified_field10_authority

    state = {
        "canonical_ranking_timeframe": "H4",
        "adx_current_selected_symbols_20260708": ["EURUSD", "GBPUSD"],
        "completed_broker_candle": "2026-07-17T08:00:00Z",
    }
    first = build_unified_field10_authority(state, source_frame=_source(), persist=True)

    reopened = {
        "canonical_ranking_timeframe": "4H",
        "adx_current_selected_symbols_20260708": ["EURUSD", "GBPUSD"],
        # This is a later H1 watermark inside the same H4 bucket.
        "completed_broker_candle": "2026-07-17T09:00:00+00:00",
    }
    changed = _source()
    changed.loc[0, "Expected Return 6H"] = -99
    second = build_unified_field10_authority(reopened, source_frame=changed, persist=True)

    assert second["reused_from"] == "DURABLE_FIELD10_AUTHORITY_SQLITE"
    pd.testing.assert_frame_equal(first["table"], second["table"])
    assert first["snapshot"]["snapshot_hash"] == second["snapshot"]["snapshot_hash"]


def test_new_lunch_surfaces_are_wired_without_replacing_legacy_labels():
    source = Path("ui/lunch_four_core_fields_20260619.py").read_text(encoding="utf-8")
    assert "FIELD12_FIELD" in source and "FIELD13_FIELD" in source
    assert "FIELD_SELECTOR_LABELS" in source
    assert "elif selected_field == FIELD12_FIELD" in source
    assert "elif selected_field == FIELD13_FIELD" in source
