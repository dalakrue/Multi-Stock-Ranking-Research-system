from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from core.field10_adaptive_regime_metrics_20260702 import compute_adaptive_regime_metrics
from core.field10_unified_migration_20260703 import (
    _frame_for_exact_symbol,
    _frame_through_cutoff,
    migrate_and_verify_field10,
)
from ui.lunch_field10_multi_symbol_20260701 import _rank_column_order


def _synthetic_h1(rows: int = 720) -> pd.DataFrame:
    index = pd.date_range("2026-05-01", periods=rows, freq="h", tz="UTC")
    wave = np.sin(np.arange(rows) / 22.0) * 0.00025
    drift = np.arange(rows) * 0.000003
    close = 1.08 + drift + np.cumsum(wave)
    return pd.DataFrame(
        {
            "Open": close - 0.00005,
            "High": close + 0.00025,
            "Low": close - 0.00025,
            "Close": close,
            "Volume": np.linspace(100, 250, rows),
        },
        index=index,
    )


def test_adaptive_metrics_publish_requested_horizons() -> None:
    result = compute_adaptive_regime_metrics(_synthetic_h1())
    assert result["ok"] is True
    assert 0.0 <= float(result["transition_risk_24h"]) <= 100.0
    for horizon in (12, 24, 36):
        assert result[f"expected_return_{horizon}h"] is not None
        assert int(result[f"expected_return_{horizon}h_sample_count"]) >= 20


def test_unified_migration_adds_and_backfills_rank_columns(tmp_path: Path) -> None:
    db = tmp_path / "legacy.sqlite3"
    # Build all current tables first, then seed a legacy-style daily row whose
    # only transition evidence is the old six-hour field.
    first = migrate_and_verify_field10(db)
    assert first["ok"] is True
    with sqlite3.connect(db) as conn:
        conn.execute(
            """INSERT INTO field10_daily_higher_lock(
                broker_day,symbol,higher_standard_regime,less_risky_bias,
                data_quality_grade,data_quality_score,higher_transition_risk,
                lock_status,locked_at_broker_time,last_reviewed_broker_time,parent_run_id
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            ("2026-07-03", "EURUSD", "BULL_TREND", "BUY", "A", 95.0, 20.0,
             "TODAY_LOCKED_UNTIL_23H", "2026-07-03T03:00:00", "2026-07-03T03:00:00", "parent"),
        )
        conn.execute(
            "UPDATE field10_daily_higher_lock SET transition_risk_24h=NULL WHERE broker_day='2026-07-03' AND symbol='EURUSD'"
        )
        conn.commit()
    report = migrate_and_verify_field10(db)
    assert report["ok"] is True
    with sqlite3.connect(db) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(field10_daily_higher_lock)")}
        assert {
            "transition_risk_24h", "expected_return_12h",
            "expected_return_24h", "expected_return_36h",
        }.issubset(columns)
        row = conn.execute(
            "SELECT transition_risk_24h,expected_return_12h,expected_return_24h,expected_return_36h "
            "FROM field10_daily_higher_lock "
            "WHERE broker_day='2026-07-03' AND symbol='EURUSD'"
        ).fetchone()
    assert row[0] == pytest_approx(59.04, abs=1e-6)
    assert row[1:] == (None, None, None)  # migration never fabricates zero expected returns


def pytest_approx(value: float, *, abs: float):
    import pytest
    return pytest.approx(value, abs=abs)


def test_field10_ui_has_one_authoritative_rank_surface() -> None:
    source = Path("ui/lunch_field10_multi_symbol_20260701.py").read_text(encoding="utf-8")
    assert source.count("Today First — Ranked Multi-Symbol Decision Table") == 1
    assert "Multi-Symbol Run and Rank Summary" not in source
    assert "Today — Locked Higher-Standard Regime, Rank, Data Quality and Less-Risky Bias" not in source
    assert "Legacy / Diagnostics — Previous Field 10 Surfaces" in source
    assert "Saved child generation" not in source
    assert "Transition Risk 24H" in source
    assert "Expected Return 12H" in source
    assert "Expected Return 24H" in source
    assert "Expected Return 36H" in source
    assert 'pinned="left"' in source


def test_cross_symbol_backfill_is_rejected() -> None:
    frame = pd.DataFrame({
        "symbol": ["EURUSD", "EURUSD"],
        "close": [1.08, 1.09],
    })
    assert len(_frame_for_exact_symbol(frame, "EURUSD")) == 2
    assert _frame_for_exact_symbol(frame, "USDJPY").empty
    unidentified = frame.drop(columns=["symbol"])
    assert _frame_for_exact_symbol(unidentified, "EURUSD").empty


def test_rank_column_order_places_requested_horizons_first() -> None:
    frame = pd.DataFrame({
        "Daily Rank": [1],
        "Symbol": ["EURUSD"],
        "Expected Return 36H (%)": [0.3],
        "Expected Return 24H (%)": [0.2],
    })
    ordered = _rank_column_order(frame)
    assert list(ordered.columns[:2]) == ["Expected Return 24H (%)", "Expected Return 36H (%)"]


def test_settings_and_lunch_use_same_migration_version() -> None:
    settings_source = Path("core/multi_symbol_field10_20260701.py").read_text(encoding="utf-8")
    lunch_source = Path("ui/lunch_four_core_fields_20260619.py").read_text(encoding="utf-8")
    assert "migrate_and_verify_field10(DB_PATH)" in settings_source
    assert "field10-unified-rank-columns-20260703-v2" in lunch_source
    assert "migrate_and_verify_field10()" in lunch_source


def test_historical_backfill_respects_completed_candle_cutoff() -> None:
    frame = pd.DataFrame({
        "time": pd.date_range("2026-07-01T00:00:00Z", periods=4, freq="h"),
        "symbol": ["EURUSD"] * 4,
        "close": [1.0, 1.1, 1.2, 1.3],
    })
    causal = _frame_through_cutoff(frame, "2026-07-01T01:00:00Z")
    assert len(causal) == 2
    assert causal["close"].max() == 1.1
