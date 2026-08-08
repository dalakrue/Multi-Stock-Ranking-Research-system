from __future__ import annotations

from pathlib import Path

import pandas as pd


def _frame(symbol: str, timeframe: str, rows: int = 120) -> pd.DataFrame:
    freq = "h" if timeframe == "H1" else "4h"
    times = pd.date_range("2026-01-01", periods=rows, freq=freq, tz="UTC")
    close = pd.Series(range(rows), dtype=float) / 10000.0 + 1.10
    return pd.DataFrame({
        "open_time": times,
        "open": close,
        "high": close + 0.0004,
        "low": close - 0.0004,
        "close": close + 0.0001,
        "volume": 1000.0,
        "symbol": symbol,
        "timeframe": timeframe,
        "provider": "FINNHUB",
        "provider_symbol": symbol,
        "validation_status": "VALID",
    })


def test_all_three_selectors_keep_exact_capacity_and_fast_finnhub_load(monkeypatch, tmp_path: Path):
    from core.calculation import run_orchestrator
    from core.data import deployment_migrations_20260705 as migrations
    from core.multi_symbol_load_manager_20260707 import load_group_market_data

    monkeypatch.setattr(migrations, "DEFAULT_DB_PATH", tmp_path / "selector-load.sqlite3")
    calls: list[dict[str, object]] = []

    def fake_prepare(state, *, run_id, selected_symbols, timeframe, progress_callback=None):
        calls.append({
            "symbols": list(selected_symbols),
            "stagger": state.get("quota_safe_stagger_enabled_20260706"),
            "rounds": state.get("multi_symbol_fetch_rounds_20260706"),
            "scope": state.get("settings_calculation_scope_20260625"),
            "provider": state.get("fast_multi_symbol_primary_provider_20260708"),
        })
        results = {
            symbol: {
                "ok": True,
                "symbol": symbol,
                "timeframe": timeframe,
                "frame": _frame(symbol, timeframe),
                "provider": "FINNHUB",
                "provider_symbol": symbol,
                "status": "LIVE_PRIMARY",
                "validation_status": "VALID",
                "latest_completed_candle": "2026-01-05T23:00:00+00:00",
            }
            for symbol in selected_symbols
        }
        return {"run_id": run_id, "results": results, "complete": True}

    monkeypatch.setattr(run_orchestrator, "prepare_market_data_for_run", fake_prepare)
    state: dict[str, object] = {
        "connector_mode": "finnhub",
        "finnhub_api_key": "test",
        "twelve_api_key": "fallback",
    }
    first = ["EURUSD", "USDJPY", "AUDUSD", "GBPUSD", "USDCAD", "USDCHF",
             "EURJPY", "GBPJPY", "EURGBP", "NZDUSD", "EURCHF", "EURAUD", "EURCAD"]
    second = ["EURNZD", "GBPCHF", "GBPAUD", "GBPCAD", "AUDJPY", "XAUUSD", "XAGUSD"]
    third = ["NAS100", "US500", "US30", "DAX40", "UK100", "JPN225", "HK50"]

    first_record = load_group_market_data(state, "FIRST", first, "H1")
    second_record = load_group_market_data(state, "SECOND", second, "H1")
    third_record = load_group_market_data(state, "THIRD", third, "H1")

    assert first_record["requested_symbols"] == first[:10]
    assert second_record["requested_symbols"] == second[:10]
    assert third_record["requested_symbols"] == third[:10]
    assert first_record["loaded_symbols"] == first[:10]
    assert second_record["loaded_symbols"] == second[:10]
    assert third_record["loaded_symbols"] == third[:10]
    assert [len(call["symbols"]) for call in calls] == [10, 7, 7]
    assert all(call["stagger"] is False for call in calls)
    assert all(call["rounds"] == 2 for call in calls)
    assert all(call["scope"] == "LUNCH_CORE" for call in calls)
    assert all(call["provider"] == "FINNHUB" for call in calls)
    # Temporary speed controls must not leak into calculation state.
    assert "quota_safe_stagger_enabled_20260706" not in state
    assert "multi_symbol_fetch_rounds_20260706" not in state
    assert "settings_calculation_scope_20260625" not in state


def test_startup_health_never_promotes_twelve_fallback_to_active():
    from core.startup_lunch_orchestrator_20260704 import connector_health

    state = {
        "connector_mode": "twelve",  # legacy saved profile
        "finnhub_api_key": "f",
        "twelve_api_key": "t",
        "twelve_data_connected": True,
        "finnhub_connected": False,
    }
    health = connector_health(state, ttl_seconds=0)
    assert health["active_provider"] == "finnhub"
    assert health["fallback_provider"] == "twelve_data"
    assert health["actual_healthy_provider"] == "twelve_data"
    assert state["active_market_provider_20260705"] == "FINNHUB"
    assert state["fallback_market_provider_20260705"] == "TWELVE_DATA"
