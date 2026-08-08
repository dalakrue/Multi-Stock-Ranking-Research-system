from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd


def _frame(rows: int, hours: int = 4) -> pd.DataFrame:
    end = datetime(2026, 7, 6, 12, tzinfo=timezone.utc)
    times = [end - timedelta(hours=hours * (rows - 1 - index)) for index in range(rows)]
    return pd.DataFrame({
        "open_time": times,
        "open": [1.0] * rows,
        "high": [1.1] * rows,
        "low": [0.9] * rows,
        "close": [1.02] * rows,
        "volume": [100.0] * rows,
    })


def test_legacy_gen_string_is_numeric_and_bridge_never_republishes_it(monkeypatch):
    from core.generation_identity_20260707 import numeric_generation
    from core.field1_publication_bridge_20260626 import ensure_field1_publication

    legacy = "GEN-d95bb1bf93bb3e05"
    assert numeric_generation(legacy) > 0
    state = {
        "symbol": "EURUSD",
        "timeframe": "H4",
        "successful_calculation_generation_20260617": legacy,
        "last_df": _frame(160),
        "lunch_metric_result_cache": {
            "ok": True,
            "scores": {"Decision": "SELL"},
            "history": pd.DataFrame({"event_time_utc": [_frame(1).iloc[-1]["open_time"]]}),
        },
    }
    monkeypatch.setattr("core.canonical_lookup_20260626.resolve_canonical", lambda _state: {})
    result = ensure_field1_publication(state, {})
    canonical = result["canonical"]
    assert isinstance(canonical["calculation_generation"], int)
    assert canonical["calculation_generation"] > 0
    assert str(canonical["generation_id"]).startswith("GEN-")
    assert isinstance(state["successful_calculation_generation_20260617"], int)


def test_load_manager_admits_only_complete_exact_timeframe_symbols(monkeypatch):
    from core.calculation import run_orchestrator
    from core.multi_symbol_load_manager_20260707 import (
        activate_loaded_scope_for_run,
        load_group_market_data,
        loaded_group_status,
    )

    def fake_prepare(state, *, run_id, selected_symbols, timeframe, progress_callback=None, **_kwargs):
        report = {
            "run_id": run_id,
            "timeframe": timeframe,
            "results": {
                "EURUSD": {"ok": True, "status": "CACHED", "provider": "LOCAL_VALID_CACHE", "frame": _frame(160)},
                "GBPCHF": {"ok": True, "status": "CACHED", "provider": "LOCAL_VALID_CACHE", "frame": _frame(40)},
            },
            "complete": False,
        }
        state[run_orchestrator.MARKET_RESULTS_KEY] = report
        return report

    monkeypatch.setattr(run_orchestrator, "prepare_market_data_for_run", fake_prepare)
    state: dict = {"timeframe": "H4"}
    record = load_group_market_data(state, "FIRST", ["EURUSD", "GBPCHF"], "H4")
    assert record["loaded_symbols"] == ["EURUSD"]
    assert record["failed_symbols"] == ["GBPCHF"]
    assert record["validations"]["GBPCHF"]["reason"].startswith("INSUFFICIENT_LOCAL_HISTORY")

    exact = loaded_group_status(state, "FIRST", ["EURUSD", "GBPCHF"], "H4")
    assert exact["ready"] is True
    assert exact["status"] == "PARTIAL_READY"
    assert exact["loaded_symbols"] == ["EURUSD"]

    stale = loaded_group_status(state, "FIRST", ["EURUSD"], "H4")
    assert stale["ready"] is False
    assert stale["status"] == "STALE"

    activated = activate_loaded_scope_for_run(state, "LUNCH_CORE", ["EURUSD", "GBPCHF"], "H4")
    assert activated["ok"] is True
    assert state["multi_symbol_selected_20260701"] == ["EURUSD"]
    assert list(state[run_orchestrator.MARKET_RESULTS_KEY]["results"]) == ["EURUSD"]


def test_calculation_reuses_loaded_report_and_never_calls_loader(monkeypatch):
    from core.calculation import run_orchestrator

    state = {
        "require_explicit_multi_symbol_load_20260707": True,
        "multi_symbol_loaded_run_active_20260707": {
            "loaded_symbols": ["EURUSD"], "load_id": "LOAD-1",
        },
        "multi_symbol_selected_20260701": ["EURUSD"],
        "timeframe": "H4",
        run_orchestrator.MARKET_RESULTS_KEY: {
            "results": {"EURUSD": {"ok": True, "frame": _frame(160)}},
            "loaded_symbols": ["EURUSD"],
        },
    }
    monkeypatch.setattr(
        run_orchestrator,
        "prepare_market_data_for_run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("loader must not be called")),
    )
    monkeypatch.setattr(run_orchestrator, "finalize_canonical_run", lambda _state, _manifest, run_id: {"identity": {"snapshot_hash": "abc"}})

    result = run_orchestrator.execute_existing_multi_symbol_run(
        state,
        lambda: {},
        scope="LUNCH_CORE",
        progress_callback=None,
        existing_runner=lambda *_args, **_kwargs: {"ok": True, "status": "COMPLETED"},
    )
    assert result["calculation_reused_preloaded_data_20260707"] is True
    assert "multi_symbol_loaded_run_active_20260707" not in state


def test_settings_contract_exposes_three_load_buttons_and_compute_only_runs():
    from pathlib import Path

    settings = Path("ui/multi_symbol_settings_20260701.py").read_text(encoding="utf-8")
    router = Path("tabs/antd_page_router_20260615.py").read_text(encoding="utf-8")
    orchestrator = Path("core/calculation/run_orchestrator.py").read_text(encoding="utf-8")
    assert "Load Selected Data" in settings
    assert "Reload Failed Symbols" in settings
    assert "activate_loaded_scope_for_run" in router
    assert "Calculate Loaded First Selector" in router
    assert "Calculate Loaded Second Selector" in router
    assert "Calculate Loaded Third Selector" in router
    assert "calculation_reuses_preloaded_data" in orchestrator
    assert "Load Selected Data for this selector before starting calculation" in orchestrator
