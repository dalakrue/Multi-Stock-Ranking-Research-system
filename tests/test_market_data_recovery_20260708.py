from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.data.market_data_orchestrator import (
    MarketDataOrchestrator,
    ProviderPermanentError,
    PROVIDER_PRIORITY,
)


def _frame(rows: int = 160, *, freq: str = "h") -> pd.DataFrame:
    times = pd.date_range("2026-06-01", periods=rows, freq=freq, tz="UTC")
    close = pd.Series([1.10 + i * 0.0001 for i in range(rows)], dtype=float)
    return pd.DataFrame(
        {
            "time": times,
            "open": close - 0.00005,
            "high": close + 0.0002,
            "low": close - 0.0002,
            "close": close,
            "volume": 1000.0,
        }
    )


class _Response:
    status_code = 200
    headers: dict[str, str] = {}

    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _Session:
    def __init__(self, payload):
        self.payload = payload
        self.calls: list[dict[str, object]] = []

    def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return _Response(self.payload)


def test_live_fallback_order_matches_settings_contract() -> None:
    assert PROVIDER_PRIORITY == ("FINNHUB", "TWELVE_DATA", "MT5", "ALPHA_VANTAGE", "LOCAL_VALID_CACHE")


def test_provider_symbol_mapping_covers_fx() -> None:
    assert MarketDataOrchestrator.provider_symbol("EURUSD", "FINNHUB") == "OANDA:EUR_USD"
    assert MarketDataOrchestrator.provider_symbol("EURUSD", "TWELVE_DATA") == "EUR/USD"
    assert MarketDataOrchestrator.provider_symbol("EURUSD", "MT5") == "EURUSD"


def test_mt5_fallback_recovers_when_key_providers_fail(tmp_path: Path) -> None:
    calls: list[str] = []

    def fail(name: str):
        def _adapter(**kwargs):
            calls.append(name)
            raise ProviderPermanentError(f"{name} unavailable")
        return _adapter

    def mt5(**kwargs):
        calls.append("MT5")
        return _frame()

    def forbidden(**kwargs):
        raise AssertionError("downstream providers must not run after keyless live success")

    orchestrator = MarketDataOrchestrator(
        db_path=tmp_path / "recovery.sqlite3",
        adapters={
            "FINNHUB": fail("FINNHUB"),
            "TWELVE_DATA": fail("TWELVE_DATA"),
            "MT5": mt5,
            "ALPHA_VANTAGE": forbidden,
        },
    )
    result = orchestrator.fetch(
        symbol="EURUSD",
        timeframe="H1",
        bars=120,
        force_live=True,
        run_id="RECOVERY",
        state={"connector_mode": "finnhub", "finnhub_api_key": "configured", "twelve_api_key": "configured"},
    )
    assert result.ok is True
    assert result.provider == "MT5"
    assert result.status == "LIVE_FALLBACK"
    assert len(result.frame) == 120
    assert calls == ["FINNHUB", "TWELVE_DATA", "MT5"]


def test_yahoo_h4_is_built_from_real_h1_rows(tmp_path: Path) -> None:
    timestamps = [int(value.timestamp()) for value in pd.date_range("2026-06-01", periods=40, freq="h", tz="UTC")]
    payload = {
        "chart": {
            "error": None,
            "result": [
                {
                    "timestamp": timestamps,
                    "indicators": {
                        "quote": [
                            {
                                "open": [1.0 + i * 0.001 for i in range(40)],
                                "high": [1.01 + i * 0.001 for i in range(40)],
                                "low": [0.99 + i * 0.001 for i in range(40)],
                                "close": [1.005 + i * 0.001 for i in range(40)],
                                "volume": [100 + i for i in range(40)],
                            }
                        ]
                    },
                }
            ],
        }
    }
    session = _Session(payload)
    orchestrator = MarketDataOrchestrator(db_path=tmp_path / "yahoo-h4.sqlite3", session=session)
    frame = orchestrator._fetch_yahoo_finance(
        symbol="EURUSD",
        provider_symbol="EURUSD=X",
        timeframe="H4",
        bars=8,
        state={},
    )
    assert len(frame) == 8
    assert list(frame.columns) == ["time", "open", "high", "low", "close", "volume"]
    assert pd.to_datetime(frame["time"], utc=True).diff().dropna().dt.total_seconds().eq(4 * 3600).all()
    assert session.calls
    assert session.calls[0]["params"]["interval"] == "1h"


def test_provider_failure_messages_redact_tokens_and_explain_route(tmp_path: Path) -> None:
    secret = "super-secret-token-123456"

    def fail_with_secret(**kwargs):
        raise RuntimeError(f"request failed token={secret}&symbol=EURUSD")

    orchestrator = MarketDataOrchestrator(
        db_path=tmp_path / "redaction.sqlite3",
        adapters={
            "FINNHUB": fail_with_secret,
            "TWELVE_DATA": fail_with_secret,
            "YAHOO_FINANCE": fail_with_secret,
            "MT5": fail_with_secret,
            "ALPHA_VANTAGE": fail_with_secret,
        },
    )
    result = orchestrator.fetch(
        symbol="EURUSD",
        timeframe="H1",
        bars=20,
        force_live=True,
        state={"connector_mode": "finnhub", "finnhub_api_key": secret, "twelve_api_key": secret, "alpha_vantage_api_key": secret},
    )
    assert result.ok is False
    assert secret not in result.message
    assert secret not in str(result.attempts)
    assert "Provider route:" in result.message
    assert "[REDACTED]" in result.message
