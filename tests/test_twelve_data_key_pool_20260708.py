from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.twelve_data_key_pool import TwelveDataKeyPool
from core.data.market_data_orchestrator import MarketDataOrchestrator, provider_priority_for_state
from core.multi_symbol_load_manager_20260707 import canonical_universe_from_groups, _validate_result


def _state() -> dict:
    return {
        "twelve_api_key_1": "key-one-ABCD",
        "twelve_api_key_2": "key-two-WXYZ",
        "enable_twelve_multi_key_loading": True,
        "twelve_data_per_key_minute_limit": 2,
    }


def _frame(rows: int = 40) -> pd.DataFrame:
    end = pd.Timestamp.now(tz="UTC").floor("4h") - pd.Timedelta(hours=4)
    times = pd.date_range(end=end, periods=rows, freq="4h")
    return pd.DataFrame({
        "time": times,
        "open": [1.10 + i * 0.0001 for i in range(rows)],
        "high": [1.11 + i * 0.0001 for i in range(rows)],
        "low": [1.09 + i * 0.0001 for i in range(rows)],
        "close": [1.105 + i * 0.0001 for i in range(rows)],
        "volume": [100 + i for i in range(rows)],
    })




class _SessionStateLike:
    """Small Streamlit SessionStateProxy stand-in: mutable but not MutableMapping."""
    def __init__(self, data: dict):
        self._data = dict(data)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __setitem__(self, key, value):
        self._data[key] = value

    def __getitem__(self, key):
        return self._data[key]


def test_session_state_like_parallel_pools_share_runtime_and_use_both_keys() -> None:
    state = _SessionStateLike({
        "twelve_api_key_1": "session-key-one-1111",
        "twelve_api_key_2": "session-key-two-2222",
        "enable_twelve_multi_key_loading": True,
        "twelve_data_per_key_minute_limit": 8,
    })
    leases = [
        TwelveDataKeyPool.from_state(state).reserve_key(symbol=f"EUR{i}USD", timeframe="H4")
        for i in range(4)
    ]
    assert all(lease is not None for lease in leases)
    assert {lease.alias for lease in leases if lease is not None} == {"TWELVE_KEY_1", "TWELVE_KEY_2"}
    snapshot = TwelveDataKeyPool.from_state(state).status_snapshot()
    assert snapshot["TWELVE_KEY_1"]["used_credits"] == 2
    assert snapshot["TWELVE_KEY_2"]["used_credits"] == 2


def test_both_twelve_keys_are_independent_workers() -> None:
    state = _state()
    pool = TwelveDataKeyPool.from_state(state)
    first = pool.reserve_key(symbol="EURUSD", timeframe="H4")
    second = pool.reserve_key(symbol="GBPUSD", timeframe="H4")
    third = pool.reserve_key(symbol="USDJPY", timeframe="H4")
    assert first is not None and second is not None and third is not None
    assert {first.alias, second.alias, third.alias} == {"TWELVE_KEY_1", "TWELVE_KEY_2"}
    assert first.masked_key.endswith("ABCD")
    assert second.masked_key.endswith("WXYZ") or third.masked_key.endswith("WXYZ")


def test_key_1_limit_or_429_does_not_disable_key_2() -> None:
    state = _state()
    pool = TwelveDataKeyPool.from_state(state)
    pool.mark_429("TWELVE_KEY_1", retry_after=60, reason="KEY_1_RATE_LIMIT")
    lease = pool.reserve_key(symbol="EURUSD", timeframe="H4")
    assert lease is not None
    assert lease.alias == "TWELVE_KEY_2"


def test_both_keys_limited_returns_none_for_pool() -> None:
    state = _state()
    pool = TwelveDataKeyPool.from_state(state)
    pool.mark_429("TWELVE_KEY_1", retry_after=60, reason="KEY_1_RATE_LIMIT")
    pool.mark_429("TWELVE_KEY_2", retry_after=60, reason="KEY_2_RATE_LIMIT")
    assert pool.reserve_key(symbol="EURUSD", timeframe="H4") is None
    snap = pool.status_snapshot()
    assert snap["TWELVE_KEY_1"]["cooldown_reset_time"]
    assert snap["TWELVE_KEY_2"]["cooldown_reset_time"]


def test_provider_order_is_twelve_pool_then_finnhub_then_cache() -> None:
    order = provider_priority_for_state({"connector_mode": "twelve_pool"})
    assert order[:3] == ("TWELVE_DATA_KEY_POOL", "FINNHUB", "LOCAL_VALID_CACHE")


def test_empty_twelve_response_is_failure_and_finnhub_fallback_can_succeed(tmp_path: Path) -> None:
    def twelve(**kwargs):
        return pd.DataFrame(), False, "EMPTY_CANDLES"

    def finnhub(**kwargs):
        return _frame(rows=40), True, "Finnhub valid candles"

    router = MarketDataOrchestrator(
        db_path=tmp_path / "pool.sqlite3",
        adapters={"TWELVE_DATA_KEY_POOL": twelve, "FINNHUB": finnhub},
    )
    result = router.fetch(
        symbol="EURUSD", timeframe="H4", state={**_state(), "finnhub_api_key": "fh"},
        bars=40, run_id="POOL", force_live=True,
    )
    assert result.ok is True
    assert result.provider == "FINNHUB"
    assert any(a["provider"] == "TWELVE_DATA_KEY_POOL" and not a["ok"] for a in result.attempts)
    assert any(a["provider"] == "FINNHUB" and a["ok"] for a in result.attempts)


def test_canonical_universe_dedupes_three_selectors_to_12() -> None:
    groups = {
        "FIRST": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURUSD"],
        "SECOND": ["USDCAD", "USDCHF", "EURJPY", "GBPJPY"],
        "THIRD": ["EURGBP", "NZDUSD", "EURCHF", "EURAUD", "EURCAD", "EURNZD"],
    }
    assert canonical_universe_from_groups(groups, limit=12) == [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF",
        "EURJPY", "GBPJPY", "EURGBP", "NZDUSD", "EURCHF", "EURAUD",
    ]


def test_field10_validation_rejects_empty_candle_response() -> None:
    payload = {
        "ok": True,
        "symbol": "EURUSD",
        "timeframe": "H4",
        "provider": "TWELVE_DATA_KEY_POOL",
        "frame": pd.DataFrame(),
        "attempts": [{"provider": "TWELVE_DATA_KEY_POOL", "ok": False, "message": "EMPTY_CANDLES"}],
    }
    result = _validate_result(payload, symbol="EURUSD", timeframe="H4", required_rows=600)
    assert result["ok"] is False
    assert result["failure_code"] in {"NO_GENUINE_CANDLES", "BELOW_MODULE_MINIMUM", "VALIDATION_WARNING"}
    assert result["provider"] == "TWELVE_DATA_KEY_POOL"
