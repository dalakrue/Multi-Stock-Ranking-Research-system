from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from core.data.market_data_orchestrator import MarketDataResult
from core.data.multi_symbol_scheduler import MultiSymbolScheduler, ScheduleItem
from core.full_metric_canonical_adapter_20260618 import build_full_metric_authority
from core.multi_symbol_authority_identity_20260706 import restamp_child_authority
from core.multi_symbol_field10_20260701 import assess_data_quality
from ui.lunch_field10_multi_symbol_20260701 import _ensure_time_columns


def _ohlc(rows: int, timeframe: str = "H4") -> pd.DataFrame:
    freq = "4h" if timeframe == "H4" else "h"
    time = pd.date_range("2026-04-01", periods=rows, freq=freq, tz="UTC")
    return pd.DataFrame({
        "time": time,
        "open": 1.10,
        "high": 1.11,
        "low": 1.09,
        "close": 1.105,
        "volume": 100,
    })


def test_full_metric_authority_remains_strict_and_identity_only_child_adapter_restamps():
    metric = {
        "ok": True,
        "scores": {"Direction": "BUY", "Decision": "ALLOWED", "Master /10": 8},
        "metrics": {"close": 1.105},
    }
    frame = _ohlc(3)
    with pytest.raises(ValueError, match="requires EURUSD H1"):
        build_full_metric_authority(metric, frame, symbol="EURCHF", timeframe="H4")

    protected = build_full_metric_authority(metric, frame, symbol="EURUSD", timeframe="H1")
    original_scores = dict(protected["snapshot"])
    authority = restamp_child_authority(
        protected, symbol="EURCHF", timeframe="H4", source_frame=frame,
    )
    snapshot = authority["snapshot"]
    assert snapshot["symbol"] == "EURCHF"
    assert snapshot["timeframe"] == "H4"
    assert snapshot["authority_scope"] == "MULTI_SYMBOL_CHILD"
    assert snapshot["operational_authority"] is False
    assert snapshot["latest_completed_candle_time"] == frame["time"].iloc[-1].isoformat()
    assert snapshot["master_score"] == original_scores["master_score"]
    assert snapshot["tradeability_decision"] == original_scores["tradeability_decision"]


def test_h4_quality_uses_150_candle_contract_not_h1_600():
    frame = _ohlc(150)
    state = {
        "canonical_completed_ohlc_df_20260617": frame,
        "selected_timeframe": "H4",
        "timeframe": "H4",
    }
    canonical = {
        "run_id": "RUN-EURCHF-H4",
        "symbol": "EURCHF",
        "timeframe": "H4",
        "source_id": "TWELVE:EURCHF:H4",
    }
    report = assess_data_quality(state, canonical)
    assert report["timeframe"] == "H4"
    assert report["required_rows"] == 150
    assert report["rows"] == 150
    assert report["status"] == "PASS"
    assert not any("/600" in reason for reason in report["reasons"])


def test_field10_display_guarantees_time_and_timeframe_columns():
    source = pd.DataFrame({
        "Rank": [1, 2],
        "Symbol": ["EURCHF", "NZDUSD"],
        "Completed Broker Candle": ["2026-07-06T04:00:00+00:00"] * 2,
    })
    view = _ensure_time_columns(source, {"timeframe": "H4"})
    assert list(view.columns[:2]) == ["Time", "Timeframe"]
    assert view["Time"].tolist() == source["Completed Broker Candle"].tolist()
    assert view["Timeframe"].tolist() == ["H4", "H4"]


def test_quota_scheduler_waits_for_persistent_capacity_and_completes_all(tmp_path: Path):
    class FakeQuota:
        def __init__(self):
            self.available = False

        def status(self):
            return SimpleNamespace(to_dict=lambda: {
                "estimated_credits_remaining": 6.0 if self.available else 0.0,
                "next_safe_request_time": None,
                "rate_limited": False,
            })

    class FakeOrchestrator:
        def __init__(self):
            self.quota = FakeQuota()
            self.calls: list[str] = []

        def fetch(self, **kwargs):
            self.calls.append(kwargs["symbol"])
            frame = _ohlc(150)
            return MarketDataResult(
                ok=True,
                symbol=kwargs["symbol"],
                timeframe=kwargs["timeframe"],
                frame=frame,
                provider="TWELVE_DATA",
                provider_symbol=kwargs["symbol"],
                status="LIVE_PRIMARY",
                message="ok",
                latest_completed_candle=frame["time"].iloc[-1].isoformat(),
                fallback_provider=None,
                attempts=[{"provider": "TWELVE_DATA", "ok": True, "request_sent": True}],
                data_age_seconds=0.0,
                data_quality_score=100.0,
                validation_status="VALID",
                run_id=kwargs["run_id"],
            )

    fake = FakeOrchestrator()
    sleeps: list[float] = []

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        fake.quota.available = True

    scheduler = MultiSymbolScheduler(
        db_path=tmp_path / "scheduler.sqlite3",
        orchestrator=fake,
        sleep_fn=sleep,
        clock_fn=lambda: 0.0,
    )
    symbols = ["EURCHF", "NZDUSD"]
    scheduler.plan = lambda *args, **kwargs: [
        ScheduleItem(
            symbol=symbol,
            timeframe="H4",
            needs_update=True,
            missing_data=True,
            latest_completed_candle=None,
            expected_completed_candle="2026-07-06T04:00:00+00:00",
            active_session_relevance=0,
            field10_priority=0.0,
            active_symbol=index == 0,
            reason="MISSING_HISTORY",
        )
        for index, symbol in enumerate(symbols)
    ]
    report = scheduler.run(
        symbols=symbols,
        timeframe="H4",
        state={
            "quota_safe_stagger_enabled_20260706": True,
            "quota_safe_batch_size_20260706": 4,
            "quota_safe_batch_interval_seconds_20260706": 1,
            "multi_symbol_fetch_rounds_20260706": 3,
        },
        bars=150,
        run_id="RUN-ALL-10",
        force_live=True,
    )
    assert sleeps
    assert fake.calls == symbols
    assert report["complete"] is True
    assert report["unresolved_symbols"] == []


def test_selector_contains_validated_runtime_cache_fallback_and_load_button():
    selector = Path("ui/lunch_multi_symbol_selector_20260704.py").read_text(encoding="utf-8")
    core = Path("core/multi_symbol_field10_20260701.py").read_text(encoding="utf-8")
    assert 'form_submit_button("Load Selected Symbol"' in selector
    assert "COMPLETE_RUNTIME_RESTORED" in selector
    assert "COMPLETE_RUNTIME_RESTORED" in core
    assert "validate_child_state(state, runtime_snapshot_path=cache_path)" in core


def test_settings_multi_symbol_child_uses_identity_only_adapter():
    source = Path("core/settings_run_orchestrator_20260617.py").read_text(encoding="utf-8")
    assert "restamp_child_authority" in source
    assert 'multi_symbol_child_run_active_20260701' in source
    assert 'symbol="EURUSD" if multi_symbol_child else symbol' in source


def test_settings_source_identity_uses_exact_multi_symbol_child_timeframe(monkeypatch):
    import core.settings_run_orchestrator_20260617 as settings

    fake_state = {
        "multi_symbol_child_run_active_20260701": {"symbol": "EURCHF"},
        "calculation_symbol_20260702": "EURCHF",
        "selected_timeframe": "H4",
        "timeframe": "H4",
        "source": "TWELVE_DATA",
    }
    monkeypatch.setattr(settings, "st", SimpleNamespace(session_state=fake_state))
    assert settings._source_identity() == ("EURCHF", "H4", "TWELVE_DATA")


def test_live_response_is_merged_with_existing_exact_symbol_repository_history(tmp_path: Path):
    from core.data.candle_repository import normalize_frame
    from core.data.market_data_orchestrator import MarketDataOrchestrator

    def raw(start: str, periods: int) -> pd.DataFrame:
        time = pd.date_range(start, periods=periods, freq="4h", tz="UTC")
        return pd.DataFrame({
            "time": time,
            "open": 1.10,
            "high": 1.11,
            "low": 1.09,
            "close": 1.105,
            "volume": 100,
        })

    response_page = raw("2025-01-14", 80)
    disabled = lambda **kwargs: (_ for _ in ()).throw(RuntimeError("disabled in test"))
    orchestrator = MarketDataOrchestrator(
        db_path=tmp_path / "merged-history.sqlite3",
        adapters={
            "TWELVE_DATA": lambda **kwargs: response_page,
            "MT5": disabled,
            "FINNHUB": disabled,
            "ALPHA_VANTAGE": disabled,
        },
    )
    seed = normalize_frame(
        raw("2025-01-01", 100),
        symbol="EURCHF",
        timeframe="H4",
        provider="SEED",
        provider_symbol="EUR/CHF",
        source_status="CACHED_VALID",
    )
    orchestrator.repository.upsert(seed, run_id="seed", require_complete=True)

    result = orchestrator.fetch(
        symbol="EURCHF",
        timeframe="H4",
        state={"twelve_api_key": "test-only"},
        bars=180,
        run_id="merge-test",
        force_live=True,
    )
    assert result.ok
    assert len(result.frame) >= 150
    assert result.attempts[-1]["response_rows"] == 80
    assert result.attempts[-1]["repository_rows_after_merge"] == len(result.frame)
