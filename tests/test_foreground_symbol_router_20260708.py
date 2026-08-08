from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.data.deployment_migrations_20260705 import migrate_deployment_schema
from core.data.market_data_orchestrator import MarketDataOrchestrator, provider_priority_for_state
from core.data.symbol_level_provider_registry_20260708 import SymbolLevelProviderRegistry
from core.multi_symbol_load_manager_20260707 import (
    CANONICAL_GROUP,
    LOAD_RECORDS_KEY,
    loaded_canonical_status,
    normalize_symbols,
)


def _frame(symbol: str = "EURUSD", rows: int = 40) -> pd.DataFrame:
    end = pd.Timestamp.now(tz="UTC").floor("4h") - pd.Timedelta(hours=4)
    times = pd.date_range(end=end, periods=rows, freq="4h")
    return pd.DataFrame(
        {
            "time": times,
            "open": [1.10 + i * 0.0001 for i in range(rows)],
            "high": [1.11 + i * 0.0001 for i in range(rows)],
            "low": [1.09 + i * 0.0001 for i in range(rows)],
            "close": [1.105 + i * 0.0001 for i in range(rows)],
            "volume": [100 + i for i in range(rows)],
        }
    )


def test_provider_order_is_cache_twelve_pool_finnhub_cache_policy() -> None:
    order = provider_priority_for_state({"connector_mode": "twelve_data_fallback"})
    assert order[:3] == ("TWELVE_DATA_KEY_POOL", "FINNHUB", "LOCAL_VALID_CACHE")


def test_twelve_empty_candles_falls_back_to_finnhub(tmp_path: Path) -> None:
    db = tmp_path / "router.sqlite3"

    def twelve(**kwargs):
        return pd.DataFrame(), False, "Twelve key pool auth ok but EMPTY_CANDLES"

    def finnhub(**kwargs):
        return _frame(rows=40), True, "Finnhub fallback valid candles"

    router = MarketDataOrchestrator(
        db_path=db,
        adapters={"TWELVE_DATA_KEY_POOL": twelve, "FINNHUB": finnhub},
    )
    result = router.fetch(
        symbol="EURUSD",
        timeframe="H4",
        state={"twelve_api_key_1": "twelve", "finnhub_api_key": "finnhub"},
        bars=40,
        run_id="R1",
        force_live=True,
    )
    assert result.ok is True
    assert result.provider == "FINNHUB"
    assert any(a["provider"] == "TWELVE_DATA_KEY_POOL" and not a["ok"] for a in result.attempts)
    assert any(a["provider"] == "FINNHUB" and a["ok"] for a in result.attempts)


def test_valid_local_cache_avoids_live_api(tmp_path: Path) -> None:
    db = tmp_path / "cache.sqlite3"
    router = MarketDataOrchestrator(db_path=db)
    normalized = router.repository.upsert(
        __import__("core.data.candle_repository", fromlist=["normalize_frame"]).normalize_frame(
            _frame(rows=40), symbol="EURUSD", timeframe="H4", provider="TWELVE_DATA_KEY_POOL", provider_symbol="EURUSD"
        ),
        run_id="seed",
    )
    assert normalized["inserted"] > 0

    def should_not_call(**kwargs):  # pragma: no cover - failure path
        raise AssertionError("live provider should not be called when exact cache is valid")

    router = MarketDataOrchestrator(
        db_path=db,
        adapters={"TWELVE_DATA_KEY_POOL": should_not_call, "FINNHUB": should_not_call},
    )
    result = router.fetch(symbol="EURUSD", timeframe="H4", state={}, bars=25, run_id="R2")
    assert result.ok is True
    assert result.status in {"CACHED_VALID", "STALE_VALID"}
    assert result.provider != "NONE"


def test_last_valid_cache_is_degraded_provider_not_none(tmp_path: Path) -> None:
    db = tmp_path / "lastcache.sqlite3"
    router = MarketDataOrchestrator(db_path=db)
    frame = __import__("core.data.candle_repository", fromlist=["normalize_frame"]).normalize_frame(
        _frame(rows=35), symbol="EURUSD", timeframe="H4", provider="TWELVE_DATA_KEY_POOL", provider_symbol="EURUSD"
    )
    router.repository.upsert(frame, run_id="seed")

    def fail(**kwargs):
        return pd.DataFrame(), False, "provider failed EMPTY_CANDLES"

    router = MarketDataOrchestrator(
        db_path=db,
        adapters={"TWELVE_DATA_KEY_POOL": fail, "FINNHUB": fail},
    )
    result = router.fetch(
        symbol="EURUSD",
        timeframe="H4",
        state={"twelve_api_key_1": "twelve", "finnhub_api_key": "finnhub"},
        bars=35,
        run_id="R3",
        force_live=True,
    )
    assert result.ok is True
    assert result.provider != "NONE"
    with sqlite3.connect(db) as conn:
        statuses = [row[0] for row in conn.execute("SELECT status FROM symbol_load_ledger_20260708")]
    assert "DEGRADED_VALID_CACHE" in statuses


def test_all_providers_fail_records_explicit_failure(tmp_path: Path) -> None:
    db = tmp_path / "fail.sqlite3"

    def fail(**kwargs):
        return pd.DataFrame(), False, "EMPTY_CANDLES"

    router = MarketDataOrchestrator(
        db_path=db,
        adapters={"TWELVE_DATA_KEY_POOL": fail, "FINNHUB": fail},
    )
    result = router.fetch(
        symbol="EURUSD",
        timeframe="H4",
        state={"twelve_api_key_1": "twelve", "finnhub_api_key": "finnhub"},
        bars=30,
        run_id="R4",
        force_live=True,
    )
    assert result.ok is False
    assert result.provider == "NONE"
    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT status,error_code FROM symbol_load_ledger_20260708 WHERE provider_attempted='ALL_PROVIDERS'").fetchall()
    assert rows and rows[-1][0] == "FAILED_EXPLICIT"


def test_symbol_provider_registry_opens_circuit_after_hard_failure(tmp_path: Path) -> None:
    db = tmp_path / "health.sqlite3"
    migrate_deployment_schema(db)
    registry = SymbolLevelProviderRegistry(db)
    registry.record_attempt(
        provider="TWELVE_DATA_KEY_POOL",
        symbol="EURUSD",
        timeframe="H4",
        ok=False,
        error_code="AUTH_FAILED",
        error_message="bad access_key",
    )
    score = registry.get_score("TWELVE_DATA_KEY_POOL", "EURUSD", "H4")
    assert score.live_state == "AUTH_FAILED"
    assert score.circuit_open is True
    assert registry.circuit_open("TWELVE_DATA_KEY_POOL", "GBPUSD", "H4") is True


def test_field10_status_board_shows_all_selected_including_failed() -> None:
    state = {
        LOAD_RECORDS_KEY: {
            CANONICAL_GROUP: {
                "group": CANONICAL_GROUP,
                "timeframe": "H4",
                "selection_signature": "x",
                "requested_symbols": ["EURUSD", "GBPUSD", "USDJPY"],
                "loaded_symbols": ["EURUSD"],
                "failed_symbols": ["GBPUSD", "USDJPY"],
                "validations": {
                    "EURUSD": {"ok": True, "provider": "TWELVE_DATA_KEY_POOL", "rows": 35, "reason": "READY"},
                    "GBPUSD": {"ok": False, "provider": "NONE", "rows": 0, "reason": "EMPTY_CANDLES"},
                    "USDJPY": {"ok": False, "provider": "NONE", "rows": 0, "reason": "RATE_LIMITED"},
                },
                "status": "PARTIAL_READY",
            }
        }
    }
    status = loaded_canonical_status(state, ["EURUSD", "GBPUSD", "USDJPY"], "H4")
    rows = status["status_rows"]
    assert [r["Symbol"] for r in rows] == ["EURUSD", "GBPUSD", "USDJPY"]
    assert rows[0]["Actual Candle Provider"] == "TWELVE_DATA_KEY_POOL"
    assert rows[1]["Final state"] == "FAILED_EXPLICIT"
    assert "Explicit failure reason" in rows[1]
