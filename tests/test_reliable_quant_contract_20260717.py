from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def test_timeframe_aliases_and_timestamp_forms_share_identity():
    from core.reliable_quant_contract_20260717 import canonical_completed_candle, normalize_timeframe

    assert normalize_timeframe("H4") == normalize_timeframe("4H") == "H4"
    values = {
        canonical_completed_candle("2026-07-17T09:00:00Z", "H4"),
        canonical_completed_candle("2026-07-17T09:00:00+00:00", "4H"),
        canonical_completed_candle("2026-07-17T09:00:00", "H4"),
    }
    assert values == {"2026-07-17T08:00:00+00:00"}


def test_candle_contract_rejects_incomplete_future_duplicate_and_bad_ohlc():
    from core.reliable_quant_contract_20260717 import validate_candle_rows

    rows = [
        {"symbol": "EURUSD", "bar_close_utc": "2026-07-17T08:00:00Z", "is_complete": True, "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15},
        {"symbol": "EURUSD", "bar_close_utc": "2026-07-17T08:00:00+00:00", "is_complete": True, "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15},
        {"symbol": "EURUSD", "bar_close_utc": "2026-07-17T09:00:00Z", "is_complete": False, "open": 1.1, "high": 1.0, "low": 1.2, "close": 1.15},
    ]
    report = validate_candle_rows(rows, symbol="EURUSD", timeframe="H4", completed_candle_close_utc="2026-07-17T08:00:00Z")
    assert report["ok"] is False
    assert report["padding_used"] is False
    assert any("duplicate" in error for error in report["errors"])
    assert any("future" in error for error in report["errors"])
    assert any("incomplete" in error for error in report["errors"])
    assert any("OHLC" in error for error in report["errors"])


def test_target_label_uses_only_future_completed_rows_and_settles():
    from core.reliable_quant_contract_20260717 import target_outcome_from_future_rows

    result = target_outcome_from_future_rows(
        entry_price=1.1000,
        direction="BUY",
        target_distance=0.0100,
        entry_candle_close_utc="2026-07-17T08:00:00Z",
        future_rows=[
            {"bar_close_utc": "2026-07-17T08:00:00Z", "is_complete": True, "high": 1.2000, "low": 1.0000},
            {"bar_close_utc": "2026-07-17T12:00:00Z", "is_complete": True, "high": 1.1150, "low": 1.0950},
        ],
    )
    assert result["settled"] is True
    assert result["target_reached"] is True
    assert result["future_rows_used"] == 1
    assert round(result["future_MFE"], 6) == 0.015


def test_probability_and_promotion_remain_shadow_only_without_settled_sample():
    from core.reliable_quant_contract_20260717 import promotion_gate, settled_target_probability

    probability = settled_target_probability([{"settled": True, "target_reached": True}] * 99)
    assert probability["probability_target_reached"] is None
    assert probability["research_only"] is True
    promotion = promotion_gate(
        settled_sample_size=99,
        out_of_sample=True,
        calibrated=True,
        no_lookahead=True,
        multiple_testing_registered=True,
    )
    assert promotion["promoted"] is False
    assert promotion["status"] == "SHADOW_ONLY"


def test_missing_cpi_or_ppi_event_evidence_blocks():
    from core.reliable_quant_contract_20260717 import event_risk_state

    before_release = event_risk_state(
        now_utc="2026-07-17T08:30:00Z",
        release_utc="2026-07-17T09:00:00Z",
        actual=None,
        consensus=None,
    )
    after_release = event_risk_state(
        now_utc="2026-07-17T09:30:00Z",
        release_utc="2026-07-17T09:00:00Z",
        actual=None,
        consensus=None,
    )
    assert before_release["state"] == "PRE_EVENT"
    assert after_release["state"] == "RELEASED_UNCONFIRMED"
    assert before_release["permission"] == after_release["permission"] == "BLOCK"
    assert before_release["surprise_z"] is None


def test_utility_ranking_is_deterministic_and_cost_aware():
    from core.reliable_quant_contract_20260717 import deterministic_rank_rows, expected_net_value

    assert expected_net_value(probability_target_reached=0.7, expected_mfe=10, expected_mae=5, spread_cost=1) == 4.5
    rows = [
        {"Symbol": "GBPUSD", "Expected Net Value": 4.0, "Trade Permission": "ALLOW", "Data Quality": "A"},
        {"Symbol": "EURUSD", "Expected Net Value": 4.0, "Trade Permission": "ALLOW", "Data Quality": "A"},
        {"Symbol": "USDJPY", "Expected Net Value": "UNAVAILABLE", "Trade Permission": "BLOCK_RESEARCH_ONLY", "Data Quality": "UNKNOWN"},
    ]
    ranked = deterministic_rank_rows(rows)
    assert [row["Symbol"] for row in ranked] == ["EURUSD", "GBPUSD", "USDJPY"]
    assert [row["Rank"] for row in ranked] == [1, 2, 3]


def test_trade_identity_rejects_selector_mutation():
    from core.reliable_quant_contract_20260717 import freeze_trade_identity, validate_trade_update

    trade = freeze_trade_identity(
        trade_id="T1", symbol="EURUSD", timeframe="4H", entry_time_utc="2026-07-17T08:00:00Z",
        entry_snapshot_hash="hash-a", provider="TEST", entry_price=1.1, stop_price=1.09, target_price=1.12,
    ).to_dict()
    changed = dict(trade, symbol="GBPUSD")
    result = validate_trade_update(trade, changed)
    assert result["ok"] is False
    assert "symbol" in result["changed_fields"]


def test_authority_persistence_is_append_only_and_exact_restore_is_read_only(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ADX_FIELD10_AUTHORITY_DB_PATH", str(tmp_path / "authority.sqlite3"))
    from core.field10_unified_authority_20260709 import build_unified_field10_authority, load_saved_field10_authority

    source = pd.DataFrame([
        {"Symbol": "EURUSD", "Load Status": "READY", "Sample Count": 250, "Data Quality Grade": "A", "Less-Risky Bias": "BUY", "Provider Used": "TEST"},
        {"Symbol": "GBPUSD", "Load Status": "READY", "Sample Count": 250, "Data Quality Grade": "A", "Less-Risky Bias": "SELL", "Provider Used": "TEST"},
    ])
    state = {
        "canonical_ranking_timeframe": "H4",
        "adx_current_selected_symbols_20260708": ["EURUSD", "GBPUSD"],
        "completed_broker_candle": "2026-07-17T08:00:00Z",
    }
    built = build_unified_field10_authority(state, source_frame=source, persist=True)
    assert built["snapshot"]["cross_device_parity_status"] == "CROSS_DEVICE_PARITY_UNVERIFIED"
    before = sqlite3.connect(tmp_path / "authority.sqlite3").execute("SELECT COUNT(*) FROM field10_unified_rank_snapshot").fetchone()[0]

    reopened = {
        "canonical_ranking_timeframe": "4H",
        "adx_current_selected_symbols_20260708": ["EURUSD", "GBPUSD"],
        "completed_broker_candle": "2026-07-17T09:00:00+00:00",
    }
    loaded = load_saved_field10_authority(reopened)
    assert loaded is not None
    assert loaded["reused_from"] == "DURABLE_FIELD10_AUTHORITY_SQLITE"
    assert loaded["snapshot"]["snapshot_hash"] == built["snapshot"]["snapshot_hash"]
    after = sqlite3.connect(tmp_path / "authority.sqlite3").execute("SELECT COUNT(*) FROM field10_unified_rank_snapshot").fetchone()[0]
    assert after == before == 1


def test_display_adapters_do_not_call_authority_builder():
    field12 = Path("ui/lunch_field12_higher_regime_rank.py").read_text(encoding="utf-8")
    field10 = Path("ui/lunch_field10_multi_symbol_20260701.py").read_text(encoding="utf-8")
    dinner = Path("tabs/field456789_page_20260626.py").read_text(encoding="utf-8")
    assert "build_unified_field10_authority" not in field12
    assert "build_unified_field10_authority(state, source_frame=table, persist=True)" not in field10
    assert "build_unified_field10_authority(st.session_state, persist=True)" not in dinner


def test_paper_trade_store_keeps_entry_identity_when_closed(tmp_path: Path):
    from core.reliable_quant_contract_20260717 import freeze_trade_identity
    from core.trade_identity_store_20260717 import close_trade, record_trade

    db = tmp_path / "trade.sqlite3"
    identity = freeze_trade_identity(
        trade_id="T-1", symbol="EURUSD", timeframe="H4", entry_time_utc="2026-07-17T08:00:00Z",
        entry_snapshot_hash="SNAP-1", provider="TEST", entry_price=1.1, stop_price=1.09, target_price=1.12,
    )
    assert record_trade(identity, path=db)["status"] == "RECORDED"
    assert record_trade(identity, path=db)["status"] == "IDEMPOTENT_EXISTING"
    closed = close_trade("T-1", exit_reason="TIME_EXPIRY", event_time_utc="2026-07-17T12:00:00Z", path=db)
    assert closed["status"] == "CLOSED"
    with sqlite3.connect(db) as conn:
        row = conn.execute("SELECT symbol,timeframe,entry_snapshot_hash,status,exit_reason FROM field10_trade_identity WHERE trade_id='T-1'").fetchone()
    assert row == ("EURUSD", "H4", "SNAP-1", "CLOSED", "TIME_EXPIRY")
