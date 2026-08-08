from __future__ import annotations

from pathlib import Path

import pandas as pd

import core.multi_symbol_field10_20260701 as ms


def _ohlc(rows: int = 700) -> pd.DataFrame:
    time = pd.date_range("2026-06-01", periods=rows, freq="h", tz="UTC")
    base = pd.Series(range(rows), dtype=float) / 10000.0 + 1.2
    return pd.DataFrame({
        "time": time,
        "open": base,
        "high": base + 0.0010,
        "low": base - 0.0010,
        "close": base + 0.0002,
    })


def test_main_symbol_runs_requested_scope_and_secondaries_run_lunch_core(tmp_path: Path, monkeypatch):
    state = {
        ms.MAIN_SYMBOL_KEY: "GBPJPY",
        ms.SELECTED_KEY: ["EURUSD", "GBPJPY", "XAUUSD"],
        "symbol": "GBPJPY",
        "timeframe": "H1",
        "settings_calculation_scope_20260625": "QUICK",
    }
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(ms, "_cache_path", lambda symbol: tmp_path / f"{symbol}.pkl.gz")
    monkeypatch.setattr(ms, "_rank_persisted_rows", lambda *args, **kwargs: None)
    monkeypatch.setattr(ms, "load_field10_tables", lambda *args, **kwargs: {
        "summary": pd.DataFrame(), "daily": pd.DataFrame(), "hourly": pd.DataFrame(),
    })
    monkeypatch.setattr(ms, "_persist_symbol_evidence", lambda current, **kwargs: {
        "symbol": current["symbol"],
        "status": "COMPLETED",
        "quality": {"grade": "A"},
        "field_validation": [
            {"Field": number, "Status": "PASS"} for number in range(1, 10)
        ],
        "broker_day": "2026-07-02",
        "run_id": f"RUN-{current['symbol']}",
        "source_id": f"SRC-{current['symbol']}",
    })

    import core.canonical_runtime_20260617 as canonical_runtime
    monkeypatch.setattr(
        canonical_runtime,
        "get_canonical",
        lambda current: current.get("canonical_decision_result_20260617") or {},
    )

    import core.field3_regime_lifecycle_monitor_20260701 as field3
    monkeypatch.setattr(field3, "build_field3_regime_lifecycle_monitor", lambda *args, **kwargs: {
        "status": "AVAILABLE", "symbol": state["symbol"], "history_25d": [{"ok": True}],
    })

    def runner():
        symbol = state["symbol"]
        scope = state["settings_calculation_scope_20260625"]
        calls.append((symbol, scope))
        state["canonical_decision_result_20260617"] = {
            "run_id": f"RUN-{symbol}",
            "symbol": symbol,
            "timeframe": "H1",
            "source_id": f"SRC-{symbol}",
            "latest_completed_candle_time": "2026-07-02T10:00:00+00:00",
        }
        state["canonical_completed_ohlc_df_20260617"] = _ohlc()
        return {"ok": True, "canonical": {"ok": True}}

    manifest = ms.run_selected_symbols(state, runner, scope="QUICK")

    assert calls == [
        ("EURUSD", "QUICK"),
        ("GBPJPY", "LUNCH_CORE"),
        ("XAUUSD", "LUNCH_CORE"),
    ]
    assert manifest["main_symbol"] == "EURUSD"
    assert manifest["fields_4_to_9_symbol"] == "EURUSD"
    assert manifest["scope_matrix"] == {
        "EURUSD": "FIELDS_1_TO_9_PLUS_AI",
        "GBPJPY": "FIELDS_1_TO_3_PLUS_FIELDS_10_11",
        "XAUUSD": "FIELDS_1_TO_3_PLUS_FIELDS_10_11",
    }
    assert manifest["symbol_summaries"]["EURUSD"]["field_validation"] == [
        {"Field": field, "Status": "PASS"} for field in range(1, 10)
    ]
    assert manifest["symbol_summaries"]["GBPJPY"]["field_validation"] == [
        {"Field": 1, "Status": "PASS"},
        {"Field": 2, "Status": "PASS"},
        {"Field": 3, "Status": "PASS"},
    ]
    assert state["symbol"] == "EURUSD"
    assert state[ms.ACTIVE_KEY] == "EURUSD"
    assert state[ms.DISPLAY_SYMBOL_KEY] == "EURUSD"
    assert state["settings_calculation_scope_20260625"] == "QUICK"


def test_routing_and_ui_contracts_are_wired_in_source():
    root = Path(__file__).resolve().parents[1]
    orchestrator = (root / "core/settings_run_orchestrator_v9_parts/part_001.py").read_text(encoding="utf-8")
    orchestrator_2 = (root / "core/settings_run_orchestrator_v9_parts/part_002.py").read_text(encoding="utf-8")
    orchestrator_4 = (root / "core/settings_run_orchestrator_v9_parts/part_004.py").read_text(encoding="utf-8")
    lunch = (root / "ui/lunch_four_core_fields_20260619.py").read_text(encoding="utf-8")
    field10 = (root / "ui/lunch_field10_multi_symbol_20260701.py").read_text(encoding="utf-8")
    table5 = (root / "ui/lunch_next_hour_bias_history_20260626.py").read_text(encoding="utf-8")
    router = (root / "tabs/antd_page_router_20260615.py").read_text(encoding="utf-8")
    connection = (root / "core/navigation_parts/connection.py").read_text(encoding="utf-8")
    sidebar = (root / "ui/sidebar_fallback_panel.py").read_text(encoding="utf-8")

    assert 'quick_scope = requested_scope == "LUNCH_CORE"' in orchestrator
    assert '"fields": [1, 2, 3] if quick_scope else list(range(1, 10))' in orchestrator
    assert "SKIPPED_FOR_QUICK_FIELDS_1_2_3" in orchestrator_2
    assert '"scope": "QUICK_FIELDS_1_2_3"' in orchestrator_4

    selector_call = lunch.index("_render_lunch_symbol_selector(state)")
    copy_call = lunch.index("render_lunch_top_copy_buttons(state)", selector_call)
    assert selector_call < copy_call
    assert "Display completed result for symbol" not in field10
    assert "Multi-Symbol Calculation Scope Matrix" in field10
    assert "Cross-Symbol Allocation and Entry Readiness" in field10
    assert "allow_cards=False" in field10
    assert "Field 3 Higher-Standard Multi-Symbol Bias + Consolidated Field 10 — All Loaded Settings Symbols" in field10

    assert "Master-Action Distribution" in table5
    assert "Download Table 5 CSV" in table5
    assert "Reliability & Outcome" in table5

    assert "ensure_main_symbol_active(st.session_state)" in router
    assert "Saved connection reused" in connection
    assert "_twelve_key_digest" in connection
    assert "Connect Once Using Saved Settings" in sidebar
    assert "Refresh Main Feed" in sidebar


def test_field3_publishes_for_non_eurusd_main_symbol():
    from core.field3_regime_lifecycle_monitor_20260701 import build_field3_regime_lifecycle_monitor

    frame = _ohlc(760)
    snapshot = {
        "run_id": "GBPJPY-FIELD3-ROUTING",
        "generation_id": "1",
        "source_snapshot_hash": "gbpjpy-routing-hash",
        "snapshot_hash": "gbpjpy-routing-hash",
        "symbol": "GBPJPY",
        "timeframe": "H1",
        "broker_candle_time": frame["time"].iloc[-1],
        "regime": "RANGE",
        "decision": "WAIT",
        "less_risky_decision": "WAIT",
    }
    state = {
        "canonical_completed_ohlc_df_20260617": frame,
        "canonical_result_20260617": snapshot,
        ms.MAIN_SYMBOL_KEY: "GBPJPY",
        "symbol": "GBPJPY",
    }
    payload = build_field3_regime_lifecycle_monitor(snapshot, state, force=True)

    assert payload["status"] == "AVAILABLE"
    assert payload["symbol"] == "GBPJPY"
    assert payload["history_25d"]
    assert all(str(row.get("Symbol") or "GBPJPY").upper() == "GBPJPY" for row in payload["history_25d"][:5])
