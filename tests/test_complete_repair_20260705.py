from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from core.complete_repair_20260705 import (
    LOW_SPREAD_THRESHOLD_POINTS,
    SECONDARY_SYMBOL_POOL,
    DataProvenance,
    build_cache_identity,
    fallback_label,
    migrate_complete_repair_schema,
    refresh_lunch_snapshot,
    select_low_spread_top8,
    select_secondary_top10,
)
from core.field11_similar_path_simulator_20260702 import _resample_ohlc


def test_secondary_pool_is_exact_and_excludes_primary_three():
    assert len(SECONDARY_SYMBOL_POOL) == 15
    assert set(("EURUSD", "GBPUSD", "USDJPY")).isdisjoint(SECONDARY_SYMBOL_POOL)
    assert SECONDARY_SYMBOL_POOL[:4] == ("AUDUSD", "NZDUSD", "USDCAD", "USDCHF")


def test_low_spread_preset_uses_measured_evidence_only():
    state = {
        "recent_spread_metrics_20260705": {
            "AUDUSD": {"average_spread": 8, "sample_size": 120, "provider": "TWELVE_DATA"},
            "NZDUSD": {"average_spread": 19.9, "sample_size": 90, "provider": "FINNHUB"},
            "USDCAD": {"average_spread": 20, "sample_size": 200, "provider": "TWELVE_DATA"},
            "USDCHF": {"average_spread": 21, "sample_size": 200, "provider": "TWELVE_DATA"},
            "EURGBP": {"average_spread": 5, "sample_size": 0, "provider": "TWELVE_DATA"},
        }
    }
    selected, evidence = select_low_spread_top8(state)
    assert selected == ["AUDUSD", "NZDUSD"]
    assert not evidence.empty
    assert (evidence["Average Spread"] < LOW_SPREAD_THRESHOLD_POINTS).all()
    assert (evidence["Sample Size"] > 0).all()


def test_secondary_top10_is_deterministic_without_fabricated_spread_claims():
    selected, evidence = select_secondary_top10({})
    assert selected == list(SECONDARY_SYMBOL_POOL[:10])
    assert evidence["Measured Average Spread"].isna().all()
    assert set(evidence["Spread Evidence"]) == {"NOT MEASURED"}


def test_cache_identity_invalidates_on_required_dimensions():
    base = dict(
        symbols=["EURUSD", "USDJPY"], primary_symbol="EURUSD", timeframe="H1",
        run_id="run-1", latest_completed_candle="2026-07-05T18:00:00Z",
        provider="TWELVE_DATA", calculation_mode="QUICK",
    )
    original = build_cache_identity(**base)
    for key, replacement in (
        ("symbols", ["EURUSD", "GBPUSD"]),
        ("primary_symbol", "USDJPY"),
        ("timeframe", "H4"),
        ("run_id", "run-2"),
        ("latest_completed_candle", "2026-07-05T19:00:00Z"),
        ("provider", "FINNHUB"),
        ("calculation_mode", "FULL"),
    ):
        candidate = dict(base)
        candidate[key] = replacement
        assert build_cache_identity(**candidate) != original


def test_fallback_metadata_is_explicit_and_does_not_invent_price():
    provenance = DataProvenance(
        source="LOCAL_DATABASE", value_status="ESTIMATED_DERIVED_FEATURE",
        freshness_status="STALE", fallback_level=7, coverage_pct=42.0,
        reliability_score=18.0, note="raw OHLC not replaced",
    )
    payload = provenance.to_dict()
    assert "value" not in payload
    label = fallback_label(level=7, status=payload["value_status"], source=payload["source"])
    assert "L7" in label and "LOCAL DATABASE" in label


def test_migration_is_idempotent_and_preserves_existing_rows(tmp_path: Path):
    db = tmp_path / "repair.sqlite3"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE legacy_history(id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO legacy_history(value) VALUES('keep me')")
        conn.commit()
    first = migrate_complete_repair_schema(db, create_backup=True)
    second = migrate_complete_repair_schema(db, create_backup=False)
    assert first["ok"] and second["ok"]
    assert first["required_tables_present"] and second["required_tables_present"]
    assert first["backup"] and Path(first["backup"]).exists()
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT value FROM legacy_history").fetchone()[0] == "keep me"
        assert conn.execute("SELECT COUNT(*) FROM schema_version_20260705").fetchone()[0] == 1
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_refresh_is_read_only_and_preserves_context(monkeypatch):
    import core.field10_daily_snapshot_contract_20260702 as contract

    monkeypatch.setattr(contract, "load_current_daily_snapshot", lambda: {
        "current": pd.DataFrame([{"Symbol": "EURUSD"}]),
        "metadata": {"daily_snapshot_id": "snap-1"},
    })
    state = {
        "multi_symbol_selected_20260701": ["EURUSD", "USDJPY"],
        "timeframe": "H4",
        "lunch_active_field_selector_20260624": "10. Open / Close — Multi-Symbol Rank",
        "field10_render_cache_old": {"x": 1},
    }
    report = refresh_lunch_snapshot(state)
    assert report["heavy_calculation_started"] is False
    assert report["field10_rows"] == 1
    assert state["multi_symbol_selected_20260701"] == ["EURUSD", "USDJPY"]
    assert state["timeframe"] == "H4"
    assert state["lunch_active_field_selector_20260624"].startswith("10.")
    assert "field10_render_cache_old" not in state


def _minute_frame() -> pd.DataFrame:
    idx = pd.date_range("2026-07-01", periods=8 * 60, freq="min", tz="UTC")
    seq = pd.Series(range(len(idx)), index=idx, dtype=float)
    return pd.DataFrame({
        "time": idx,
        "open": 1 + seq / 10000,
        "high": 1.001 + seq / 10000,
        "low": 0.999 + seq / 10000,
        "close": 1.0005 + seq / 10000,
        "volume": 1.0,
        "spread": 2.0,
    })


def test_field11_resampling_uses_safe_ohlcv_rules_for_supported_timeframes():
    source = _minute_frame()
    for timeframe, expected_minutes in (("M1", 1), ("H1", 60), ("H4", 240), ("D1", 1440)):
        result = _resample_ohlc(source, timeframe)
        assert not result.empty
        if len(result) > 1:
            delta = int((result.iloc[1]["time"] - result.iloc[0]["time"]).total_seconds() // 60)
            assert delta == expected_minutes
        first = result.iloc[0]
        window = source.iloc[:expected_minutes]
        assert first["open"] == window.iloc[0]["open"]
        assert first["high"] == window["high"].max()
        assert first["low"] == window["low"].min()
        assert first["close"] == window.iloc[-1]["close"]
        assert first["volume"] == window["volume"].sum()
        assert first["spread"] == window["spread"].mean()


def test_field11_selector_and_field10_navigation_contracts_are_present():
    selector_source = Path("ui/lunch_multi_symbol_selector_20260704.py").read_text(encoding="utf-8")
    router_source = Path("tabs/antd_page_router_20260615.py").read_text(encoding="utf-8")
    assert "11:" in selector_source
    assert '"active_field": "Field 10"' in router_source
    assert '"field_10_expanded": True' in router_source
    assert '"scroll_target": "field-10-anchor"' in router_source


def test_copy_and_ai_context_include_structured_fields_10_and_11():
    source = Path("core/lunch_broker_sentiment_ai_history_20260622.py").read_text(encoding="utf-8")
    assert "_field10_field11_context" in source
    assert "field10_top_rows" in source
    assert "Field 11 result" in source
    assert "Field 10" in source and "Field 11" in source
