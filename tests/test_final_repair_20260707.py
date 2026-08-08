from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd


def _ohlc(rows: int, *, timeframe_hours: int = 4, end_hour: int = 12) -> pd.DataFrame:
    end = datetime(2026, 7, 6, end_hour, tzinfo=timezone.utc)
    stamps = [end - timedelta(hours=timeframe_hours * (rows - 1 - index)) for index in range(rows)]
    return pd.DataFrame(
        {
            "open_time": stamps,
            "open": [1.0] * rows,
            "high": [1.1] * rows,
            "low": [0.9] * rows,
            "close": [1.02] * rows,
            "volume": [100.0] * rows,
        }
    )


def test_exact_symbol_cache_is_admitted_but_cross_symbol_cache_is_rejected() -> None:
    from core.multi_symbol_load_manager_20260707 import _validate_result

    exact = _validate_result(
        {
            "ok": False,
            "symbol": "EURUSD",
            "timeframe": "H4",
            "provider": "LOCAL_VALID_CACHE",
            "validation_status": "CACHED_VALID",
            "frame": _ohlc(160),
        },
        symbol="EURUSD",
        timeframe="h4",
        required_rows=150,
    )
    assert exact["ok"] is True
    assert exact["trusted_exact_cache"] is True
    assert exact["reason"] == "READY"

    wrong_symbol = _validate_result(
        {
            "ok": True,
            "symbol": "USDJPY",
            "timeframe": "H4",
            "provider": "LOCAL_VALID_CACHE",
            "validation_status": "CACHED_VALID",
            "frame": _ohlc(160),
        },
        symbol="EURUSD",
        timeframe="H4",
        required_rows=150,
    )
    assert wrong_symbol["ok"] is False
    assert wrong_symbol["exact_identity"] is False
    assert wrong_symbol["reason"].startswith("IDENTITY_MISMATCH")


def test_field3_nested_dataframe_publication_is_recognized() -> None:
    from core.child_snapshot_publication_20260706 import _has_field3

    state = {
        "regime_standard_detail_tables_published_20260618": {
            "higher": pd.DataFrame({"Symbol": ["EURUSD"], "Bias": ["BUY"]})
        }
    }
    assert _has_field3(state) is True
    assert _has_field3({"regime_standard_detail_tables_published_20260618": {"status": "UNAVAILABLE"}}) is False


def test_powerbi_production_main_path_passes_validation() -> None:
    from core.powerbi_child_bundle_20260706 import validate_powerbi_bundle

    bundle = {
        "symbol": "AUDUSD",
        "timeframe": "H1",
        "run_id": "RUN-1",
        "generation_id": "GEN-1",
        "snapshot_hash": "hash",
        "completed_broker_candle": "2026-07-06T11:00:00+00:00",
        "source_id": "source",
        "main": pd.DataFrame(
            {
                "time": pd.date_range("2026-07-06T12:00:00Z", periods=3, freq="h"),
                "prediction": [1.0, 1.1, 1.2],
            }
        ),
    }
    result = validate_powerbi_bundle(bundle, symbol="AUDUSD", timeframe="H1")
    assert result == {
        "ok": True,
        "status": "PASS",
        "missing": [],
        "exact_symbol_timeframe": True,
        "has_path": True,
    }

    # A DataFrame stored under another supported path key must not trigger
    # pandas' ambiguous truth-value exception.
    bundle["main"] = pd.DataFrame()
    bundle["future_path"] = pd.DataFrame({"time": ["2026-07-06T12:00:00Z"], "price": [1.1]})
    result = validate_powerbi_bundle(bundle, symbol="AUDUSD", timeframe="H1")
    assert result["ok"] is True
    assert result["has_path"] is True


def test_powerbi_uses_exact_canonical_candle_not_fresher_alias() -> None:
    import types

    if "streamlit" not in sys.modules:
        streamlit_stub = types.ModuleType("streamlit")
        streamlit_stub.fragment = lambda fn: fn
        streamlit_stub.session_state = {}
        sys.modules["streamlit"] = streamlit_stub
    from ui.powerbi_cached_renderer_20260619 import _select_market_for_canonical

    canonical = {"completed_broker_candle": "2026-07-06T11:00:00+00:00"}
    exact = _ohlc(10, timeframe_hours=1, end_hour=11)
    stale_or_future = _ohlc(10, timeframe_hours=1, end_hour=15)
    state = {
        "canonical_completed_ohlc_df_20260617": exact,
        "last_df": stale_or_future,
    }
    selected, notes = _select_market_for_canonical(state, canonical)
    assert not selected.empty
    assert pd.to_datetime(selected["time"], utc=True).max() == pd.Timestamp("2026-07-06T11:00:00Z")
    assert any("exact canonical candle" in note for note in notes)


def test_field10_row_contract_rejects_insufficient_history_and_accepts_complete_rows() -> None:
    from core.multi_symbol_completion_contract_20260706 import _usable_field10_rows

    incomplete = pd.DataFrame(
        {
            "Symbol": ["AUDUSD", "EURGBP"],
            "Rank": [1, 2],
            "Higher-Standard Bias": ["SELL", "BUY"],
            "Data Quality": ["D", "B"],
            "Reliability Score": ["INSUFFICIENT LOCAL HISTORY", 54.64],
        }
    )
    usable, reasons = _usable_field10_rows(incomplete, ["AUDUSD", "EURGBP"])
    assert usable["AUDUSD"] is False
    assert usable["EURGBP"] is True
    assert reasons["AUDUSD"]

    complete = incomplete.copy()
    complete.loc[0, "Reliability Score"] = 51.9
    usable, reasons = _usable_field10_rows(complete, ["AUDUSD", "EURGBP"])
    assert usable == {"AUDUSD": True, "EURGBP": True}
    assert reasons == {"AUDUSD": [], "EURGBP": []}


def test_consolidated_field10_surface_and_strict_progress_are_present() -> None:
    source = Path("ui/lunch_field10_multi_symbol_20260701.py").read_text(encoding="utf-8")
    render = source[source.index("def render_field10_content"):]
    assert "Field 3 Higher-Standard Multi-Symbol Bias + Consolidated Field 10 — All Loaded Settings Symbols" in render
    assert "_build_consolidated_field10_table_20260707" in render
    assert "field10_consolidated_exact_symbol_table_20260707" in render
    assert "_render_consolidated_field10_visual_20260707" in render
    assert "_render_field10_three_sections_20260706(state)" not in render
    assert "progress_percent\": 100.0 if ok else 99.0" in Path(
        "core/multi_symbol_completion_contract_20260706.py"
    ).read_text(encoding="utf-8")
