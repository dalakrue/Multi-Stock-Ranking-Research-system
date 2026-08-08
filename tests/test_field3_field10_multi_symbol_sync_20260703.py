from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from core.field3_bias_resolver_20260703 import resolve_standard_evidence
from core.field3_multi_symbol_fallback_20260703 import build_field3_local_snapshot
from core.multi_symbol_field10_20260701 import recover_symbol_universe
import core.system_continuous_validation_20260702 as validation


ROOT = Path(__file__).resolve().parents[1]


def _ohlc(direction: float = 1.0, rows: int = 700) -> pd.DataFrame:
    time = pd.date_range("2026-05-01", periods=rows, freq="h", tz="UTC")
    trend = direction * np.linspace(0.0, 0.08, rows)
    close = 1.10 + trend + np.sin(np.arange(rows) / 17.0) * 0.001
    return pd.DataFrame(
        {
            "time": time,
            "open": close - direction * 0.00015,
            "high": np.maximum(close, close - direction * 0.00015) + 0.0004,
            "low": np.minimum(close, close - direction * 0.00015) - 0.0004,
            "close": close,
        }
    )


def test_resolver_reads_only_higher_standard_row() -> None:
    frame = pd.DataFrame(
        [
            {"Standard": "Lower Standard", "Regime": "BULL", "Regime Bias": "BUY"},
            {"Standard": "Middle Standard", "Regime": "BULL", "Regime Bias": "BUY"},
            {"Standard": "Higher Standard", "Regime": "BEAR", "Regime Bias": "SELL", "Reliability": 83},
        ]
    )
    evidence = resolve_standard_evidence(frame, "higher")
    assert evidence["bias"] == "SELL"
    assert evidence["regime"] == "BEAR"
    assert evidence["reliability"] == 83


def test_recover_symbol_universe_repairs_stale_eurusd_widget_identity() -> None:
    state = {
        "multi_symbol_selected_20260701": ["EURUSD"],
        "multi_symbol_main_symbol_20260702": "EURUSD",
        "multi_symbol_active_20260701": "EURUSD",
        "lunch_display_symbol_20260702": "EURUSD",
        "symbol": "NZDUSD",
        "canonical_decision_result_20260617": {"symbol": "NZDUSD", "timeframe": "H1"},
    }
    recovered = recover_symbol_universe(state)
    assert recovered["main_symbol"] == "NZDUSD"
    assert recovered["active_symbol"] == "NZDUSD"
    assert recovered["selected_symbols"][0] == "NZDUSD"
    assert "EURUSD" in recovered["selected_symbols"]


def test_plan_b_local_field3_builds_all_three_standards() -> None:
    frame = _ohlc(1.0)
    state = {
        "symbol": "NZDUSD",
        "active_snapshot_symbol_20260702": "NZDUSD",
        "last_df": frame,
        "canonical_decision_result_20260617": {
            "symbol": "NZDUSD",
            "timeframe": "H1",
            "completed_candle_utc": frame["time"].iloc[-1],
        },
    }
    result = build_field3_local_snapshot(state, "NZDUSD", allow_provider_fetch=False)
    assert result["ok"] is True
    assert result["summary"]["Standard"].tolist() == [
        "Lower Standard",
        "Middle Standard",
        "Higher Standard",
    ]
    assert result["summary"].loc[result["summary"]["Standard"].eq("Higher Standard"), "Regime Bias"].iloc[0] in {"BUY", "SELL"}
    assert len(result["details"]["higher"]) == 600


def test_field10_top_table_ranks_every_symbol_without_cross_symbol_wait(monkeypatch) -> None:
    exact = {
        "EURUSD": {
            "symbol": "EURUSD",
            "last_df": _ohlc(1.0),
            "regime_standard_table_20260617": pd.DataFrame(
                [{"Standard": "Higher Standard", "Regime": "BULL", "Regime Bias": "BUY", "Reliability": 88}]
            ),
        },
        "NZDUSD": {
            "symbol": "NZDUSD",
            "last_df": _ohlc(-1.0),
            "regime_standard_table_20260617": pd.DataFrame(
                [{"Standard": "Higher Standard", "Regime": "BEAR", "Regime Bias": "SELL", "Reliability": 84}]
            ),
        },
    }
    monkeypatch.setattr(validation, "_exact_symbol_state", lambda state, symbol: exact[symbol])
    state = {
        "multi_symbol_selected_20260701": ["EURUSD", "NZDUSD"],
        "multi_symbol_main_symbol_20260702": "EURUSD",
        "symbol": "EURUSD",
        "canonical_decision_result_20260617": {"symbol": "EURUSD"},
    }
    table, report = validation.build_field3_higher_standard_multi_symbol_table(
        state, ["EURUSD", "NZDUSD"], parent_run_id=None
    )
    assert set(table["Symbol"]) == {"EURUSD", "NZDUSD"}
    assert set(table["Higher-Standard Bias"]) == {"BUY", "SELL"}
    assert table["Rank"].tolist() == [1, 2]
    assert report["wait_rows"] == 0


def test_ui_contains_field10_top_table_and_field3_top10_plan_b() -> None:
    field10 = (ROOT / "ui" / "lunch_field10_multi_symbol_20260701.py").read_text(encoding="utf-8")
    lunch = (ROOT / "ui" / "lunch_four_core_fields_20260619.py").read_text(encoding="utf-8")
    render = field10[field10.index("def render_field10_content"):]
    assert "_build_consolidated_field10_table_20260707" in render
    assert "Field 3 Higher-Standard Multi-Symbol Bias + Consolidated Field 10 — All Loaded Settings Symbols" in render
    assert "_render_field10_three_sections_20260706(state)" not in render
    assert "_render_locked_morning_snapshot" not in render
    assert "Plan B — Top 10 Currency Pairs" in lunch
    assert "TOP_10_CURRENCY_PAIRS" in lunch
    assert "lunch_symbol_selector_recovery_synced_20260703" in lunch
