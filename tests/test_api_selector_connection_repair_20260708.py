from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from core.app.refresh import _first_not_none, refresh_data
from core.connector_state_machine_20260621 import CONNECTED_WITH_FALLBACK, snapshot, succeed
from core.data.candle_repository import CandleRepository, normalize_frame
from core.data.market_data_orchestrator import (
    MarketDataOrchestrator,
    MarketDataResult,
    PROVIDER_PRIORITY,
    ProviderPermanentError,
    provider_interval_for,
)
from core.multi_symbol_load_manager_20260707 import (
    LOAD_RECORDS_KEY,
    load_group_market_data,
    reload_failed_symbols,
    selection_signature,
)
from core.normalized_multi_symbol_migration_20260707 import (
    GROUPS,
    load_current_selections,
    replace_current_selections,
)

SYMBOLS = [
    "EURUSD", "AUDUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP",
    "NZDUSD", "EURCHF", "EURAUD", "EURCAD", "EURNZD", "GBPCHF",
]


class _Quota:
    def reserve(self, **kwargs):
        return {"allowed": True, "request_id": "Q1"}

    def complete(self, *args, **kwargs):
        return None

    def release(self, *args, **kwargs):
        return None

    def record_429(self, *args, **kwargs):
        return None

    def backoff_seconds(self, attempt: int) -> float:
        return 0.0


def raw_frame(rows: int = 120, timeframe: str = "H4") -> pd.DataFrame:
    freq = "4h" if timeframe == "H4" else "h"
    times = pd.date_range("2026-01-01", periods=rows, freq=freq, tz="UTC")
    close = pd.Series([1.10 + i * 0.0001 for i in range(rows)], dtype=float)
    return pd.DataFrame({
        "timestamp": times,
        "open": close - 0.00005,
        "high": close + 0.0002,
        "low": close - 0.0002,
        "close": close,
    })


def validated_payload(symbol: str, timeframe: str = "H4", rows: int = 120, provider: str = "FINNHUB") -> dict[str, Any]:
    frame = normalize_frame(
        raw_frame(rows, timeframe), symbol=symbol, timeframe=timeframe,
        provider=provider, provider_symbol=MarketDataOrchestrator.provider_symbol(symbol, provider),
    )
    return {
        "ok": True,
        "symbol": symbol,
        "canonical_symbol": symbol,
        "timeframe": timeframe,
        "frame": frame,
        "provider": provider,
        "provider_symbol": MarketDataOrchestrator.provider_symbol(symbol, provider),
        "status": "LIVE_PRIMARY" if provider == "FINNHUB" else "LIVE_FALLBACK",
        "validation_status": "VALID",
        "latest_completed_candle": pd.Timestamp(frame["open_time"].max()).isoformat(),
        "attempts": [{"provider": provider, "ok": True}],
        "persisted": True,
    }


def failed_payload(symbol: str, timeframe: str = "H4", category: str = "TEMPORARY_PROVIDER_ERROR") -> dict[str, Any]:
    return {
        "ok": False,
        "symbol": symbol,
        "timeframe": timeframe,
        "frame": pd.DataFrame(),
        "provider": "NONE",
        "provider_symbol": symbol,
        "status": category,
        "message": f"{symbol} provider unavailable",
        "validation_status": "FAILED",
        "attempts": [{"provider": "FINNHUB", "ok": False, "category": category}],
    }


def patch_loader(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, outcomes: dict[str, dict[str, Any]]):
    from core.calculation import run_orchestrator
    from core.data import deployment_migrations_20260705 as migrations
    from core import multi_symbol_load_manager_20260707 as manager

    monkeypatch.setattr(migrations, "DEFAULT_DB_PATH", tmp_path / "selector.sqlite3")
    monkeypatch.setattr(manager, "_persist_load_audit", lambda record, state: None)

    def fake_prepare(state, *, run_id, selected_symbols, timeframe, progress_callback=None):
        results = {symbol: outcomes.get(symbol, validated_payload(symbol, timeframe)) for symbol in selected_symbols}
        return {"run_id": run_id, "results": results, "complete": all(v.get("ok") for v in results.values())}

    monkeypatch.setattr(run_orchestrator, "prepare_market_data_for_run", fake_prepare)


def test_01_nonempty_dataframe_is_never_boolean_evaluated() -> None:
    frame = pd.DataFrame({"x": [1]})
    assert _first_not_none(frame, {"fallback": True}) is frame


def test_02_empty_dataframe_triggers_provider_fallback(tmp_path: Path) -> None:
    calls: list[str] = []

    def finnhub(**kwargs):
        calls.append("FINNHUB")
        return pd.DataFrame()

    def twelve(**kwargs):
        calls.append("TWELVE_DATA")
        return raw_frame()

    orch = MarketDataOrchestrator(
        db_path=tmp_path / "fallback.sqlite3", quota_manager=_Quota(),
        adapters={"FINNHUB": finnhub, "TWELVE_DATA": twelve},
    )
    result = orch.fetch(
        symbol="EURUSD", timeframe="H4", bars=120, force_live=True,
        state={"finnhub_api_key": "f", "twelve_api_key": "t"},
    )
    assert result.ok and result.provider == "TWELVE_DATA"
    assert calls == ["FINNHUB", "TWELVE_DATA"]


def test_03_finnhub_failure_continues_to_twelve_data(tmp_path: Path) -> None:
    def finnhub(**kwargs):
        raise ProviderPermanentError("Finnhub candle endpoint restricted")

    orch = MarketDataOrchestrator(
        db_path=tmp_path / "restricted.sqlite3", quota_manager=_Quota(),
        adapters={"FINNHUB": finnhub, "TWELVE_DATA": lambda **kwargs: raw_frame()},
    )
    result = orch.fetch(
        symbol="EURUSD", timeframe="H4", bars=120, force_live=True,
        state={"finnhub_api_key": "f", "twelve_api_key": "t"},
    )
    assert result.ok and result.provider == "TWELVE_DATA"
    assert [a["provider"] for a in result.attempts[:2]] == ["FINNHUB", "TWELVE_DATA"]


def test_04_valid_twelve_data_is_connected_with_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeOrchestrator:
        def fetch(self, **kwargs):
            payload = validated_payload("EURUSD", "H4", provider="TWELVE_DATA")
            return MarketDataResult(
                ok=True, symbol="EURUSD", timeframe="H4", frame=payload["frame"],
                provider="TWELVE_DATA", provider_symbol="EUR/USD", status="LIVE_FALLBACK",
                message="Twelve Data supplied validated candles", latest_completed_candle=payload["latest_completed_candle"],
                fallback_provider="TWELVE_DATA",
                attempts=[{"provider": "FINNHUB", "ok": False, "category": "PERMANENT_CLIENT_ERROR", "message": "restricted"},
                          {"provider": "TWELVE_DATA", "ok": True}],
                data_age_seconds=0.0, data_quality_score=100.0, validation_status="VALID",
            )

    import core.data.market_data_orchestrator as module
    monkeypatch.setattr(module, "MarketDataOrchestrator", FakeOrchestrator)
    state: dict[str, Any] = {
        "canonical_result_20260617": pd.DataFrame({"preserve": [1]}),
        "symbol": "EURUSD", "timeframe": "H4", "connector_bars": 600,
    }
    result = refresh_data(state)
    assert result["ok"] is True
    assert result["connection_state"] == CONNECTED_WITH_FALLBACK
    assert state["market_connection_outcome_20260708"] == CONNECTED_WITH_FALLBACK
    assert state["actual_market_provider_used_20260708"] == "TWELVE_DATA"


def test_05_one_symbol_failure_does_not_fail_batch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    outcomes = {"USDCAD": failed_payload("USDCAD")}
    patch_loader(monkeypatch, tmp_path, outcomes)
    record = load_group_market_data({}, "SECOND", ["AUDUSD", "USDCAD", "USDCHF"], "H4")
    assert record["loaded_symbols"] == ["AUDUSD", "USDCHF"]
    assert record["failed_symbols"] == ["USDCAD"]
    assert record["load_status"] == "PARTIAL"


@pytest.mark.parametrize(
    ("group", "symbols"),
    [
        ("FIRST", ["NZDUSD", "EURCHF", "EURAUD", "EURCAD", "EURNZD", "GBPCHF"]),
        ("SECOND", ["AUDUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP"]),
        ("THIRD", ["EURUSD", "NZDUSD", "EURCHF", "EURAUD", "EURCAD", "EURNZD"]),
    ],
)
def test_06_to_08_each_selector_loads_exact_visible_symbols(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, group: str, symbols: list[str]
) -> None:
    patch_loader(monkeypatch, tmp_path, {})
    record = load_group_market_data({}, group, symbols, "H4")
    assert record["requested_symbols"] == symbols
    assert record["loaded_symbols"] == symbols
    assert list(record["report"]["results"]) == symbols


def test_09_deselected_symbol_is_not_loaded(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    seen: list[list[str]] = []
    from core.calculation import run_orchestrator
    from core.data import deployment_migrations_20260705 as migrations
    from core import multi_symbol_load_manager_20260707 as manager
    monkeypatch.setattr(migrations, "DEFAULT_DB_PATH", tmp_path / "deselect.sqlite3")
    monkeypatch.setattr(manager, "_persist_load_audit", lambda record, state: None)

    def fake_prepare(state, *, run_id, selected_symbols, timeframe, progress_callback=None):
        seen.append(list(selected_symbols))
        return {"results": {s: validated_payload(s, timeframe) for s in selected_symbols}}

    monkeypatch.setattr(run_orchestrator, "prepare_market_data_for_run", fake_prepare)
    state: dict[str, Any] = {}
    load_group_market_data(state, "SECOND", ["AUDUSD", "USDCAD"], "H4")
    load_group_market_data(state, "SECOND", ["AUDUSD"], "H4")
    assert seen[-1] == ["AUDUSD"]


def test_10_symbol_order_is_preserved(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    symbols = ["GBPJPY", "AUDUSD", "EURGBP", "USDCHF"]
    patch_loader(monkeypatch, tmp_path, {})
    record = load_group_market_data({}, "SECOND", symbols, "H4")
    assert record["requested_symbols"] == symbols
    assert record["loaded_symbols"] == symbols


def test_11_h4_maps_correctly_for_every_provider() -> None:
    assert provider_interval_for("H4", "FINNHUB") == "60"
    assert provider_interval_for("H4", "TWELVE_DATA") == "1h"
    assert provider_interval_for("H4", "MT5") == "H4"
    assert provider_interval_for("H4", "ALPHA_VANTAGE") == "60min"
    assert provider_interval_for("H4", "LOCAL_VALID_CACHE") == "H4"


def test_12_canonical_symbols_map_for_every_provider() -> None:
    for symbol in SYMBOLS:
        assert MarketDataOrchestrator.provider_symbol(symbol, "FINNHUB") == f"OANDA:{symbol[:3]}_{symbol[3:]}"
        assert MarketDataOrchestrator.provider_symbol(symbol, "TWELVE_DATA") == f"{symbol[:3]}/{symbol[3:]}"
        assert MarketDataOrchestrator.provider_symbol(symbol, "MT5") == symbol
        assert MarketDataOrchestrator.provider_symbol(symbol, "ALPHA_VANTAGE") == symbol


def test_13_successful_rows_persist_under_exact_symbol_and_timeframe(tmp_path: Path) -> None:
    repository = CandleRepository(tmp_path / "candles.sqlite3")
    frame = normalize_frame(raw_frame(120, "H4"), symbol="EURCAD", timeframe="H4", provider="TWELVE_DATA", provider_symbol="EUR/CAD")
    repository.upsert(frame, run_id="PERSIST")
    assert len(repository.load("EURCAD", "H4", limit=200)) == 120
    assert repository.load("EURUSD", "H4", limit=200).empty
    assert repository.load("EURCAD", "H1", limit=200).empty


def test_14_reload_failed_retries_only_allowed_failed_statuses(monkeypatch: pytest.MonkeyPatch) -> None:
    import core.multi_symbol_load_manager_20260707 as manager
    symbols = ["AUDUSD", "USDCAD", "USDCHF"]
    state: dict[str, Any] = {
        LOAD_RECORDS_KEY: {
            "SECOND": {
                "selection_signature": selection_signature(symbols, "H4"),
                "timeframe": "H4", "requested_symbols": symbols,
                "loaded_symbols": ["AUDUSD"], "failed_symbols": ["USDCAD", "USDCHF"],
                "validations": {
                    "USDCAD": {"failure_category": "TEMPORARY_ERROR"},
                    "USDCHF": {"failure_category": "TIMEFRAME_NOT_SUPPORTED"},
                },
                "status": "PARTIAL_READY",
            }
        }
    }
    captured: dict[str, Any] = {}

    def fake_load(state, group, symbols, timeframe, *, progress_callback=None, retry_symbols=None):
        captured["retry"] = list(retry_symbols)
        return {"retried_symbols": list(retry_symbols)}

    monkeypatch.setattr(manager, "load_group_market_data", fake_load)
    reload_failed_symbols(state, "SECOND", symbols, "H4")
    assert captured["retry"] == ["USDCAD"]


def test_15_cached_valid_dataframe_loads_without_boolean_error(tmp_path: Path) -> None:
    from core.runtime_selection_20260705 import latest_completed_candle
    end = pd.Timestamp(latest_completed_candle(timeframe="H4"))
    times = pd.date_range(end=end, periods=120, freq="4h")
    raw = raw_frame(120, "H4")
    raw["timestamp"] = times
    orch = MarketDataOrchestrator(db_path=tmp_path / "cache.sqlite3", quota_manager=_Quota())
    normalized = normalize_frame(raw, symbol="EURUSD", timeframe="H4", provider="TWELVE_DATA", provider_symbol="EUR/USD")
    orch.repository.upsert(normalized, run_id="CACHE")
    result = orch.fetch(symbol="EURUSD", timeframe="H4", bars=120, state={})
    assert result.ok and len(result.frame) >= 100


def test_16_cached_empty_dataframe_does_not_block_fresh_request(tmp_path: Path) -> None:
    called = {"value": False}

    def finnhub(**kwargs):
        called["value"] = True
        return raw_frame()

    orch = MarketDataOrchestrator(
        db_path=tmp_path / "fresh.sqlite3", quota_manager=_Quota(),
        adapters={"FINNHUB": finnhub},
    )
    result = orch.fetch(
        symbol="EURUSD", timeframe="H4", bars=120, force_live=False,
        state={"finnhub_api_key": "f"},
    )
    assert called["value"] and result.ok


def test_17_summary_counts_are_consistent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    patch_loader(monkeypatch, tmp_path, {"USDCAD": failed_payload("USDCAD")})
    record = load_group_market_data({}, "SECOND", ["AUDUSD", "USDCAD", "USDCHF"], "H4")
    assert record["selected_count"] == record["loaded_count"] + record["failed_count"]
    assert len(record["requested_symbols"]) == len(record["loaded_symbols"]) + len(record["failed_symbols"])


def test_18_selector_state_is_isolated(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    patch_loader(monkeypatch, tmp_path, {})
    state: dict[str, Any] = {}
    load_group_market_data(state, "FIRST", ["NZDUSD", "EURCHF"], "H4")
    load_group_market_data(state, "SECOND", ["AUDUSD", "USDCAD"], "H4")
    load_group_market_data(state, "THIRD", ["EURJPY", "GBPJPY"], "H4")
    records = state[LOAD_RECORDS_KEY]
    assert records["FIRST"]["requested_symbols"] == ["NZDUSD", "EURCHF"]
    assert records["SECOND"]["requested_symbols"] == ["AUDUSD", "USDCAD"]
    assert records["THIRD"]["requested_symbols"] == ["EURJPY", "GBPJPY"]


def test_19_successful_fallback_never_sets_error_state() -> None:
    state: dict[str, Any] = {}
    succeed(state, "market_connector_20260621", "fallback ready", connection_state=CONNECTED_WITH_FALLBACK)
    assert snapshot(state, "market_connector_20260621")["state"] == CONNECTED_WITH_FALLBACK


def test_20_failed_provider_has_useful_category(tmp_path: Path) -> None:
    def fail(**kwargs):
        raise ProviderPermanentError("candle endpoint unavailable")

    orch = MarketDataOrchestrator(
        db_path=tmp_path / "fail.sqlite3", quota_manager=_Quota(),
        adapters={"FINNHUB": fail, "TWELVE_DATA": fail, "MT5": fail, "ALPHA_VANTAGE": fail},
    )
    result = orch.fetch(
        symbol="EURUSD", timeframe="H4", bars=120, force_live=True,
        state={"finnhub_api_key": "f", "twelve_api_key": "t", "alpha_vantage_api_key": "a"},
    )
    assert result.ok is False
    assert result.attempts
    assert all(str(item.get("category") or "").strip() for item in result.attempts)
    assert "Provider route:" in result.message


def test_21_normalized_selector_persistence_keeps_first_twelve(tmp_path: Path) -> None:
    first = [f"S{i:02d}USD" for i in range(12)]
    replace_current_selections(tmp_path / "selectors.sqlite3", {"first": first, "second": [], "third": []}, "H4")
    restored = load_current_selections(tmp_path / "selectors.sqlite3")
    assert restored is not None
    assert restored["first"] == first
    assert GROUPS["first"][2] == 12


def test_22_provider_order_matches_settings_contract() -> None:
    assert PROVIDER_PRIORITY == ("FINNHUB", "TWELVE_DATA", "MT5", "ALPHA_VANTAGE", "LOCAL_VALID_CACHE")


def test_23_three_selector_widget_and_button_keys_are_isolated() -> None:
    from ui.multi_symbol_settings_20260701 import _group_defs
    definitions, _ = _group_defs()
    widget_keys = [definitions[group]["widget_key"] for group in ("FIRST", "SECOND", "THIRD")]
    state_keys = [definitions[group]["state_key"] for group in ("FIRST", "SECOND", "THIRD")]
    pending_keys = [definitions[group]["pending_key"] for group in ("FIRST", "SECOND", "THIRD")]
    assert len(set(widget_keys)) == 3
    assert len(set(state_keys)) == 3
    assert len(set(pending_keys)) == 3
    source = Path("ui/multi_symbol_settings_20260701.py").read_text()
    for group in ("first", "second", "third"):
        assert f"multi_symbol_{{group_name.lower()}}_load_selected_20260707" in source
        assert f"multi_symbol_{{group_name.lower()}}_reload_failed_20260707" in source


def test_24_main_feed_normalization_accepts_missing_volume_and_rejects_bad_ohlc() -> None:
    valid = raw_frame(4, "H4")
    normalized = normalize_frame(
        valid, symbol="EURUSD", timeframe="H4", provider="FINNHUB",
        provider_symbol="OANDA:EUR_USD",
    )
    assert len(normalized) == 4
    assert "volume" in normalized.columns
    assert normalized["volume"].isna().all()

    bad = valid.copy()
    bad.loc[0, "high"] = bad.loc[0, "low"] - 1.0
    rejected = normalize_frame(
        bad, symbol="EURUSD", timeframe="H4", provider="FINNHUB",
        provider_symbol="OANDA:EUR_USD",
    )
    assert (rejected["validation_status"] == "INVALID_OHLC_RELATION").any()
