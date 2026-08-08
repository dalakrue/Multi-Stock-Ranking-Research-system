from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import core.system_continuous_validation_20260702 as validator
from core.buy_sell_frequency_20260629 import enrich_bfd_sfd
from core.field10_adaptive_regime_metrics_20260702 import compute_adaptive_regime_metrics
from ui.lunch_field2_saved_path_v13 import build_ohlc_fallback_projection


def _ohlc(symbol_seed: int, rows: int = 900, direction: float = 1.0) -> pd.DataFrame:
    rng = np.random.default_rng(symbol_seed)
    time = pd.date_range("2026-05-01", periods=rows, freq="h", tz="UTC")
    noise = rng.normal(0.0, 0.00022 + symbol_seed * 0.000005, rows)
    cyc = 0.00016 * np.sin(np.arange(rows) / (7.0 + symbol_seed))
    returns = direction * (0.000025 + symbol_seed * 0.000001) + cyc + noise
    close = 1.0 + np.cumsum(returns)
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) + 0.00025
    low = np.minimum(open_, close) - 0.00025
    return pd.DataFrame({"time": time, "open": open_, "high": high, "low": low, "close": close, "volume": 1000 + np.arange(rows)})


def test_ordered_multi_selector_replaces_legacy_single_symbol_ui():
    settings = Path("ui/multi_symbol_settings_20260701.py").read_text(encoding="utf-8")
    fallback = Path("ui/sidebar_fallback_panel.py").read_text(encoding="utf-8")
    facade = Path("ui/global_symbol_selector_20260629.py").read_text(encoding="utf-8")
    assert "first selected = Main Core Symbol" in settings
    assert "st.multiselect" in settings
    assert "Instrument library" not in settings
    assert "Type symbol" not in settings
    assert "show_symbol_selector: bool = False" in fallback
    assert "render_multi_symbol_selector" in facade


def test_field10_adaptive_metrics_are_complete_and_symbol_specific():
    buy = compute_adaptive_regime_metrics(_ohlc(2, direction=1.0))
    sell = compute_adaptive_regime_metrics(_ohlc(8, direction=-1.0))
    assert buy["ok"] and sell["ok"]
    required = (
        "regime_probability", "regime_entropy", "posterior_margin", "regime_age",
        "expected_regime_duration", "estimated_remaining_duration", "transition_risk_1h",
        "transition_risk_3h", "transition_risk_6h", "calibrated_bias_probability",
        "brier_score", "forecast_accuracy_1h", "forecast_accuracy_3h", "forecast_accuracy_6h",
    )
    for payload in (buy, sell):
        assert payload["bias"] in {"BUY", "SELL"}
        assert all(payload[key] is not None for key in required)
        assert payload["transition_risk_1h"] < payload["transition_risk_3h"] < payload["transition_risk_6h"]
    varying = sum(buy[key] != sell[key] for key in required)
    assert varying >= 10


def test_field10_display_overlay_fills_wait_and_missing_values(monkeypatch):
    states = {
        "GBPUSD": {"data": _ohlc(3, direction=1.0), "higher_standard_bias": "BUY"},
        "USDJPY": {"data": _ohlc(6, direction=-1.0), "higher_standard_bias": "SELL"},
    }
    monkeypatch.setattr(validator, "_cached_symbol_state", lambda symbol: states[symbol])
    current = pd.DataFrame([
        {"Symbol": "GBPUSD", "Stable Daily Bias": "WAIT", "Less-Risky Bias": "WAIT", "Entry Permission": "BLOCKED", "Safety Veto": "CLEAR"},
        {"Symbol": "USDJPY", "Stable Daily Bias": "WAIT", "Less-Risky Bias": "WAIT", "Entry Permission": "NO TRADE", "Safety Veto": "CLEAR"},
    ])
    repaired, report = validator.build_field10_display_overlay(current)
    assert report["ok"] and report["repaired_rows"] == 2
    repaired_by_symbol = repaired.set_index("Symbol")
    assert repaired_by_symbol.loc["GBPUSD", "Stable Daily Bias"] == "BUY"
    assert repaired_by_symbol.loc["USDJPY", "Stable Daily Bias"] == "SELL"
    assert repaired_by_symbol.loc["GBPUSD", "Less-Risky Bias"] == "BUY"
    assert repaired_by_symbol.loc["USDJPY", "Less-Risky Bias"] == "SELL"
    assert set(repaired["Entry Permission"].tolist()) == {"CAUTION"}
    assert repaired["Regime Probability"].notna().all()
    assert repaired["Forecast Accuracy 6H"].notna().all()
    assert set(repaired["Stored Stable Daily Bias"].tolist()) == {"WAIT"}


def test_field10_priority_view_adds_every_selected_symbol_and_has_no_blank_cells(monkeypatch):
    states = {
        "EURUSD": {"data": _ohlc(2, direction=1.0), "higher_standard_bias": "BUY"},
        "GBPUSD": {"data": _ohlc(5, direction=-1.0), "higher_standard_bias": "SELL"},
        "USDJPY": {},
    }
    monkeypatch.setattr(validator, "_cached_symbol_state", lambda symbol: states.get(symbol, {}))
    immutable = pd.DataFrame([{
        "Symbol": "EURUSD",
        "Daily Rank": pd.NA,
        "Stable Daily Bias": "WAIT",
        "Higher-Standard Bias": "BUY",
        "Less-Risky Bias": pd.NA,
        "Entry Permission": "BLOCKED",
        "Safety Veto": "CLEAR",
        "Explanation": "UNAVAILABLE",
    }])
    original = immutable.copy(deep=True)
    selected = ["EURUSD", "GBPUSD", "USDJPY"]

    view, report = validator.build_field10_display_overlay(immutable, selected)

    assert immutable.equals(original), "immutable publication must not be changed"
    assert report["ok"]
    assert report["all_rows_ranked"]
    assert report["all_visible_cells_explicit"]
    assert report["missing_selected_symbols"] == []
    assert set(view["Symbol"].tolist()) == set(selected)
    assert view["Rank"].tolist() == [1, 2, 3]
    assert view["Rank"].notna().all()
    assert view["Higher-Standard Bias"].astype(str).str.len().gt(0).all()
    assert view["Snapshot Status"].astype(str).str.len().gt(0).all()
    flattened = " ".join(view.astype(str).to_numpy().ravel()).upper()
    assert "N/A" not in flattened
    assert "UNAVAILABLE" not in flattened
    assert not any(report["blank_all_visible_cells"].values())


def test_powerbi_fallback_is_non_empty_for_non_eurusd_symbols():
    for symbol, seed in (("GBPUSD", 2), ("USDCAD", 7), ("USDJPY", 11)):
        market = _ohlc(seed, rows=400, direction=1.0 if seed % 2 else -1.0)
        canonical = {
            "symbol": symbol,
            "timeframe": "H1",
            "run_id": f"RUN-{symbol}",
            "generation_id": f"GEN-{symbol}",
            "completed_broker_candle": market["time"].iloc[-1].isoformat(),
            "snapshot_hash": f"HASH-{symbol}",
        }
        bundle, future, meta = build_ohlc_fallback_projection(market, canonical)
        assert meta["ok"] and meta["fallback_projection"]
        assert bundle["ok"] and len(bundle["main"]) == 6
        assert len(future) == 6
        main = bundle["main"]
        assert (main["upper_band"] > main["main_path"]).all()
        assert (main["lower_band"] < main["main_path"]).all()
        assert bundle["summary"]["path_source"] == "ACTIVE_SYMBOL_OHLC_CAUSAL_FALLBACK"


def test_post_run_navigation_and_live_session_are_wired():
    router = Path("tabs/antd_page_router_20260615.py").read_text(encoding="utf-8")
    session = Path("core/session_context_20260625.py").read_text(encoding="utf-8")
    lunch = Path("ui/lunch_four_core_fields_20260619.py").read_text(encoding="utf-8")
    assert '"lunch_active_field_selector_20260624": "1. Open / Close — Full Metric 25-Day History + Decision Tables"' in router
    assert '"lunch_field_open_1_20260621": True' in router
    assert '"lunch_field_open_2_20260621": False' in router
    assert '"lunch_field_open_3_20260621": False' in router
    assert "pd.Timestamp.now(tz='UTC')" in session
    assert "AUTO_FROM_CURRENT_UTC_TIME" in session
    assert "Current Session Time" in lunch
    assert "validate_and_repair_state(state)" in lunch


def test_bfd_sfd_distribution_is_not_forced_to_no_trade():
    frame = pd.DataFrame({
        "Decision": ["BUY"] * 8 + ["SELL"] * 2,
        "BUY Pressure": [8.0] * 10,
        "SELL Pressure": [2.0] * 10,
    })
    result = enrich_bfd_sfd(frame)
    assert not result.empty
    assert {"BFD", "SFD"}.issubset(result.columns)
    assert (result["BFD"].astype(str) != "No Trade").any()


def test_field11_has_cache_repair_and_non_eurusd_support_paths():
    source = Path("core/field11_similar_path_simulator_20260702.py").read_text(encoding="utf-8")
    ui = Path("ui/lunch_field11_similar_path_20260702.py").read_text(encoding="utf-8")
    assert "CACHE_REPAIRED" in source
    assert "available_saved_symbols" in source
    assert "for symbol in universe" in source
    assert "prepare_field11_index" in ui
    assert "MT5/APIs" in ui and "available_saved_symbols" in ui
