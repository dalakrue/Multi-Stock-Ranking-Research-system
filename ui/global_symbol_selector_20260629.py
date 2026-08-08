"""Backward-compatible facade for the ordered Multi-Symbol Selector.

The removed single-symbol library/text-input UI must never reappear through an
older Home/sidebar import.  Existing callers still receive the Main Core Symbol.
"""
from __future__ import annotations

from typing import Any, MutableMapping


def render_global_symbol_selector(
    state: MutableMapping[str, Any],
    *,
    key_prefix: str,
    auto_refresh_library: bool = True,
    show_refresh_status: bool = True,
) -> str:
    del key_prefix, auto_refresh_library
    import streamlit as st
    from ui.multi_symbol_settings_20260701 import render_multi_symbol_selector, normalize_symbol

    selected = render_multi_symbol_selector(state)
    main = normalize_symbol(selected[0] if selected else state.get("multi_symbol_main_symbol_20260702") or state.get("symbol") or "EURUSD")
    state["multi_symbol_main_symbol_20260702"] = main
    state["connector_symbol_20260702"] = main
    state["symbol"] = main
    if show_refresh_status:
        refresh = state.get("last_refresh_result_20260621")
        if isinstance(refresh, dict):
            st.caption(
                f"Latest Main Core refresh: {refresh.get('status', 'NOT RUN')} · "
                f"source={refresh.get('source', state.get('source', 'DISCONNECTED'))} · "
                f"rows={(refresh.get('quality') or {}).get('rows', state.get('last_connection_rows', 0)) if isinstance(refresh.get('quality'), dict) else state.get('last_connection_rows', 0)}"
            )
    return main


__all__ = ["render_global_symbol_selector"]
