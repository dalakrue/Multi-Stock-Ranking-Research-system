from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


def _frame(rows: int, timeframe: str = "H1", symbol: str = "EURUSD") -> pd.DataFrame:
    freq = {"H1": "h", "H4": "4h", "D1": "D"}[timeframe]
    times = pd.date_range("2026-01-01", periods=rows, freq=freq, tz="UTC")
    trend = np.linspace(0.0, 0.02, rows)
    wave = np.sin(np.arange(rows) / 7.0) * 0.001
    close = 1.10 + trend + wave
    open_ = np.r_[close[0], close[:-1]]
    return pd.DataFrame({
        "time": times,
        "open": open_,
        "high": np.maximum(open_, close) + 0.0005,
        "low": np.minimum(open_, close) - 0.0005,
        "close": close,
        "volume": np.arange(rows) + 100,
        "symbol": symbol,
    })


def _payload(symbol: str, rows: int, timeframe: str = "H1") -> dict:
    return {
        "ok": True,
        "status": "CACHED_VALID",
        "validation_status": "VALID",
        "provider": "LOCAL_VALID_CACHE",
        "symbol": symbol,
        "timeframe": timeframe,
        "frame": _frame(rows, timeframe, symbol),
    }


def test_minimum_history_contract_accepts_100_genuine_candles():
    from core.timeframe_window_contract_20260706 import (
        calculation_eligibility,
        minimum_calculation_candles,
        required_candles,
    )

    assert required_candles("H1") == 600
    assert required_candles("H4") == 150
    assert minimum_calculation_candles("H1") == 100
    assert minimum_calculation_candles("H4") == 100
    assert minimum_calculation_candles("D1") == 25
    assert calculation_eligibility(timeframe="H1", available=597)["mode"] == "ADAPTIVE_PARTIAL_HISTORY"
    assert calculation_eligibility(timeframe="H1", available=100)["eligible"] is True
    assert calculation_eligibility(timeframe="H1", available=99)["eligible"] is False


def test_loader_accepts_597_and_100_but_rejects_99():
    from core.multi_symbol_load_manager_20260707 import _validate_result

    almost_full = _validate_result(_payload("EURUSD", 597), symbol="EURUSD", timeframe="H1", required_rows=600)
    adaptive = _validate_result(_payload("GBPCHF", 100), symbol="GBPCHF", timeframe="H1", required_rows=600)
    below = _validate_result(_payload("AUDJPY", 99), symbol="AUDJPY", timeframe="H1", required_rows=600)

    assert almost_full["ok"] is True
    assert almost_full["calculation_mode"] == "ADAPTIVE_PARTIAL_HISTORY"
    assert almost_full["rows"] == 597
    assert adaptive["ok"] is True
    assert adaptive["minimum_rows"] == 100
    assert below["ok"] is False
    assert "BELOW_MINIMUM" in below["reason"]


def test_adaptive_field10_metrics_are_numeric_at_100_candles():
    from core.field10_adaptive_regime_metrics_20260702 import compute_adaptive_regime_metrics

    report = compute_adaptive_regime_metrics(_frame(100, "H1"), timeframe="H1")
    assert report["ok"] is True
    assert report["status"] == "ADAPTIVE_PARTIAL_HISTORY_DERIVED"
    assert report["sample_count"] == 100
    assert report["full_history"] is False
    for key in (
        "expected_return_12h", "expected_return_24h", "expected_return_36h",
        "calibrated_reliability", "regime_probability", "transition_risk_3h",
    ):
        assert report[key] is not None
        assert math.isfinite(float(report[key]))


def test_cumulative_activation_merges_all_loaded_groups_without_six_symbol_cap():
    from core.calculation.run_orchestrator import MARKET_RESULTS_KEY
    from core.multi_symbol_load_manager_20260707 import (
        LOAD_RECORDS_KEY,
        activate_loaded_universe_for_run,
        selection_signature,
    )

    configured = {
        "FIRST": ["EURUSD", "USDJPY", "AUDUSD"],
        "SECOND": ["EURCHF", "EURAUD", "EURCAD"],
        "THIRD": ["GBPAUD", "GBPCAD", "AUDJPY"],
    }
    records = {}
    for group, symbols in configured.items():
        results = {symbol: _payload(symbol, 100, "H1") for symbol in symbols}
        records[group] = {
            "load_id": f"LOAD-{group}",
            "group": group,
            "scope": {"FIRST": "LUNCH_CORE", "SECOND": "QUICK", "THIRD": "FULL"}[group],
            "timeframe": "H1",
            "selection_signature": selection_signature(symbols, "H1"),
            "requested_symbols": list(symbols),
            "loaded_symbols": list(symbols),
            "failed_symbols": [],
            "report": {"results": results},
        }
    state = {LOAD_RECORDS_KEY: records, "timeframe": "H1"}

    activated = activate_loaded_universe_for_run(state, "LUNCH_CORE", configured, "H1")
    expected = configured["FIRST"] + configured["SECOND"] + configured["THIRD"]
    assert activated["ok"] is True
    assert activated["loaded_symbols"] == expected
    assert len(activated["loaded_symbols"]) == 9
    assert state["multi_symbol_selected_20260701"] == expected
    assert list(state[MARKET_RESULTS_KEY]["results"]) == expected
    assert state["multi_symbol_loaded_run_active_20260707"]["group"] == "ALL_LOADED"


def test_third_defaults_exclude_requested_removed_symbols():
    from core.multi_symbol_run_groups_20260706 import DEFAULT_GROUPS

    removed = {"EURUSD", "USDJPY", "GBPUSD"}
    assert len(DEFAULT_GROUPS["THIRD"]) == 6
    assert removed.isdisjoint(DEFAULT_GROUPS["THIRD"])
    assert DEFAULT_GROUPS["THIRD"][:3] == ["GBPAUD", "GBPCAD", "AUDJPY"]


def test_database_migration_creates_selector_and_load_audit_tables(tmp_path: Path):
    from core.data.deployment_migrations_20260705 import migrate_deployment_schema

    db = tmp_path / "repair.sqlite3"
    result = migrate_deployment_schema(db)
    assert result["ok"] is True
    with sqlite3.connect(db) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "runtime_symbol_groups_20260706" in tables
        assert "multi_symbol_load_audit_20260707" in tables
        row = conn.execute(
            "SELECT migration_name FROM deployment_schema_migrations ORDER BY version DESC LIMIT 1"
        ).fetchone()
    assert row and "adaptive_partial_history" in row[0]


def test_group_preferences_auto_save_and_restore(tmp_path: Path):
    from core.multi_symbol_run_groups_20260706 import (
        COMPLETED_UNION_KEY,
        FIRST_GROUP_KEY,
        SECOND_GROUP_KEY,
        THIRD_GROUP_KEY,
        load_group_preferences,
        save_group_preferences,
    )

    db = tmp_path / "groups.sqlite3"
    state = {
        FIRST_GROUP_KEY: ["EURUSD", "AUDUSD"],
        SECOND_GROUP_KEY: ["EURCHF"],
        THIRD_GROUP_KEY: ["GBPAUD", "GBPCAD", "AUDJPY"],
        COMPLETED_UNION_KEY: ["EURUSD"],
    }
    save_group_preferences(db, state)
    restored = load_group_preferences(db)
    assert restored["first"] == state[FIRST_GROUP_KEY]
    assert restored["second"] == state[SECOND_GROUP_KEY]
    assert restored["third"] == state[THIRD_GROUP_KEY]
    assert restored["completed"] == state[COMPLETED_UNION_KEY]


def test_selector_widget_is_authoritative_after_first_seed():
    source = Path("ui/multi_symbol_settings_20260701.py").read_text(encoding="utf-8")
    assert 'if item["widget_key"] not in state:' in source
    assert 'state[item["state_key"]] = list(widget_selected)' in source
    assert 'state[item["widget_key"]] = list(selected)' in source
    # The old failure rewrote an already-instantiated widget from stale state.
    assert 'if widget_selected != selected' not in source


def test_597_h1_daily_validation_is_publishable_adaptive_not_full():
    from core.field10_daily_snapshot_contract_20260702 import validate_completed_h1_frame

    frame = _frame(597, "H1")
    latest = frame["time"].iloc[-1]
    report = validate_completed_h1_frame(frame, latest_completed_h1_utc=latest, symbol="EURUSD")
    assert report["status"] == "INCOMPLETE"
    assert report["eligible"] is True
    assert report["calculation_mode"] == "ADAPTIVE_PARTIAL_HISTORY"
    assert report["sample_count"] == 597
