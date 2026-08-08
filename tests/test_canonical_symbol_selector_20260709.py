from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from core.canonical_symbol_selection_20260709 import available_symbols, activate_symbol, active_symbol, filter_frame_for_symbol


def _state() -> dict:
    ranking = pd.DataFrame([
        {"Rank": 1, "Symbol": "AUDUSD", "Entry permission": "WAIT", "InstitutionalUtility": 0.1, "Data quality grade": "A"},
        {"Rank": 2, "Symbol": "USDCAD", "Entry permission": "TRADE CANDIDATE", "InstitutionalUtility": 0.2, "Data quality grade": "A"},
    ])
    return {
        "canonical_run_identity_20260708": {"canonical_symbols": ["AUDUSD", "USDCAD", "AUDUSD"]},
        "field10_institutional_ranking_20260708": ranking,
        "field11_similar_path_multisymbol_20260708": pd.DataFrame([
            {"Symbol": "AUDUSD", "Horizon": "1H", "Endpoint P50": 0.1},
            {"Symbol": "USDCAD", "Horizon": "1H", "Endpoint P50": 0.2},
        ]),
    }


def test_available_symbols_prefers_canonical_order_and_deduplicates() -> None:
    assert available_symbols(_state()) == ["AUDUSD", "USDCAD"]


def test_activate_symbol_updates_all_display_keys_without_child_publication() -> None:
    state = _state()
    report = activate_symbol(state, "USDCAD", surface="field2", try_legacy=False)
    assert report["ok"] is True
    assert report["status"] == "CANONICAL_SYMBOL_LOADED"
    assert active_symbol(state, surface="field2") == "USDCAD"
    assert state["lunch_active_symbol_20260704"] == "USDCAD"
    assert state["field2_selected_symbol_20260709"] == "USDCAD"


def test_filter_frame_for_symbol_changes_field_view() -> None:
    state = _state()
    frame = state["field11_similar_path_multisymbol_20260708"]
    view = filter_frame_for_symbol(frame, "USDCAD")
    assert len(view) == 1
    assert view.iloc[0]["Endpoint P50"] == 0.2


def test_loaded_symbols_are_only_selectable_universe() -> None:
    state = {
        "canonical_loaded_symbols": ["USDJPY", "AUDUSD"],
        "canonical_selected_symbols": ["EURUSD", "USDJPY", "AUDUSD", "GBPUSD"],
        "field10_institutional_ranking_20260708": pd.DataFrame([
            {"Symbol": "EURUSD", "Candle count": 0, "Entry permission": "BLOCKED"},
            {"Symbol": "USDJPY", "Candle count": 500, "Entry permission": "TRADE CANDIDATE"},
            {"Symbol": "AUDUSD", "Candle count": 500, "Entry permission": "WAIT"},
        ]),
    }
    assert available_symbols(state) == ["USDJPY", "AUDUSD"]


def test_global_activation_overrides_stale_surface_and_propagates_every_tab() -> None:
    state = _state()
    state["canonical_loaded_symbols"] = ["AUDUSD", "USDCAD"]
    state["research_canonical_symbol_20260709"] = "AUDUSD"
    report = activate_symbol(state, "USDCAD", surface="settings_global", try_legacy=False)
    assert report["ok"] is True
    assert active_symbol(state, surface="research") == "USDCAD"
    assert state["symbol"] == "USDCAD"
    for key in (
        "field3_canonical_symbol_20260709", "field10_canonical_symbol_20260709",
        "field12_canonical_symbol_20260709", "field13_canonical_symbol_20260709",
        "research_canonical_symbol_20260709", "ai_canonical_symbol_20260709",
    ):
        assert state[key] == "USDCAD"
