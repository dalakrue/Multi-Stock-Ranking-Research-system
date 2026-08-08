from __future__ import annotations

import importlib
from pathlib import Path
import sys
import types

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _field10_module():
    if "streamlit" not in sys.modules:
        streamlit = types.ModuleType("streamlit")
        streamlit.session_state = {}
        sys.modules["streamlit"] = streamlit
    return importlib.import_module("ui.lunch_field10_multi_symbol_20260701")


def test_consolidated_field10_keeps_every_loaded_exact_symbol(monkeypatch) -> None:
    module = _field10_module()
    symbols = ["AUDUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP"]
    evidence = {
        symbol: {
            "ok": True,
            "rows": 150,
            "required_rows": 150,
            "minimum_rows": 100,
            "calculation_mode": "FULL_HISTORY",
            "provider": "TWELVE_DATA",
            "spacing": {"status": "PASS"},
        }
        for symbol in symbols
    }
    monkeypatch.setattr(module, "_field10_loaded_symbol_contract", lambda state, universe: (symbols, evidence))

    import core.system_continuous_validation_20260702 as validation
    monkeypatch.setattr(
        validation,
        "build_field3_higher_standard_multi_symbol_table",
        lambda state, selected_symbols, parent_run_id=None: (
            pd.DataFrame(
                {
                    "Rank": range(1, 7),
                    "Symbol": symbols,
                    "Higher Standard Regime": ["BEAR_NORMAL", "RANGE_NORMAL", "BULL_NORMAL", "RANGE_NORMAL", "BULL_NORMAL", "RANGE_NORMAL"],
                    "Higher-Standard Bias": ["SELL", "SELL", "BUY", "BUY", "BUY", "BUY"],
                    "Reliability": [65, 61, 59, 57, 55, 53],
                    "Data Quality": ["A", "A", "B", "B", "B", "C"],
                }
            ),
            {"status": "COMPLETE", "symbols": 6},
        ),
    )
    monkeypatch.setattr(
        module,
        "_latest_run_main_table_20260706",
        lambda state, selected_symbols, manifest: (
            pd.DataFrame({"Symbol": symbols[:2], "Final Score": [82.0, 77.0]}),
            {"field10_row_count": 2},
        ),
    )
    import core.field10_daily_snapshot_contract_20260702 as daily_contract
    monkeypatch.setattr(daily_contract, "load_current_daily_snapshot", lambda: {"metadata": {}})
    monkeypatch.setattr(module, "_load_field10_source_frames_20260706", lambda metadata: {})
    monkeypatch.setattr(
        module,
        "_build_visible_four_source_fusion_20260706",
        lambda latest, sources, completion: pd.DataFrame({"Symbol": ["AUDUSD"], "Sentiment Bias": ["SELL"]}),
    )

    table, report = module._build_consolidated_field10_table_20260707(
        {}, {"main_symbol": "AUDUSD", "parent_run_id": "TEST-RUN"}
    )
    assert table["Symbol"].tolist() == symbols
    assert len(table) == 6
    assert set(table["Load Status"]) == {"COMPLETED SNAPSHOT"}
    assert report["row_count"] == 6
    assert report["parent_run_id"] == "TEST-RUN"


def test_secure_startup_is_connection_only_with_fixed_three_minute_guard() -> None:
    from core.secure_api_startup_20260619 import initialize_secure_settings

    state = {
        "use_secure_api_keys_20260619": False,
        "auto_connect_after_login_20260619": False,
        "auto_calculate_new_h1_20260619": True,
        "open_lunch_after_auto_run_20260619": True,
        "auto_run_cooldown_minutes_20260619": 19,
    }
    initialize_secure_settings(state)
    assert state["use_secure_api_keys_20260619"] is True
    assert state["auto_connect_after_login_20260619"] is True
    assert state["auto_calculate_new_h1_20260619"] is False
    assert state["open_lunch_after_auto_run_20260619"] is False
    assert state["auto_run_cooldown_minutes_20260619"] == 3


def test_legacy_field10_surfaces_are_not_called_by_visible_pages() -> None:
    field10 = (ROOT / "ui" / "lunch_field10_multi_symbol_20260701.py").read_text(encoding="utf-8")
    visible = field10[field10.index("def render_field10_content"):field10.index("def _field10_part4_diagnostic_table")]
    assert "_render_field10_three_sections_20260706(state)" not in visible
    assert "_render_locked_morning_snapshot" not in visible
    assert visible.count("with st.expander(") == 1

    lunch = (ROOT / "ui" / "lunch_four_core_fields_20260619.py").read_text(encoding="utf-8")
    final_lunch = (ROOT / "tabs" / "final_lunch_upgrade_20260617.py").read_text(encoding="utf-8")
    dinner = (ROOT / "tabs" / "field456789_page_20260626.py").read_text(encoding="utf-8")
    assert "_render_lunch_search_box(state)" not in lunch
    assert "render_lunch_search(st.session_state)" not in final_lunch
    assert "_render_field10_part4()" not in dinner[dinner.index("def show"):]
