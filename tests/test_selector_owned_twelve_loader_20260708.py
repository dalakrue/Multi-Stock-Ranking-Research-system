from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core.multi_symbol_load_manager_20260707 as mgr


def _frame(symbol: str, rows: int = 32) -> pd.DataFrame:
    stamps = pd.date_range("2026-07-01", periods=rows, freq="4h", tz="UTC")
    base = pd.Series(range(rows), dtype=float) / 10000.0 + 1.10
    return pd.DataFrame({
        "open_time": stamps,
        "time": stamps,
        "open": base,
        "high": base + 0.0005,
        "low": base - 0.0005,
        "close": base + 0.0001,
        "volume": 1000.0,
        "symbol": symbol,
        "timeframe": "H4",
        "provider": "TWELVE_DATA_KEY_POOL",
        "provider_key_alias": "",
        "validation_status": "VALID",
    })


def _payload(symbol: str, key_alias: str, *, ok: bool, failure: str = "circuit") -> dict[str, Any]:
    if ok:
        frame = _frame(symbol)
        return {
            "ok": True,
            "symbol": symbol,
            "timeframe": "H4",
            "provider": "TWELVE_DATA_KEY_POOL",
            "provider_symbol": symbol,
            "frame": frame,
            "status": "COMPLETED",
            "message": "validated",
            "validation_status": "VALID",
            "actual_key_name": key_alias,
            "provider_key_alias": key_alias,
            "attempts": [{
                "provider": "TWELVE_DATA_KEY_POOL",
                "ok": True,
                "request_sent": True,
                "actual_key_name": key_alias,
                "provider_key_alias": key_alias,
            }],
        }
    if failure == "quota":
        return {
            "ok": False,
            "symbol": symbol,
            "timeframe": "H4",
            "provider": "TWELVE_DATA_KEY_POOL",
            "status": f"{key_alias}_QUOTA_COOLDOWN",
            "message": f"{key_alias}_QUOTA_COOLDOWN",
            "assigned_key": key_alias,
            "attempts": [{
                "provider": "TWELVE_DATA_KEY_POOL",
                "ok": False,
                "request_sent": False,
                "quota_blocked": True,
                "category": "RATE_LIMITED",
                "message": f"{key_alias}_QUOTA_COOLDOWN",
            }],
        }
    return {
        "ok": False,
        "symbol": symbol,
        "timeframe": "H4",
        "provider": "TWELVE_DATA_KEY_POOL",
        "status": "RUN_CIRCUIT_OPEN",
        "message": "Provider skipped by foreground symbol-level circuit breaker after recent hard failure.",
        "attempts": [{
            "provider": "TWELVE_DATA_KEY_POOL",
            "ok": False,
            "request_sent": False,
            "category": "RUN_CIRCUIT_OPEN",
            "message": "Provider skipped by foreground symbol-level circuit breaker after recent hard failure.",
        }],
    }


def _fake_record(state: dict, group: str, symbols: list[str], key_alias: str, ok_symbols: set[str], *, failure: str = "circuit", retried: list[str] | None = None) -> dict[str, Any]:
    validations: dict[str, Any] = {}
    results: dict[str, Any] = {}
    loaded: list[str] = []
    failed: list[str] = []
    for symbol in symbols:
        ok = symbol in ok_symbols
        payload = _payload(symbol, key_alias, ok=ok, failure=failure)
        validation = mgr._validate_result(payload, symbol=symbol, timeframe="H4", required_rows=600)
        validation.setdefault("assigned_key", key_alias)
        validations[symbol] = validation
        if ok:
            results[symbol] = payload
            loaded.append(symbol)
        else:
            failed.append(symbol)
    record = {
        "group": group,
        "scope": mgr.scope_for_group(group),
        "load_id": f"FAKE-{group}-{len(state.get('calls', []))}",
        "loaded_at": "2026-07-08T00:00:00+00:00",
        "timeframe": "H4",
        "selection_signature": mgr.selection_signature(symbols, "H4"),
        "requested_symbols": list(symbols),
        "loaded_symbols": loaded,
        "failed_symbols": failed,
        "required_candles": 600,
        "minimum_calculation_candles": 25,
        "validations": validations,
        "retried_symbols": list(retried or []),
        "status": "FULL_READY" if loaded and not failed else "PARTIAL_READY" if loaded else "FAILED",
        "report": {
            "run_id": "FAKE",
            "timeframe": "H4",
            "results": results,
            "requested_symbols": list(symbols),
            "loaded_symbols": loaded,
            "unresolved_symbols": failed,
        },
    }
    records = state.get(mgr.LOAD_RECORDS_KEY, {})
    records[group] = record
    state[mgr.LOAD_RECORDS_KEY] = records
    return record


def test_selector_owned_load_all_keeps_key_1_on_selector_1_and_key_2_on_selector_2(monkeypatch):
    s1 = ["AUDUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP"]
    s2 = ["NZDUSD", "EURCHF", "EURAUD", "EURCAD", "EURNZD", "EURUSD"]
    state: dict[str, Any] = {}
    calls: list[dict[str, Any]] = []

    def fake_load_group(state_arg, group, symbols, timeframe, *, progress_callback=None, retry_symbols=None, force_reload=False):
        key_alias = state_arg.get(mgr.ASSIGNED_TWELVE_KEY_STATE_KEY)
        calls.append({"group": group, "symbols": list(symbols), "key": key_alias, "retry_symbols": retry_symbols, "force": force_reload})
        ok_symbols = set(list(s1 + s2)[:7])
        return _fake_record(state_arg, str(group), list(symbols), str(key_alias), ok_symbols)

    monkeypatch.setattr(mgr, "load_group_market_data", fake_load_group)
    status = mgr.load_all_selectors_safely(state, {"FIRST": s1, "SECOND": s2, "THIRD": []}, "H4")

    assert [c["group"] for c in calls] == ["FIRST", "SECOND"]
    assert calls[0]["key"] == "TWELVE_KEY_1"
    assert calls[1]["key"] == "TWELVE_KEY_2"
    assert len(status["status_rows"]) == 12
    assert status["loaded_now_count"] == 7
    assert len(status["failed_symbols"]) == 5
    first_providers = {row["Actual provider used"] for row in status["status_rows"][:6] if row["Load Final State"] == "VALIDATED"}
    second_providers = {row["Actual provider used"] for row in status["status_rows"][6:] if row["Load Final State"] == "VALIDATED"}
    assert first_providers == {"TWELVE_KEY_1"}
    assert second_providers <= {"TWELVE_KEY_2"}


def test_reload_failed_only_preserves_ready_rows_and_retries_only_failed(monkeypatch):
    s1 = ["AUDUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP"]
    state: dict[str, Any] = {}
    _fake_record(state, "FIRST", s1, "TWELVE_KEY_1", set(s1[:4]))
    calls: list[dict[str, Any]] = []

    def fake_load_group(state_arg, group, symbols, timeframe, *, progress_callback=None, retry_symbols=None, force_reload=False):
        calls.append({"symbols": list(symbols), "retry_symbols": list(retry_symbols or []), "force": force_reload})
        # Retry succeeds only for the two previously failed rows; existing READY rows remain valid.
        return _fake_record(state_arg, str(group), list(symbols), "TWELVE_KEY_1", set(symbols), retried=list(retry_symbols or []))

    monkeypatch.setattr(mgr, "load_group_market_data", fake_load_group)
    monkeypatch.setattr(mgr, "clear_circuit_breaker_for_symbols", lambda symbols, timeframe, provider=None: {"cleared": len(symbols), "symbols": list(symbols)})

    mgr.load_selector_with_assigned_key(state, "FIRST", s1, "H4", "TWELVE_KEY_1", retry_failed_only=True)
    assert calls == [{"symbols": s1, "retry_symbols": s1[4:], "force": True}]
    status = mgr.merge_selector_load_results(state, {"FIRST": s1, "SECOND": [], "THIRD": []}, "H4")
    assert status["loaded_now_count"] == 6
    assert status["failed_symbols"] == []
    assert all(row["Load Final State"] == "VALIDATED" for row in status["status_rows"])


def test_circuit_skipped_rows_show_none_and_request_not_attempted():
    symbols = ["AUDUSD", "USDCAD"]
    state: dict[str, Any] = {}
    _fake_record(state, "FIRST", symbols, "TWELVE_KEY_1", {"AUDUSD"}, failure="circuit")
    status = mgr.merge_selector_load_results(state, {"FIRST": symbols, "SECOND": [], "THIRD": []}, "H4")
    failed_row = next(row for row in status["status_rows"] if row["Symbol"] == "USDCAD")
    assert failed_row["Load Status"] == "RUN_CIRCUIT_OPEN"
    assert failed_row["Actual provider used"] == "NONE"
    assert failed_row["API request attempted after click"] is False
    assert failed_row["Skipped by circuit breaker"] is True


def test_quota_rows_show_quota_cooldown_and_assigned_key_not_generic_none():
    symbols = ["AUDUSD", "USDCAD"]
    state: dict[str, Any] = {}
    _fake_record(state, "SECOND", symbols, "TWELVE_KEY_2", {"AUDUSD"}, failure="quota")
    status = mgr.merge_selector_load_results(state, {"FIRST": [], "SECOND": symbols, "THIRD": []}, "H4")
    failed_row = next(row for row in status["status_rows"] if row["Symbol"] == "USDCAD")
    assert failed_row["Load Status"] == "QUOTA_COOLDOWN"
    assert failed_row["Actual provider used"] == "TWELVE_KEY_2"
    assert failed_row["Assigned key"] == "TWELVE_KEY_2"
    assert failed_row["API request attempted after click"] is False
    assert failed_row["Skipped by quota cooldown"] is True


def test_manual_reload_with_real_request_marks_request_attempted_true(monkeypatch):
    symbols = ["AUDUSD", "USDCAD"]
    state: dict[str, Any] = {}
    _fake_record(state, "FIRST", symbols, "TWELVE_KEY_1", {"AUDUSD"}, failure="circuit")

    def fake_load_group(state_arg, group, symbols, timeframe, *, progress_callback=None, retry_symbols=None, force_reload=False):
        assert retry_symbols == ["USDCAD"]
        return _fake_record(state_arg, str(group), list(symbols), "TWELVE_KEY_1", set(symbols), retried=list(retry_symbols or []))

    monkeypatch.setattr(mgr, "load_group_market_data", fake_load_group)
    monkeypatch.setattr(mgr, "clear_circuit_breaker_for_symbols", lambda symbols, timeframe, provider=None: {"cleared": len(symbols), "symbols": list(symbols)})

    mgr.load_selector_with_assigned_key(state, "FIRST", symbols, "H4", "TWELVE_KEY_1", retry_failed_only=True)
    status = mgr.merge_selector_load_results(state, {"FIRST": symbols, "SECOND": [], "THIRD": []}, "H4")
    retried_row = next(row for row in status["status_rows"] if row["Symbol"] == "USDCAD")
    assert retried_row["Load Status"] == "TWELVE_KEY_1_SUCCESS"
    assert retried_row["API request attempted after click"] is True
