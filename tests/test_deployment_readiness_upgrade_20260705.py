from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

import pandas as pd
import pytest

from core.data.candle_repository import CandleRepository, normalize_frame
from core.data.deployment_migrations_20260705 import migrate_deployment_schema
from core.data.market_data_orchestrator import (
    MarketDataOrchestrator,
    PROVIDER_PRIORITY,
    ProviderPermanentError,
)
from core.data.multi_symbol_scheduler import MultiSymbolScheduler
from core.data.twelve_data_quota_manager import TwelveDataQuotaManager
from core.runtime_selection_20260705 import (
    TOP_10_CURRENCY_PAIRS,
    latest_completed_candle,
    load_runtime_preferences,
    save_runtime_preferences,
    synchronize_runtime_selection,
)
from core.sentiment.eurusd_sentiment_engine import score_article


def _complete_frame(rows: int = 8, *, freq: str = "h") -> pd.DataFrame:
    times = pd.date_range(end=pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=3), periods=rows, freq=freq)
    close = pd.Series([1.10 + i * 0.0001 for i in range(rows)], dtype=float)
    return pd.DataFrame(
        {
            "time": times,
            "open": close - 0.00005,
            "high": close + 0.0002,
            "low": close - 0.0002,
            "close": close,
            "volume": [100 + i for i in range(rows)],
        }
    )


def test_provider_priority_is_finnhub_active_and_twelve_first_fallback(tmp_path: Path) -> None:
    assert PROVIDER_PRIORITY == (
        "FINNHUB", "TWELVE_DATA", "MT5", "ALPHA_VANTAGE",
        "LOCAL_VALID_CACHE",
    )
    calls: list[str] = []

    def finnhub(**kwargs):
        calls.append("FINNHUB")
        raise ProviderPermanentError("endpoint unavailable")

    def twelve(**kwargs):
        calls.append("TWELVE_DATA")
        return _complete_frame()

    def forbidden(name: str):
        def _adapter(**kwargs):
            calls.append(name)
            raise AssertionError(f"{name} must not run after Twelve fallback success")
        return _adapter

    orchestrator = MarketDataOrchestrator(
        db_path=tmp_path / "providers.sqlite3",
        adapters={
            "FINNHUB": finnhub,
            "TWELVE_DATA": twelve,
            "MT5": forbidden("MT5"),
            "ALPHA_VANTAGE": forbidden("ALPHA_VANTAGE"),
        },
    )
    result = orchestrator.fetch(
        symbol="EURUSD", timeframe="H1",
        state={"connector_mode": "finnhub", "finnhub_api_key": "f", "twelve_api_key": "t",
               "settings_calculation_scope_20260625": "LUNCH_CORE"},
        bars=8, run_id="T-PROVIDER", force_live=True,
    )
    assert result.ok
    assert result.provider == "TWELVE_DATA"
    assert result.status == "LIVE_FALLBACK"
    assert result.fallback_provider == "TWELVE_DATA"
    assert calls == ["FINNHUB", "TWELVE_DATA"]


def test_successful_finnhub_primary_skips_all_fallback_providers(tmp_path: Path) -> None:
    calls: list[str] = []

    def finnhub(**kwargs):
        calls.append("FINNHUB")
        return _complete_frame()

    def forbidden(name: str):
        def _adapter(**kwargs):
            calls.append(name)
            raise AssertionError(f"{name} must not run after Finnhub success")
        return _adapter

    orchestrator = MarketDataOrchestrator(
        db_path=tmp_path / "active.sqlite3",
        adapters={
            "FINNHUB": finnhub,
            "TWELVE_DATA": forbidden("TWELVE_DATA"),
            "MT5": forbidden("MT5"),
            "ALPHA_VANTAGE": forbidden("ALPHA_VANTAGE"),
        },
    )
    result = orchestrator.fetch(
        symbol="EURUSD", timeframe="H1",
        state={"connector_mode": "finnhub", "finnhub_api_key": "y"},
        bars=8, run_id="T-ACTIVE", force_live=True,
    )
    assert result.provider == "FINNHUB"
    assert result.status == "LIVE_PRIMARY"
    assert result.fallback_provider is None
    assert calls == ["FINNHUB"]

def test_twelve_quota_stops_at_six_and_survives_restart(tmp_path: Path) -> None:
    now = datetime(2026, 7, 5, 12, 0, tzinfo=timezone.utc)
    db = tmp_path / "quota.sqlite3"
    first = TwelveDataQuotaManager(db, clock=lambda: now)
    reservations = [first.reserve(cost=1, run_id="Q", symbol=f"S{i}", timeframe="H1") for i in range(6)]
    assert all(item["allowed"] for item in reservations)
    blocked = first.reserve(cost=1, run_id="Q", symbol="S6", timeframe="H1")
    assert blocked["allowed"] is False
    assert blocked["reason"] in {"ROLLING_MINUTE_SAFETY_LIMIT", "CONCURRENT_QUOTA_RECHECK_FAILED"}
    restarted = TwelveDataQuotaManager(db, clock=lambda: now)
    assert restarted.status().credits_used_last_60_seconds == pytest.approx(6.0)


def test_scheduler_does_not_use_emergency_reserve_by_default(tmp_path: Path) -> None:
    db = tmp_path / "scheduler.sqlite3"
    calls: list[str] = []

    def twelve(**kwargs):
        calls.append(kwargs["symbol"])
        return _complete_frame()

    def mt5(**kwargs):
        return _complete_frame()

    orchestrator = MarketDataOrchestrator(
        db_path=db,
        adapters={
            "TWELVE_DATA": twelve,
            "MT5": mt5,
            "FINNHUB": lambda **kwargs: _complete_frame(),
            "ALPHA_VANTAGE": lambda **kwargs: _complete_frame(),
        },
    )
    scheduler = MultiSymbolScheduler(db_path=db, orchestrator=orchestrator, max_live_requests_per_window=6, sleep_fn=lambda _seconds: None)
    report = scheduler.run(
        symbols=list(TOP_10_CURRENCY_PAIRS), timeframe="H1",
        state={"twelve_api_key": "x"}, bars=8, run_id="Q10", force_live=True,
    )
    assert report["complete"]
    assert len(calls) <= 6
    assert report["quota"]["credits_used_last_60_seconds"] <= 6


def test_incremental_candle_storage_rejects_duplicate_and_invalid_ohlc(tmp_path: Path) -> None:
    db = tmp_path / "candles.sqlite3"
    repo = CandleRepository(db)
    normalized = normalize_frame(
        _complete_frame(3), symbol="EURUSD", timeframe="H1", provider="TWELVE_DATA",
        provider_symbol="EUR/USD", now=datetime.now(timezone.utc),
    )
    first = repo.upsert(normalized, run_id="R1")
    second = repo.upsert(normalized, run_id="R2")
    assert first["inserted"] == 3
    assert second["duplicates"] == 3
    invalid = normalized.iloc[[0]].copy()
    invalid["high"] = invalid["low"] - 1
    rejected = repo.upsert(invalid, run_id="R3")
    assert rejected["rejected"] == 1
    assert repo.count("EURUSD", "H1") == 3


def test_h4_completed_candle_and_persistence_are_consistent(tmp_path: Path) -> None:
    now = datetime(2026, 7, 5, 12, 2, tzinfo=timezone.utc)
    assert latest_completed_candle(now=now, timeframe="H4", settlement_delay_minutes=3) == datetime(2026, 7, 5, 4, 0, tzinfo=timezone.utc)
    db = tmp_path / "prefs.sqlite3"
    migrate_deployment_schema(db)
    save_runtime_preferences(db, TOP_10_CURRENCY_PAIRS, "H4")
    loaded = load_runtime_preferences(db)
    state: dict[str, object] = {}
    synchronized = synchronize_runtime_selection(state, persisted=loaded)
    assert synchronized["selected_symbols"] == list(TOP_10_CURRENCY_PAIRS)
    assert synchronized["timeframe"] == "H4"
    assert state["connector_timeframe_20260705"] == "H4"


def test_migrations_are_idempotent_on_clean_and_legacy_schema(tmp_path: Path) -> None:
    clean = tmp_path / "clean.sqlite3"
    assert migrate_deployment_schema(clean)["ok"]
    assert migrate_deployment_schema(clean)["ok"]
    legacy = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(legacy) as conn:
        conn.execute(
            "CREATE TABLE schema_migrations(migration_id TEXT PRIMARY KEY, checksum TEXT NOT NULL, description TEXT NOT NULL, applied_at_utc TEXT NOT NULL)"
        )
        conn.commit()
    assert migrate_deployment_schema(legacy)["ok"]
    with sqlite3.connect(legacy) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "deployment_schema_migrations" in tables
    assert "candles" in tables
    assert "canonical_snapshots" in tables


def test_available_published_symbols_accepts_repaired_signature() -> None:
    from core.multi_symbol_field10_20260701 import available_published_symbols

    state = {"multi_symbol_selected_20260701": ["EURUSD", "USDJPY"]}
    assert available_published_symbols(state, requested=["EURUSD", "USDJPY"])[:2] == ["EURUSD", "USDJPY"]


def test_currency_aware_sentiment_direction_mapping() -> None:
    hawkish_ecb = score_article({"title": "Hawkish ECB signals higher for longer", "published_at": datetime.now(timezone.utc).isoformat()})
    hawkish_fed = score_article({"title": "Hawkish Federal Reserve signals higher for longer", "published_at": datetime.now(timezone.utc).isoformat()})
    weak_us_labor = score_article({"title": "Weak US dollar outlook after unemployment and jobless claims rise", "published_at": datetime.now(timezone.utc).isoformat()})
    assert hawkish_ecb["pair_direction_implication"] > 0
    assert hawkish_fed["pair_direction_implication"] < 0
    assert weak_us_labor["pair_direction_implication"] > 0


def test_lunch_selector_is_rendered_before_lunch_metrics() -> None:
    source = Path("ui/lunch_four_core_fields_20260619.py").read_text(encoding="utf-8")
    call = source.index("selected_field = _render_lunch_field_selector_top")
    first_lunch_metric = source.index('status_cols = st.columns(3)')
    assert call < first_lunch_metric
    assert source.count('"Choose the Lunch Field to Open"') == 1


def test_deferred_refresh_contains_no_provider_fetch_call() -> None:
    source = Path("core/app/refresh.py").read_text(encoding="utf-8")
    block = source[source.index("def run_deferred_refresh"):]
    assert "refresh_data(" not in block
    assert "MarketDataOrchestrator" not in block
    assert "restore_into_state" in block


def test_field10_h4_identity_never_falls_back_to_h1(tmp_path: Path) -> None:
    from core.field10_research_common_20260705 import build_identity, exact_completed_h1

    meta = {
        "daily_snapshot_id": "H4-SNAPSHOT",
        "parent_run_id": "H4-PARENT",
        "broker_day": "2026-07-05",
        "timeframe": "H4",
        "latest_completed_h1": "2026-07-05T08:00:00+00:00",
        "ordered_symbol_universe": ["EURUSD"],
        "universe_hash": "h4-universe",
    }
    row = {
        "symbol": "EURUSD",
        "canonical_run_id": "H4-RUN",
        "source_id": "H4-SOURCE",
        "snapshot_hash": "h4-hash",
        "timeframe": "H4",
    }
    db = tmp_path / "empty.sqlite3"
    migrate_deployment_schema(db)
    identity = build_identity(meta, row, path=db)
    assert identity.timeframe == "H4"
    frame, reasons = exact_completed_h1({}, identity)
    assert frame.empty
    assert reasons and "H1-only research candidate" in reasons[0]


def test_field10_runtime_prefers_selected_h4_over_legacy_identity() -> None:
    source = Path("core/multi_symbol_field10_20260701.py").read_text(encoding="utf-8")
    assert 'state.get("timeframe") or canonical.get("timeframe") or "H4"' in source
    assert 'state.get("timeframe") or frozen_canonical.get("timeframe") or "H4"' in source
