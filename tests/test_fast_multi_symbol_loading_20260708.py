from __future__ import annotations

from pathlib import Path

import pandas as pd


class _Response:
    status_code = 200
    headers: dict[str, str] = {}

    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _Session:
    def __init__(self, payload: dict):
        self.payload = payload
        self.calls: list[dict] = []

    def get(self, url: str, *, params: dict, timeout: float):
        self.calls.append({"url": url, "params": dict(params), "timeout": timeout})
        return _Response(self.payload)


def _raw_hourly_payload(rows: int = 20) -> dict:
    stamps = pd.date_range("2026-07-01", periods=rows, freq="h", tz="UTC")
    base = pd.Series(range(rows), dtype=float) / 10000.0 + 1.10
    return {
        "s": "ok",
        "t": [int(value.timestamp()) for value in stamps],
        "o": base.tolist(),
        "h": (base + 0.0005).tolist(),
        "l": (base - 0.0005).tolist(),
        "c": (base + 0.0001).tolist(),
        "v": [1000.0] * rows,
    }


def _valid_frame(symbol: str, timeframe: str = "H1", rows: int = 120) -> pd.DataFrame:
    freq = "h" if timeframe == "H1" else "4h"
    stamps = pd.date_range("2026-01-01", periods=rows, freq=freq, tz="UTC")
    base = pd.Series(range(rows), dtype=float) / 10000.0 + 1.10
    return pd.DataFrame({
        "open_time": stamps,
        "open": base,
        "high": base + 0.0005,
        "low": base - 0.0005,
        "close": base + 0.0001,
        "volume": 1000.0,
        "symbol": symbol,
        "timeframe": timeframe,
        "provider": "FINNHUB",
        "provider_symbol": symbol,
        "validation_status": "VALID",
        "is_complete": True,
        "data_quality_score": 100.0,
    })


def test_finnhub_h4_uses_supported_h1_resolution_and_resamples(tmp_path: Path):
    from core.data.market_data_orchestrator import MarketDataOrchestrator

    session = _Session(_raw_hourly_payload(20))
    orchestrator = MarketDataOrchestrator(db_path=tmp_path / "h4.sqlite3", session=session)
    frame = orchestrator._fetch_finnhub(
        symbol="EURUSD",
        provider_symbol="OANDA:EUR_USD",
        timeframe="H4",
        bars=100,
        state={"finnhub_api_key": "test-key"},
    )

    assert session.calls
    call = session.calls[0]
    assert call["url"].endswith("/forex/candle")
    assert call["params"]["resolution"] == "60"
    assert not frame.empty
    assert len(frame) == 5
    assert frame["time"].diff().dropna().dt.total_seconds().eq(4 * 3600).all()


def test_finnhub_routes_crypto_and_stock_to_correct_candle_endpoint(tmp_path: Path):
    from core.data.market_data_orchestrator import MarketDataOrchestrator

    session = _Session(_raw_hourly_payload(8))
    orchestrator = MarketDataOrchestrator(db_path=tmp_path / "assets.sqlite3", session=session)

    assert orchestrator.provider_symbol("BTCUSD", "FINNHUB") == "BINANCE:BTCUSDT"
    orchestrator._fetch_finnhub(
        symbol="BTCUSD", provider_symbol="BINANCE:BTCUSDT", timeframe="H1", bars=4,
        state={"finnhub_api_key": "test-key"},
    )
    orchestrator._fetch_finnhub(
        symbol="AAPL", provider_symbol="AAPL", timeframe="H1", bars=4,
        state={"finnhub_api_key": "test-key"},
    )

    assert session.calls[-2]["url"].endswith("/crypto/candle")
    assert session.calls[-1]["url"].endswith("/stock/candle")


class _QuotaStatus:
    def to_dict(self) -> dict:
        return {"estimated_credits_remaining": 0, "rate_limited": True, "next_safe_request_time": None}


class _Quota:
    def status(self) -> _QuotaStatus:
        return _QuotaStatus()


class _FastOrchestrator:
    def __init__(self):
        self.quota = _Quota()
        self.disabled_seen: list[set[str]] = []
        self.calls = 0

    def fetch(self, *, symbol, timeframe, state, bars, run_id, force_live, essential, disabled_providers):
        from core.data.market_data_orchestrator import MarketDataResult

        self.calls += 1
        self.disabled_seen.append(set(disabled_providers))
        attempts = []
        if self.calls == 1 and state.get("simulate_finnhub_timeout"):
            attempts = [{
                "provider": "FINNHUB",
                "ok": False,
                "request_sent": True,
                "category": "TEMPORARY_PROVIDER_ERROR",
                "message": "Connection timeout",
            }, {
                "provider": "TWELVE_DATA",
                "ok": True,
                "request_sent": True,
            }]
        return MarketDataResult(
            ok=True,
            symbol=symbol,
            timeframe=timeframe,
            frame=_valid_frame(symbol, timeframe, 120),
            provider="FINNHUB" if not attempts else "TWELVE_DATA",
            provider_symbol=symbol,
            status="LIVE_PRIMARY" if not attempts else "LIVE_FALLBACK",
            message="ready",
            latest_completed_candle="2026-07-01T00:00:00+00:00",
            fallback_provider=None if not attempts else "TWELVE_DATA",
            attempts=attempts,
            data_age_seconds=0.0,
            data_quality_score=100.0,
            validation_status="VALID",
            run_id=run_id,
        )


def test_finnhub_primary_12_symbol_load_never_uses_twelve_wait(tmp_path: Path):
    from core.data.multi_symbol_scheduler import MultiSymbolScheduler

    sleeps: list[float] = []
    orchestrator = _FastOrchestrator()
    scheduler = MultiSymbolScheduler(
        db_path=tmp_path / "scheduler.sqlite3",
        orchestrator=orchestrator,
        max_live_requests_per_window=7,
        sleep_fn=sleeps.append,
    )
    symbols = [
        "EURUSD", "USDJPY", "AUDUSD", "GBPUSD", "USDCAD", "USDCHF",
        "EURJPY", "GBPJPY", "EURGBP", "NZDUSD", "EURCHF", "EURAUD",
    ]
    report = scheduler.run(
        symbols=symbols,
        timeframe="H1",
        state={
            "connector_mode": "finnhub",
            "quota_safe_stagger_enabled_20260706": False,
            "market_data_progress_full_range_20260708": True,
        },
        bars=120,
        run_id="FAST-LOAD",
    )

    assert report["complete"] is True
    assert report["quota_safe_stagger"]["enabled"] is False
    assert report["quota_safe_stagger"]["paced_wait_seconds"] == 0.0
    assert sleeps == []
    assert orchestrator.calls == 12


def test_run_scoped_circuit_breaker_skips_repeated_finnhub_timeout(tmp_path: Path):
    from core.data.multi_symbol_scheduler import MultiSymbolScheduler

    orchestrator = _FastOrchestrator()
    scheduler = MultiSymbolScheduler(
        db_path=tmp_path / "circuit.sqlite3",
        orchestrator=orchestrator,
        sleep_fn=lambda _: None,
    )
    report = scheduler.run(
        symbols=["EURUSD", "USDJPY", "AUDUSD"],
        timeframe="H1",
        state={"connector_mode": "finnhub", "simulate_finnhub_timeout": True},
        bars=120,
        run_id="CIRCUIT",
    )

    assert orchestrator.disabled_seen[0] == set()
    assert "FINNHUB" in orchestrator.disabled_seen[1]
    assert "FINNHUB" in orchestrator.disabled_seen[2]
    assert report["run_disabled_providers"] == ["FINNHUB"]


def test_load_manager_returns_structured_failure_instead_of_raising(monkeypatch, tmp_path: Path):
    from core.calculation import run_orchestrator
    from core.data import deployment_migrations_20260705 as migrations
    from core.multi_symbol_load_manager_20260707 import load_group_market_data

    monkeypatch.setattr(migrations, "DEFAULT_DB_PATH", tmp_path / "structured.sqlite3")

    def fail_prepare(*args, **kwargs):
        raise RuntimeError("provider bootstrap failed")

    monkeypatch.setattr(run_orchestrator, "prepare_market_data_for_run", fail_prepare)
    state: dict[str, object] = {"connector_mode": "finnhub"}
    record = load_group_market_data(state, "FIRST", ["EURUSD", "USDJPY"], "H1")

    assert record["status"] == "FAILED"
    assert record["requested_symbols"] == ["EURUSD", "USDJPY"]
    assert record["failed_symbols"] == ["EURUSD", "USDJPY"]
    assert "provider bootstrap failed" in record["fatal_prepare_error"]
    assert record["load_elapsed_seconds"] >= 0.0
