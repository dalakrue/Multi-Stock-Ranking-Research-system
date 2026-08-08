from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.child_generation_contract_20260702 import _standard_frames
from core.child_snapshot_publication_20260706 import _has_field1
from core.data.market_data_orchestrator import (
    MarketDataOrchestrator,
    ProviderPermanentError,
    provider_priority_for_state,
)
from core.multi_symbol_load_manager_20260707 import (
    LOAD_RECORDS_KEY,
    loaded_group_status,
    selection_signature,
)
from ui.multi_symbol_settings_20260701 import (
    FIRST_BEST_6_CURRENCY_PAIRS,
    SECOND_BEST_6_CURRENCY_PAIRS,
)


def _ohlc(rows: int = 120) -> pd.DataFrame:
    time = pd.date_range("2025-01-01", periods=rows, freq="h", tz="UTC")
    close = pd.Series(range(rows), dtype=float) / 10000.0 + 1.10
    return pd.DataFrame({
        "time": time,
        "open": close,
        "high": close + 0.0005,
        "low": close - 0.0005,
        "close": close + 0.0001,
        "volume": 100,
    })


class _QuotaStub:
    def reserve(self, **kwargs):
        return {"allowed": True, "request_id": "quota-test"}

    def complete(self, *args, **kwargs):
        return None

    def release(self, *args, **kwargs):
        return None

    def record_429(self, *args, **kwargs):
        return None

    @staticmethod
    def backoff_seconds(attempt: int) -> float:
        return 0.0


def test_requested_currency_pair_presets_are_exact_and_visible_in_both_selectors():
    assert FIRST_BEST_6_CURRENCY_PAIRS == [
        "AUDUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP",
    ]
    assert SECOND_BEST_6_CURRENCY_PAIRS == [
        "NZDUSD", "EURCHF", "EURAUD", "EURCAD", "EURNZD", "GBPCHF",
    ]
    source = Path("ui/multi_symbol_settings_20260701.py").read_text(encoding="utf-8")
    assert 'if group_name in {"FIRST", "SECOND"}' in source
    assert '"First Best 6 Currency Pairs"' in source
    assert '"Second Best 6 Currency Pairs"' in source


def test_api_source_priority_is_finnhub_first_but_twelve_is_retained():
    finnhub = provider_priority_for_state({"connector_mode": "finnhub"})
    twelve = provider_priority_for_state({"connector_mode": "twelve"})
    assert finnhub[0] == "FINNHUB"
    assert "TWELVE_DATA" in finnhub
    assert twelve[0] == "FINNHUB"  # legacy profile is migrated, not promoted
    assert twelve[1] == "TWELVE_DATA"


def test_finnhub_selected_source_loads_exact_symbol_without_calling_twelve(tmp_path: Path):
    calls: list[str] = []

    def finnhub(**kwargs):
        calls.append(f"FINNHUB:{kwargs['symbol']}:{kwargs['timeframe']}")
        return _ohlc()

    def forbidden(**kwargs):
        calls.append(f"TWELVE_DATA:{kwargs['symbol']}:{kwargs['timeframe']}")
        raise AssertionError("Twelve Data must not run after a successful Finnhub primary load")

    disabled = lambda **kwargs: (_ for _ in ()).throw(ProviderPermanentError("disabled"))
    orchestrator = MarketDataOrchestrator(
        db_path=tmp_path / "finnhub-primary.sqlite3",
        quota_manager=_QuotaStub(),
        adapters={
            "FINNHUB": finnhub,
            "TWELVE_DATA": forbidden,
            "MT5": disabled,
            "ALPHA_VANTAGE": disabled,
        },
    )
    result = orchestrator.fetch(
        symbol="AUDUSD", timeframe="H1",
        state={"connector_mode": "finnhub", "finnhub_api_key": "test-key"},
        bars=120, run_id="FINNHUB-PRIMARY", force_live=True,
    )
    assert result.ok is True
    assert result.provider == "FINNHUB"
    assert result.provider_symbol == "OANDA:AUD_USD"
    assert result.status == "LIVE_PRIMARY"
    assert result.fallback_provider is None
    assert calls == ["FINNHUB:AUDUSD:H1"]
    assert set(result.frame["symbol"].unique()) == {"AUDUSD"}
    assert set(result.frame["timeframe"].unique()) == {"H1"}


def test_finnhub_failure_can_fall_back_to_twelve_without_deleting_it(tmp_path: Path):
    calls: list[str] = []

    def finnhub(**kwargs):
        calls.append("FINNHUB")
        raise ProviderPermanentError("Finnhub endpoint unavailable for account plan")

    def twelve(**kwargs):
        calls.append("TWELVE_DATA")
        return _ohlc()

    disabled = lambda **kwargs: (_ for _ in ()).throw(ProviderPermanentError("disabled"))
    orchestrator = MarketDataOrchestrator(
        db_path=tmp_path / "finnhub-fallback.sqlite3",
        quota_manager=_QuotaStub(),
        adapters={
            "FINNHUB": finnhub,
            "TWELVE_DATA": twelve,
            "MT5": disabled,
            "ALPHA_VANTAGE": disabled,
        },
    )
    result = orchestrator.fetch(
        symbol="USDCAD", timeframe="H1",
        state={
            "connector_mode": "finnhub", "finnhub_api_key": "test-key",
            "twelve_api_key": "test-key",
        },
        bars=120, run_id="FINNHUB-FALLBACK", force_live=True,
    )
    assert result.ok is True
    assert result.provider == "TWELVE_DATA"
    assert result.status == "LIVE_FALLBACK"
    assert result.fallback_provider == "TWELVE_DATA"
    assert calls == ["FINNHUB", "TWELVE_DATA"]
    assert set(result.frame["symbol"].unique()) == {"USDCAD"}


def test_order_only_selector_change_reconciles_without_refetch_or_stale_status():
    before = ["AUDUSD", "USDCAD", "USDCHF"]
    after = ["USDCHF", "AUDUSD", "USDCAD"]
    state = {
        LOAD_RECORDS_KEY: {
            "FIRST": {
                "group": "FIRST",
                "timeframe": "H1",
                "requested_symbols": before,
                "loaded_symbols": before,
                "failed_symbols": [],
                "selection_signature": selection_signature(before, "H1"),
                "report": {
                    "requested_symbols": before,
                    "loaded_symbols": before,
                    "unresolved_symbols": [],
                    "results": {symbol: {"ok": True} for symbol in before},
                },
            }
        }
    }
    status = loaded_group_status(state, "FIRST", after, "H1")
    assert status["status"] == "READY"
    assert status["stale"] is False
    assert status["loaded_symbols"] == after
    assert state[LOAD_RECORDS_KEY]["FIRST"]["order_reconciled_without_refetch"] is True


def test_current_field1_alias_and_local_field3_sidecar_satisfy_publication_inputs():
    assert _has_field1({"lunch_metric_result_published_20260618": {"ok": True}})
    summary = pd.DataFrame([
        {"Standard": "Lower Standard", "Decision": "BUY"},
        {"Standard": "Middle Standard", "Decision": "BUY"},
        {"Standard": "Higher Standard", "Decision": "SELL"},
    ])
    details = {
        name: pd.DataFrame([{"Standard": name, "Decision": decision, "Broker Candle": "2026-07-07T10:00:00+00:00"}])
        for name, decision in (
            ("Lower Standard", "BUY"),
            ("Middle Standard", "BUY"),
            ("Higher Standard", "SELL"),
        )
    }
    current, history = _standard_frames({
        "field3_local_symbol_snapshot_20260703": {
            "ok": True, "summary": summary, "details": details,
        }
    }, "2026-07-07T10:00:00+00:00")
    assert set(current) == {"Lower Standard", "Middle Standard", "Higher Standard"}
    assert set(history) == {"Lower Standard", "Middle Standard", "Higher Standard"}
    assert all(not frame.empty for frame in current.values())
    assert all(not frame.empty for frame in history.values())


def test_597_of_600_h1_secondary_child_publishes_with_persisted_local_field3(tmp_path: Path):
    import gzip
    import numpy as np

    from core.child_snapshot_publication_20260706 import publish_complete_child, validate_child_state
    from core.h4_acceptance_workflow_20260706 import _state
    from core.powerbi_child_bundle_20260706 import build_and_store_powerbi_bundle
    from core.runtime_state_cache_20260628 import save_runtime_state
    from core.serialization_compat_20260702 import loads

    rows = 597
    times = pd.date_range("2026-06-01", periods=rows, freq="h", tz="UTC")
    step = np.arange(rows, dtype=float)
    close = 1.10 + step * 0.00001 + np.sin(step / 8.0) * 0.0002
    frame = pd.DataFrame({
        "time": times,
        "open": close - 0.00005,
        "high": close + 0.0002,
        "low": close - 0.0002,
        "close": close,
        "volume": 1000.0 + step,
    })
    parent = "MS-H1-ADAPTIVE-PUBLICATION"
    state = _state("USDCAD", 1, frame, parent, ["AUDUSD", "USDCAD"])
    canonical = state["canonical_decision_result_20260617"]
    canonical.update({
        "run_id": "CANON-USDCAD-H1-001",
        "canonical_calculation_id": "CANON-USDCAD-H1-001",
        "generation_id": "GEN-USDCAD-H1-001",
        "data_signature": "SIG-USDCAD-H1-001",
        "snapshot_hash": "HASH-USDCAD-H1-001",
        "source_id": "OFFLINE-FIXTURE-USDCAD",
        "timeframe": "H1",
        "latest_completed_candle_time": times[-1].isoformat(),
        "completed_broker_candle": times[-1].isoformat(),
        "market": {"latest_completed_candle_time": times[-1].isoformat()},
    })
    state["last_valid_canonical_decision_result_20260617"] = canonical
    state["timeframe"] = state["selected_timeframe"] = "H1"
    for key in (
        "field10_multi_symbol_summary_20260701",
        "field10_daily_higher_regime_20260701",
        "field10_hourly_quality_20260701",
    ):
        state[key]["Timeframe"] = "H1"
        state[key]["Time"] = times[-1].isoformat()
        state[key]["Completed Broker Candle"] = times[-1].isoformat()
        state[key]["Required Candles"] = 600
        state[key]["Available Candles"] = 597

    # Reproduce the former secondary-child path: no global legacy standard
    # tables, only the exact-symbol local Field 3 sidecar calculated from the
    # already activated frame.
    state.pop("regime_standard_detail_tables_published_20260618", None)
    state.pop("field3_regime_lifecycle_monitor_20260701", None)
    standards = ("Lower Standard", "Middle Standard", "Higher Standard")
    state["field3_local_symbol_snapshot_20260703"] = {
        "ok": True,
        "summary": pd.DataFrame([
            {"Standard": name, "Symbol": "USDCAD", "Timeframe": "H1", "Decision": "WAIT"}
            for name in standards
        ]),
        "details": {
            name: pd.DataFrame([{
                "Standard": name, "Symbol": "USDCAD", "Timeframe": "H1",
                "Decision": "WAIT", "Broker Candle": times[-1].isoformat(),
            }])
            for name in standards
        },
    }
    assert build_and_store_powerbi_bundle(state, allow_causal_fallback=True)["ok"] is True

    cache_path = tmp_path / "USDCAD.pkl.gz"
    db_path = tmp_path / "publication.sqlite3"
    save_runtime_state(
        state, status={"ok": True, "status": "COMPLETED"},
        scope="LUNCH_CORE", path=cache_path,
    )
    publication = publish_complete_child(
        state, runtime_snapshot_path=cache_path, db_path=db_path,
    )
    assert publication["ok"] is True
    assert publication["validation"]["validation_mode"] == "ADAPTIVE_PARTIAL_HISTORY"
    assert publication["validation"]["available_candles"] == 597
    assert publication["validation"]["failed_components"] == []

    reloaded = loads(gzip.decompress(cache_path.read_bytes()))["state"]
    validation = validate_child_state(
        reloaded, runtime_snapshot_path=cache_path, db_path=db_path,
    )
    assert validation["ok"] is True
    assert validation["field3_complete"] is True
    assert validation["field10_complete"] is True
    assert validation["failed_components"] == []
