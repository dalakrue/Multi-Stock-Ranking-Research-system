from __future__ import annotations

import pandas as pd

from core.multi_symbol_api_runtime_20260702 import (
    build_request_key, classify_provider_failure, connection_profile_reusable,
    prepare_symbol_market_data,
)


def _state(signature="SIG-A"):
    return {
        "market_connector_saved_profile_20260702": {"signature": signature, "mode": "twelve", "timeframe": "H1", "bars": 600},
        "connector_mode": "twelve", "timeframe": "H1", "connector_bars": 600,
        "canonical_decision_result_20260617": {
            "symbol": "EURUSD", "completed_broker_candle": "2026-07-01T10:00:00Z"
        },
    }


def test_multi_symbol_api_exact_candle_dedup_and_force_refresh(monkeypatch):
    calls = []
    frame = pd.DataFrame({"time": pd.to_datetime(["2026-07-01T10:00:00Z"]), "open": [1.0], "high": [1.1], "low": [0.9], "close": [1.05]})

    def fake_connect(**kwargs):
        calls.append({k: v for k, v in kwargs.items() if k not in {"api_key", "bridge_token", "bridge_url"}})
        return frame.copy(), True, "TWELVE", "ok"

    monkeypatch.setattr("core.data_connectors.manual_connect", fake_connect)
    state = _state()
    first = prepare_symbol_market_data(state, "USDJPY")
    second = prepare_symbol_market_data(state, "USDJPY")
    forced = prepare_symbol_market_data(state, "USDJPY", force=True)
    assert first["status"] == "FETCHED"
    assert second["status"] == "EXACT_CANDLE_CACHE_HIT"
    assert second["requests"] == 0
    assert forced["status"] == "FETCHED"
    assert len(calls) == 2
    assert "api_key" not in first and "bridge_token" not in first


def test_profile_change_invalidates_reuse_and_request_key():
    assert connection_profile_reusable({"signature": "A"}, {"signature": "A"}) is True
    assert connection_profile_reusable({"signature": "A"}, {"signature": "B"}) is False
    one = build_request_key(provider="twelve", canonical_symbol="US500", provider_alias="SPX", timeframe="H1", candle_count=600, completed_h1_candle="2026-07-01T10:00:00Z", profile_fingerprint="A")
    two = build_request_key(provider="twelve", canonical_symbol="US500", provider_alias="SPX", timeframe="H1", candle_count=600, completed_h1_candle="2026-07-01T10:00:00Z", profile_fingerprint="B")
    assert one != two


def test_auth_invalid_symbol_and_quota_are_not_retryable():
    assert classify_provider_failure("401 invalid API key")["retryable"] is False
    assert classify_provider_failure("invalid symbol")["retryable"] is False
    assert classify_provider_failure("quota exceeded")["retryable"] is False
    assert classify_provider_failure("503 temporary failure")["retryable"] is True
