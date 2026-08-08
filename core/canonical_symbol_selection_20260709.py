"""Canonical display-symbol selection for every ADX Quant Pro tab.

This fixes the old failure mode where a per-field selector depended only on a
complete child publication.  The selector now prefers the institutional
canonical snapshot and gracefully falls back to legacy child restore when that
snapshot exists.  Selecting/loading a symbol always changes the display symbol
for the current surface; it never silently falls back to the old active symbol.
"""
from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any
import time

import pandas as pd

GLOBAL_SYMBOL_KEY = "canonical_display_symbol_20260709"
STATUS_KEY = "canonical_symbol_load_status_20260709"
FIELD_WIDGET_KEY = "canonical_symbol_widget_20260709"
HORIZON_KEY = "canonical_horizon_20260709"

SURFACE_SYMBOL_KEYS = {
    "lunch": "lunch_canonical_symbol_20260709",
    "field1": "field1_canonical_symbol_20260709",
    "field2": "field2_canonical_symbol_20260709",
    "field3": "field3_canonical_symbol_20260709",
    "field10": "field10_canonical_symbol_20260709",
    "field11": "field11_canonical_symbol_20260709",
    "morning": "morning_canonical_symbol_20260709",
    "dinner": "dinner_canonical_symbol_20260709",
    "research": "research_canonical_symbol_20260709",
    "finder": "finder_canonical_symbol_20260709",
    "ai": "ai_canonical_symbol_20260709",
    "settings_global": "settings_global_canonical_symbol_20260709",
    "field12": "field12_canonical_symbol_20260709",
    "field13": "field13_canonical_symbol_20260709",
}

DISPLAY_COMPAT_KEYS = (
    "lunch_active_symbol_20260704",
    "canonical_display_symbol_20260705",
    "lunch_display_symbol_20260702",
    "active_snapshot_symbol_20260702",
    "field10_active_symbol_20260702",
    "field10_active_symbol_widget_20260702",
    "field11_symbol_sync_pending_20260702",
    "active_symbol",
)


def normalize_symbol(value: Any) -> str:
    return str(value or "").strip().upper().replace("/", "").replace("_", "").replace(" ", "")


def _ordered_unique(values: Sequence[Any] | Any, *, limit: int = 30) -> list[str]:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, Sequence):
        return []
    out: list[str] = []
    for value in values:
        s = normalize_symbol(value)
        if s and s not in out:
            out.append(s)
        if len(out) >= limit:
            break
    return out


def _symbols_from_frame(frame: Any) -> list[str]:
    if isinstance(frame, pd.DataFrame) and not frame.empty and "Symbol" in frame.columns:
        return _ordered_unique(frame["Symbol"].dropna().astype(str).tolist(), limit=30)
    return []


def available_symbols(state: Mapping[str, Any] | None, *, limit: int = 30) -> list[str]:
    """Return only symbols with a completed loaded/saved evidence payload.

    Settings selections are intentionally excluded until the load manager has
    validated them. This prevents default/configured symbols from appearing in
    tab selectors before their own data is available.
    """
    state = state if isinstance(state, Mapping) else {}
    loaded: list[Any] = []
    for key in ("canonical_loaded_symbols", "canonical_loaded_symbols_20260705", "calculation_loaded_symbols_20260708"):
        value = state.get(key)
        if isinstance(value, str):
            loaded.append(value)
        elif isinstance(value, Sequence):
            loaded.extend(list(value))
    load_record = state.get("canonical_symbol_load_record_20260708")
    if isinstance(load_record, Mapping):
        for key in ("loaded_symbols", "completed_symbols", "symbols"):
            value = load_record.get(key)
            if isinstance(value, str):
                loaded.append(value)
            elif isinstance(value, Sequence):
                loaded.extend(list(value))
    identity = state.get("canonical_run_identity_20260708")
    if isinstance(identity, Mapping):
        value = identity.get("loaded_symbols")
        if isinstance(value, str):
            loaded.append(value)
        elif isinstance(value, Sequence):
            loaded.extend(list(value))
    authoritative = _ordered_unique(loaded, limit=limit)
    if authoritative:
        return authoritative

    # Durable-generation fallback: a validated saved ranking is itself evidence
    # that the symbol was loaded previously. Exclude explicitly missing/blocked
    # rows when the ranking contains data-quality columns.
    for key in (
        "field10_institutional_ranking_20260708",
        "field3_multisymbol_regime_20260708",
        "field1_canonical_multisymbol_summary_20260708",
        "field2_canonical_projection_20260708",
        "field11_similar_path_multisymbol_20260708",
        "field12_fundamental_nlp_rank_20260722",
        "field10_current_table_20260701",
        "multi_symbol_field10_summary_20260701",
    ):
        frame = state.get(key)
        if not isinstance(frame, pd.DataFrame) or frame.empty or "Symbol" not in frame.columns:
            continue
        usable = frame.copy()
        if "Candle count" in usable.columns:
            usable = usable.loc[pd.to_numeric(usable["Candle count"], errors="coerce").fillna(0).ge(25)]
        elif "Entry permission" in usable.columns:
            usable = usable.loc[~usable["Entry permission"].astype(str).str.upper().isin({"BLOCKED", "BLOCK_NO_DATA"})]
        authoritative.extend(_symbols_from_frame(usable))
    return _ordered_unique(authoritative, limit=limit)


def active_symbol(state: Mapping[str, Any] | None, *, surface: str = "lunch") -> str:
    state = state if isinstance(state, Mapping) else {}
    symbols = available_symbols(state)
    candidates = [
        state.get(GLOBAL_SYMBOL_KEY),
        state.get(SURFACE_SYMBOL_KEYS.get(surface, "")),
        state.get("selected_symbol_for_display_20260709"),
        state.get("lunch_active_symbol_20260704"),
        state.get("canonical_display_symbol_20260705"),
        state.get("lunch_display_symbol_20260702"),
        state.get("active_symbol"),
        state.get("symbol"),
    ]
    for value in candidates:
        s = normalize_symbol(value)
        if s and (not symbols or s in symbols):
            return s
    return symbols[0] if symbols else ""


def _field10_row(state: Mapping[str, Any], symbol: str) -> dict[str, Any]:
    sym = normalize_symbol(symbol)
    for key in ("field10_institutional_ranking_20260708", "field10_current_table_20260701", "multi_symbol_field10_summary_20260701"):
        frame = state.get(key)
        if isinstance(frame, pd.DataFrame) and not frame.empty and "Symbol" in frame.columns:
            match = frame.loc[frame["Symbol"].astype(str).map(normalize_symbol).eq(sym)]
            if not match.empty:
                return dict(match.iloc[0])
    return {}


def filter_frame_for_symbol(frame: Any, symbol: str, *, symbol_col: str = "Symbol") -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.DataFrame()
    if symbol_col not in frame.columns:
        return frame.copy()
    sym = normalize_symbol(symbol)
    return frame.loc[frame[symbol_col].astype(str).map(normalize_symbol).eq(sym)].copy()


def activate_symbol(state: MutableMapping[str, Any], symbol: Any, *, surface: str = "lunch", try_legacy: bool = True) -> dict[str, Any]:
    sym = normalize_symbol(symbol)
    symbols = available_symbols(state)
    if not sym:
        sym = symbols[0] if symbols else ""
    if not sym:
        report = {"ok": False, "status": "NO_CANONICAL_SYMBOLS", "symbol": "", "processed_at": time.time()}
        state[STATUS_KEY] = report
        return report
    if symbols and sym not in symbols:
        report = {"ok": False, "status": "SYMBOL_NOT_IN_CANONICAL_UNIVERSE", "symbol": sym, "available_symbols": symbols, "processed_at": time.time()}
        state[STATUS_KEY] = report
        return report

    surface_key = SURFACE_SYMBOL_KEYS.get(surface, f"{surface}_canonical_symbol_20260709")
    state[GLOBAL_SYMBOL_KEY] = sym
    # One selection is authoritative for every tab. Surface keys are mirrors,
    # never independent overrides. Pending widget resets are consumed before
    # each tab creates its selectbox, avoiding Streamlit widget-state errors.
    for surface_name, key_name in SURFACE_SYMBOL_KEYS.items():
        state[key_name] = sym
        if surface_name != surface:
            state[f"canonical_symbol_widget_pending_20260709_{surface_name}"] = sym
    state[surface_key] = sym
    for key in DISPLAY_COMPAT_KEYS:
        state[key] = sym
    # Some legacy tabs still read these generic keys. They now follow the same
    # display authority, while connector/settings-main keys remain untouched.
    state["symbol"] = sym
    state["selected_symbol"] = sym
    # Do not overwrite Settings main connector symbol, but make all display and
    # copy/export surfaces read the selected symbol first.
    state["selected_symbol_for_display_20260709"] = sym
    state["field1_selected_symbol_20260709"] = sym
    state["field2_selected_symbol_20260709"] = sym
    state["field3_selected_symbol_20260709"] = sym
    state["field10_selected_symbol_20260709"] = sym
    state["field11_selected_symbol_20260709"] = sym
    state.pop("field11_last_result_20260702", None)
    state.pop("direct_current_copy_payloads_20260702_v3", None)
    state.pop("copy_payload_cache_short_20260702", None)
    state.pop("copy_payload_cache_full_20260702", None)

    legacy_status = "NOT_ATTEMPTED"
    if try_legacy:
        try:
            from core.multi_symbol_field10_20260701 import activate_symbol_view
            legacy_report = activate_symbol_view(state, sym)
            legacy_status = str(legacy_report.get("status") or "LEGACY_OK") if isinstance(legacy_report, Mapping) and legacy_report.get("ok") else str((legacy_report or {}).get("status") or "LEGACY_DEGRADED")
        except Exception as exc:
            legacy_status = f"LEGACY_SKIPPED_{type(exc).__name__}"

    row = _field10_row(state, sym)
    status = "CANONICAL_SYMBOL_LOADED"
    ok = True
    if not row:
        status = "CANONICAL_SYMBOL_SELECTED_NO_RANK_ROW"
    report = {
        "ok": ok,
        "status": status,
        "symbol": sym,
        "surface": surface,
        "rank": row.get("Rank", "—"),
        "entry_permission": row.get("Entry permission", row.get("Calculation Status", "READY")),
        "data_quality_grade": row.get("Data quality grade", "—"),
        "provider_used": row.get("Provider used", row.get("Data Source", "canonical snapshot")),
        "broker_candle_time": row.get("Broker Candle Time", row.get("Completed Broker Candle", "—")),
        "legacy_restore_status": legacy_status,
        "processed_at": time.time(),
        "heavy_calculation_triggered": False,
    }
    state[STATUS_KEY] = report
    state[f"{surface}_symbol_load_status_20260709"] = report
    if try_legacy:
        try:
            from core.data.deployment_migrations_20260705 import DEFAULT_DB_PATH
            from core.runtime_selection_20260705 import save_active_display_symbol
            save_active_display_symbol(DEFAULT_DB_PATH, sym)
        except Exception as exc:
            state["canonical_display_symbol_persist_warning_20260722"] = f"{type(exc).__name__}: {exc}"
    return report


def render_selector(
    st: Any,
    state: MutableMapping[str, Any],
    *,
    surface: str,
    title: str = "Multi-Symbol Selector",
    show_horizon: bool = False,
    expanded: bool = True,
) -> tuple[str, str | None, dict[str, Any]]:
    symbols = available_symbols(state)
    current = active_symbol(state, surface=surface)
    if not current and symbols:
        current = symbols[0]
        activate_symbol(state, current, surface=surface, try_legacy=False)
    if not symbols:
        st.warning("No canonical multi-symbol snapshot is available. Run Settings calculation after loading symbols.")
        return "", None, {"ok": False, "status": "NO_CANONICAL_SYMBOLS"}
    key = f"{FIELD_WIDGET_KEY}_{surface}"
    pending_key = f"canonical_symbol_widget_pending_20260709_{surface}"
    pending = normalize_symbol(state.pop(pending_key, ""))
    if pending in symbols:
        state[key] = pending
    elif key not in state or normalize_symbol(state.get(key)) not in symbols:
        state[key] = current if current in symbols else symbols[0]
    with st.container(border=True):
        st.markdown(f"#### {title}")
        cols = st.columns([2, 1] if show_horizon else [1])
        selected = normalize_symbol(cols[0].selectbox(
            "Select symbol",
            options=symbols,
            index=symbols.index(normalize_symbol(state.get(key))) if normalize_symbol(state.get(key)) in symbols else 0,
            key=key,
            help="Select one canonical symbol and press Load. This changes this field's displayed evidence immediately.",
        ))
        horizon = None
        if show_horizon:
            hkey = f"{HORIZON_KEY}_{surface}"
            horizons = ["1H", "3H", "6H", "12H", "24H"]
            if state.get(hkey) not in horizons:
                state[hkey] = "1H"
            horizon = cols[1].selectbox("Horizon", horizons, key=hkey)
        b1, b2 = st.columns(2)
        loaded = b1.button(f"Load {selected}", key=f"load_{surface}_canonical_symbol_20260709", use_container_width=True)
        reload_clicked = b2.button("Reload current", key=f"reload_{surface}_canonical_symbol_20260709", use_container_width=True)
        if loaded:
            report = activate_symbol(state, selected, surface=surface, try_legacy=True)
        elif reload_clicked:
            report = activate_symbol(state, current or selected, surface=surface, try_legacy=True)
        else:
            report = state.get(f"{surface}_symbol_load_status_20260709") if isinstance(state.get(f"{surface}_symbol_load_status_20260709"), Mapping) else {}
            activate_symbol(state, current or selected, surface=surface, try_legacy=False)
        report = state.get(f"{surface}_symbol_load_status_20260709") if isinstance(state.get(f"{surface}_symbol_load_status_20260709"), Mapping) else report
        row = _field10_row(state, active_symbol(state, surface=surface))
        cards = st.columns(4)
        cards[0].metric("Current Symbol", active_symbol(state, surface=surface) or selected)
        cards[1].metric("Rank", str(row.get("Rank", report.get("rank", "—"))))
        cards[2].metric("Entry", str(row.get("Entry permission", report.get("entry_permission", "READY"))))
        cards[3].metric("Data Quality", str(row.get("Data quality grade", report.get("data_quality_grade", "—"))))
        st.caption(f"Loaded from canonical snapshot. Legacy child restore: {report.get('legacy_restore_status', 'not needed')}. No provider call or hidden calculation was started.")
    return active_symbol(state, surface=surface), horizon, dict(report or {})


__all__ = [
    "GLOBAL_SYMBOL_KEY", "STATUS_KEY", "available_symbols", "active_symbol", "activate_symbol",
    "filter_frame_for_symbol", "render_selector", "normalize_symbol",
]
