from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pandas as pd


def test_selection_publisher_never_mutates_widget_owned_key(monkeypatch):
    import importlib
    import sys
    from types import SimpleNamespace

    monkeypatch.setitem(sys.modules, "streamlit", SimpleNamespace(session_state={}))
    module = importlib.import_module("ui.multi_symbol_settings_20260701")

    monkeypatch.setattr(module, "save_runtime_preferences", None, raising=False)
    state = {
        module._MULTI_WIDGET_KEY: ["EURUSD"],
        "timeframe": "H4",
    }
    module._publish_selection(state, ["USDJPY", "EURUSD"])
    assert state[module.SELECTED_KEY] == ["USDJPY", "EURUSD"]
    assert state[module._MULTI_WIDGET_KEY] == ["EURUSD"]


def test_runtime_first_load_defaults_to_h4_and_does_not_touch_widget_key():
    from core.runtime_selection_20260705 import synchronize_runtime_selection

    state: dict[str, object] = {}
    result = synchronize_runtime_selection(state)
    assert result["timeframe"] == "H4"
    assert state["timeframe"] == "H4"
    assert "multi_symbol_searchable_selector_widget_20260701" not in state


def test_guest_secret_autoconnect_is_real_and_idempotent(monkeypatch):
    import core.secure_api_startup_20260619 as module

    calls = {"market": 0, "finnhub": 0}

    monkeypatch.setattr(module, "initialize_secure_settings", lambda state: state.setdefault("auto_connect_after_login_20260619", True))
    monkeypatch.setattr(module, "secure_secret_status", lambda state: {
        "second_api_configured": True,
        "finnhub_configured": True,
        "second_api_source": "Streamlit Secrets",
        "finnhub_source": "Streamlit Secrets",
    })

    def market(state):
        calls["market"] += 1
        return {"ok": True, "source": "TWELVE", "message": "connected", "rows": 600}

    def finnhub(state):
        calls["finnhub"] += 1
        return {"ok": True, "status": "AVAILABLE", "message": "connected"}

    monkeypatch.setattr(module, "_connect_market", market)
    monkeypatch.setattr(module, "_validate_finnhub_once", finnhub)
    monkeypatch.setattr(module, "_latest_h1", lambda frame: None)
    monkeypatch.setattr(module, "_canonical_latest", lambda state: None)

    state = {
        "new7_auth_logged_in": True,
        "new7_auth_guest": True,
        "new7_auth_login_ts": 123.0,
        "symbol": "EURUSD",
        "timeframe": "H4",
    }
    first = module.run_guarded_startup(state)
    second = module.run_guarded_startup(state)
    assert first["status"] == "AUTO_CONNECTED"
    assert first["auto_connected"] is True
    assert second["status"] == "RERUN_GUARD"
    assert calls == {"market": 1, "finnhub": 1}
    assert state["twelve_data_connected"] is True


def test_scheduler_paces_live_twelve_requests_in_five_symbol_batches(tmp_path: Path):
    from core.data.market_data_orchestrator import MarketDataResult
    from core.data.multi_symbol_scheduler import MultiSymbolScheduler

    now = [0.0]
    sleeps: list[float] = []

    class Quota:
        def status(self):
            return SimpleNamespace(to_dict=lambda: {"next_safe_request_time": None})

    class Orchestrator:
        quota = Quota()

        def fetch(self, *, symbol, timeframe, **kwargs):
            frame = pd.DataFrame({
                "open_time": [pd.Timestamp("2026-07-05T00:00:00Z")],
                "open": [1.0], "high": [1.1], "low": [0.9], "close": [1.0], "volume": [1.0],
            })
            return MarketDataResult(
                ok=True, symbol=symbol, timeframe=timeframe, frame=frame,
                provider="TWELVE_DATA", provider_symbol=symbol, status="LIVE_PLAN_A",
                message="ok", latest_completed_candle="2026-07-05T00:00:00+00:00",
                fallback_provider=None,
                attempts=[{"provider": "TWELVE_DATA", "ok": True}],
                data_age_seconds=0.0, data_quality_score=100.0,
                validation_status="PASS", run_id="R",
            )

    def sleep(seconds: float):
        sleeps.append(seconds)
        now[0] += seconds

    scheduler = MultiSymbolScheduler(
        db_path=tmp_path / "pace.sqlite3",
        orchestrator=Orchestrator(),
        max_live_requests_per_window=5,
        sleep_fn=sleep,
        clock_fn=lambda: now[0],
    )
    symbols = ["EURUSD", "USDJPY", "AUDUSD", "GBPUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP", "NZDUSD"]
    report = scheduler.run(
        symbols=symbols,
        timeframe="H4",
        state={
            "quota_safe_stagger_enabled_20260706": True,
            "quota_safe_batch_size_20260706": 5,
            "quota_safe_batch_interval_seconds_20260706": 60,
        },
        force_live=True,
    )
    assert report["live_requests_started"] == 10
    assert sleeps == [60.0]
    assert report["quota_safe_stagger"]["batch_size"] == 5
    assert report["quota_safe_stagger"]["pause_count"] == 1


def test_h4_regime_windows_are_six_thirty_one_fifty(monkeypatch):
    import core.field3_multi_symbol_fallback_20260703 as module

    index = pd.date_range("2026-06-01", periods=180, freq="4h", tz="UTC")
    frame = pd.DataFrame({
        "time": index,
        "open": range(180), "high": [x + 1 for x in range(180)],
        "low": [x - 1 for x in range(180)], "close": range(180), "volume": [1] * 180,
    })
    monkeypatch.setattr(module, "_canonical", lambda state: {"symbol": "EURUSD", "timeframe": "H4"})
    monkeypatch.setattr("core.lunch_h1_data_quality_v13.cached_completed_ohlc", lambda state: frame)
    matrix = pd.DataFrame({
        "event_time_utc": index[::-1], "Close": list(range(180))[::-1],
        "Lower 1-Day Regime": ["BULL"] * 180, "Lower 1-Day Z-Score": [1.0] * 180,
        "Middle 5-Day Regime": ["BULL"] * 180, "Middle 5-Day Z-Score": [1.0] * 180,
        "Higher 25-Day Regime": ["BULL"] * 180, "Higher 25-Day Z-Score": [1.0] * 180,
        "Shadow Decision": ["BUY"] * 180, "Data Quality": ["PASS"] * 180,
        "Decision Level /10": [7.0] * 180,
    })
    monkeypatch.setattr("core.lunch_h1_data_quality_v13.build_regime_decision_matrix", lambda state, canonical, limit: matrix.head(limit))
    monkeypatch.setattr(module, "compute_adaptive_regime_metrics", lambda frame: {"ok": False})
    result = module._build_tables({"timeframe": "H4"}, "EURUSD", "TEST")
    assert result["ok"]
    assert result["timeframe"] == "H4"
    assert result["summary"]["Window"].tolist() == ["6 H4 candles", "30 H4 candles", "150 H4 candles"]


def test_lunch_navigation_consumes_pending_selection_before_widget(monkeypatch):
    import importlib
    import sys
    from types import SimpleNamespace

    fake = SimpleNamespace(session_state={})
    monkeypatch.setitem(sys.modules, "streamlit", fake)
    module = importlib.reload(importlib.import_module("lunch.navigation"))
    fake.session_state[module.SELECTED_KEY] = "field_01"
    fake.session_state[module.PENDING_SELECTED_KEY] = "field_03"
    module._initialize(["field_01", "field_02", "field_03"])
    assert fake.session_state[module.SELECTED_KEY] == "field_03"
    assert module.PENDING_SELECTED_KEY not in fake.session_state


def test_settings_connection_fallbacks_are_h4():
    router = Path("tabs/antd_page_router_20260615.py").read_text()
    connection = Path("core/navigation_parts/connection.py").read_text()
    assert 'normalize_timeframe(st.session_state.get("timeframe") or "H4")' in router
    assert 'get("timeframe", "H4") or "H4"' in connection
