"""Lunch Field 13 — relabelled companion-project Field 3 surface."""
from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, Callable

import streamlit as st


FIELD13_LABEL = "13. Open / Close — Regime Lifecycle and Three-Standards Evidence"


def _safe(state: MutableMapping[str, Any], name: str, label: str, render: Callable[[], Any]) -> None:
    """Keep one optional visual component from taking down the whole Lunch tab."""
    try:
        render()
    except Exception as exc:
        state[f"field13_{name}_error_20260717"] = f"{type(exc).__name__}: {exc}"
        st.warning(f"{label} was unavailable: {type(exc).__name__}: {exc}")


def render_field13(state: MutableMapping[str, Any] | None = None) -> None:
    """Render the companion Field 3 logic as a read-only Field 13 surface."""
    state = state if state is not None else st.session_state
    st.markdown("## Field 13 — Regime Lifecycle and Three-Standards Evidence")
    st.caption(
        "Field 13 is the read-only Field 3 lifecycle companion. Lower, Middle and "
        "Higher standards, lifecycle duration, posterior trust and switch-risk "
        "evidence remain tied to the selected loaded symbol and completed generation."
    )
    try:
        from core.canonical_symbol_selection_20260709 import render_selector
        selected_symbol, _, _ = render_selector(
            st, state, surface="field13",
            title="Field 13 Loaded-Symbol Selector — Regime Lifecycle Evidence",
            expanded=True,
        )
        st.caption(f"Field 13 is displaying the saved regime evidence for {selected_symbol}.")
    except Exception as selector_exc:
        state["field13_selector_error_20260722"] = f"{type(selector_exc).__name__}: {selector_exc}"

    from ui.lunch_four_core_fields_20260619 import (
        _canonical,
        _render_evidence,
        _render_regime_history,
        _render_regime_lifecycle,
    )

    canonical = _canonical(state)
    _safe(
        state,
        "lifecycle_monitor",
        "Saved Field 3 lifecycle monitor",
        lambda: _render_monitor(state, canonical),
    )
    _safe(
        state,
        "one_hour_compatibility",
        "One-hour regime compatibility",
        lambda: _render_one_hour(state),
    )
    _safe(
        state,
        "priority_sync",
        "Priority synchronization",
        lambda: _render_priority_sync(state),
    )
    try:
        import pandas as pd
        has_multi = isinstance(state.get("field3_multisymbol_regime_20260708"), pd.DataFrame) and not state.get("field3_multisymbol_regime_20260708").empty
    except Exception:
        has_multi = False
    if not has_multi:
        _safe(state, "current_lifecycle", "Current regime lifecycle", lambda: _render_regime_lifecycle(canonical))
    _safe(state, "history", "Selected-symbol regime history", lambda: _render_regime_history(state))
    _safe(state, "evidence", "Field 3 evidence", lambda: _render_evidence("FIELD_3", state, "field13"))


def _render_monitor(state: MutableMapping[str, Any], canonical: Any) -> None:
    from ui.lunch_field3_regime_lifecycle_monitor_20260701 import render_field3_regime_lifecycle_monitor
    render_field3_regime_lifecycle_monitor(state, canonical)


def _render_one_hour(state: MutableMapping[str, Any]) -> None:
    from ui.lunch_one_hour_direction_20260626 import render_for_field
    render_for_field(state, 3)


def _render_priority_sync(state: MutableMapping[str, Any]) -> None:
    from ui.priority_sync_v9 import render_priority_sync_v9
    render_priority_sync_v9(state)


__all__ = ["FIELD13_LABEL", "render_field13"]
