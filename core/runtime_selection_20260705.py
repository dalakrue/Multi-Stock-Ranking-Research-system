"""Single authority for selected symbols, timeframe, and completed-candle identity.

The module is intentionally Streamlit-optional so it can be used by migrations,
tests, connector code, and UI code without creating widget side effects.
"""
from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from datetime import datetime, timezone
from typing import Any
import json
import sqlite3
from pathlib import Path

from core.timeframe_window_contract_20260706 import TIMEFRAME_SECONDS as SHARED_TIMEFRAME_SECONDS, selected_timeframe

TOP_10_CURRENCY_PAIRS: tuple[str, ...] = (
    "EURUSD", "USDJPY", "AUDUSD", "GBPUSD", "USDCAD",
    "USDCHF", "EURJPY", "GBPJPY", "EURGBP", "NZDUSD",
)
SUPPORTED_TIMEFRAMES: tuple[str, ...] = tuple(SHARED_TIMEFRAME_SECONDS)
TIMEFRAME_SECONDS: dict[str, int] = dict(SHARED_TIMEFRAME_SECONDS)
SELECTED_KEY = "multi_symbol_selected_20260701"
TIMEFRAME_KEY = "timeframe"
CANONICAL_SELECTION_KEY = "canonical_runtime_selection_20260705"
FIRST_LOAD_KEY = "top10_default_initialized_20260705"
SELECTION_PROFILE_VERSION = 20260706
DEFAULT_TIMEFRAME = "H4"


def normalize_symbol(value: Any, default: str = "EURUSD") -> str:
    raw = str(value or default).strip().upper().replace("/", "").replace(" ", "")
    aliases = {
        "XBTUSD": "BTCUSD", "BTCUSDT": "BTCUSD", "GOLD": "XAUUSD",
        "USDX": "DXY", "DX-Y.NYB": "DXY", "DOLLARINDEX": "DXY",
        "USTEC": "NAS100", "US100": "NAS100", "NDX": "NAS100",
        "SPX500": "US500", "SP500": "US500", "GSPC": "US500",
    }
    return aliases.get(raw, raw) or default


def normalize_symbols(values: Any, *, default_top10: bool = False) -> list[str]:
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, Sequence):
        values = []
    out: list[str] = []
    for value in values:
        symbol = normalize_symbol(value)
        if symbol and symbol not in out:
            out.append(symbol)
    return out or (list(TOP_10_CURRENCY_PAIRS) if default_top10 else [])


def normalize_timeframe(value: Any, default: str = DEFAULT_TIMEFRAME) -> str:
    raw = str(value or default).strip().upper().replace(" ", "")
    aliases = {"1H": "H1", "4H": "H4", "60MIN": "H1", "240MIN": "H4", "1DAY": "D1"}
    raw = aliases.get(raw, raw)
    return raw if raw in SUPPORTED_TIMEFRAMES else default


def timeframe_seconds(timeframe: Any) -> int:
    return TIMEFRAME_SECONDS[normalize_timeframe(timeframe)]


def latest_completed_candle(
    now: datetime | None = None,
    timeframe: Any = DEFAULT_TIMEFRAME,
    *,
    settlement_delay_minutes: int = 3,
) -> datetime:
    """Return the latest fully settled UTC candle open time.

    H4 boundaries are aligned to 00:00/04:00/08:00/... UTC. A configurable
    settlement delay prevents fetching the candle while the provider is still
    publishing it.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    seconds = timeframe_seconds(timeframe)
    adjusted_epoch = int(now.timestamp()) - max(0, int(settlement_delay_minutes)) * 60
    current_open_epoch = adjusted_epoch - (adjusted_epoch % seconds)
    completed_open_epoch = current_open_epoch - seconds
    return datetime.fromtimestamp(completed_open_epoch, tz=timezone.utc)


def cache_identity(symbol: Any, timeframe: Any, completed: datetime | str | None = None) -> str:
    completed_dt = completed or latest_completed_candle(timeframe=timeframe)
    if isinstance(completed_dt, datetime):
        completed_text = completed_dt.astimezone(timezone.utc).isoformat()
    else:
        completed_text = str(completed_dt)
    return f"{normalize_symbol(symbol)}|{normalize_timeframe(timeframe)}|{completed_text}"


def synchronize_runtime_selection(
    state: MutableMapping[str, Any],
    *,
    default_top10_on_first_load: bool = True,
    persisted: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Synchronize all legacy mirrors to one symbol/timeframe selection.

    Explicit current session values win, then persisted preferences, then the
    Top-10 first-load default. The function never erases an intentional user
    selection on rerun.
    """
    persisted = persisted if isinstance(persisted, Mapping) else {}
    current = normalize_symbols(state.get(SELECTED_KEY))
    saved = normalize_symbols(persisted.get("selected_symbols"))
    initialized = bool(state.get(FIRST_LOAD_KEY))
    try:
        persisted_profile_current = int(persisted.get("selection_profile_version") or 0) >= SELECTION_PROFILE_VERSION
    except Exception:
        persisted_profile_current = False
    if current:
        selected = current
    elif saved and persisted_profile_current:
        selected = saved
    elif default_top10_on_first_load and not initialized:
        selected = list(TOP_10_CURRENCY_PAIRS)
    else:
        main = normalize_symbol(state.get("multi_symbol_main_symbol_20260702") or state.get("symbol") or "EURUSD")
        selected = [main]

    persisted_timeframe = persisted.get("timeframe") if persisted_profile_current else None
    # init_state seeds H4, but that is only a UI default—not an explicit user
    # choice. On a fresh session the persisted timeframe must be resolved before
    # the durable generation registry is queried, otherwise an H1 snapshot is
    # incorrectly looked up as H4.
    if persisted_timeframe and not initialized:
        timeframe_source = persisted_timeframe
    else:
        timeframe_source = (
            state.get(TIMEFRAME_KEY)
            or state.get("selected_timeframe")
            or state.get("last_connected_timeframe")
            or persisted_timeframe
            or DEFAULT_TIMEFRAME
        )
    timeframe = normalize_timeframe(timeframe_source, default=DEFAULT_TIMEFRAME)
    main = normalize_symbol(
        state.get("settings_main_symbol") or state.get("multi_symbol_main_symbol_20260702") or selected[0]
    )
    if main not in selected:
        main = selected[0]
    persisted_active = persisted.get("active_display_symbol") if persisted_profile_current and not initialized else None
    active = normalize_symbol(
        persisted_active
        or state.get("canonical_display_symbol_20260709")
        or state.get("lunch_display_symbol_20260702")
        or state.get("multi_symbol_active_20260701")
        or main
    )
    if active not in selected:
        active = main

    state[SELECTED_KEY] = list(selected)
    state["settings_main_symbol"] = main
    state["multi_symbol_main_symbol_20260702"] = main
    state["connector_symbol"] = main
    state["calculation_symbol"] = main
    state["multi_symbol_active_20260701"] = active
    state["lunch_display_symbol_20260702"] = active
    state["canonical_display_symbol_20260709"] = active
    state["connector_symbol_20260702"] = main
    state["requested_symbol_20260629"] = main
    state["selected_symbol"] = main
    # Legacy calculation authority only. Lunch display switching must never mutate it.
    state.setdefault("symbol", main)
    state[TIMEFRAME_KEY] = timeframe
    state["selected_timeframe"] = timeframe
    state["connector_timeframe_20260705"] = timeframe
    state["last_connected_timeframe"] = timeframe
    state[FIRST_LOAD_KEY] = True
    completed = latest_completed_candle(timeframe=timeframe).isoformat()
    canonical = {
        "selected_symbols": list(selected),
        "main_symbol": main,
        "settings_main_symbol": main,
        "connector_symbol": main,
        "calculation_symbol": main,
        "lunch_display_symbol": active,
        "active_snapshot_symbol": active,
        "active_symbol": active,
        "timeframe": timeframe,
        "latest_completed_candle": completed,
    }
    state[CANONICAL_SELECTION_KEY] = canonical
    return canonical


def load_runtime_preferences(db_path: str | Path) -> dict[str, Any]:
    path = Path(db_path)
    if not path.exists():
        return {}
    try:
        with sqlite3.connect(str(path), timeout=5) as conn:
            columns = {str(item[1]) for item in conn.execute("PRAGMA table_info(runtime_preferences)").fetchall()}
            version_expr = "selection_profile_version" if "selection_profile_version" in columns else "0"
            active_expr = "active_display_symbol" if "active_display_symbol" in columns else "NULL"
            row = conn.execute(
                f"SELECT selected_symbols_json,timeframe,{version_expr},{active_expr} FROM runtime_preferences WHERE preference_id=1"
            ).fetchone()
        if not row:
            return {}
        return {
            "selected_symbols": json.loads(row[0] or "[]"),
            "timeframe": row[1] or DEFAULT_TIMEFRAME,
            "selection_profile_version": int(row[2] or 0),
            "active_display_symbol": normalize_symbol(row[3]) if len(row) > 3 and row[3] else None,
        }
    except Exception:
        return {}


def save_runtime_preferences(db_path: str | Path, selected_symbols: Sequence[Any], timeframe: Any) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    symbols = normalize_symbols(selected_symbols, default_top10=True)
    tf = normalize_timeframe(timeframe)
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(str(path), timeout=10) as conn:
        conn.execute("PRAGMA busy_timeout=8000")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS runtime_preferences(
                   preference_id INTEGER PRIMARY KEY CHECK(preference_id=1),
                   selected_symbols_json TEXT NOT NULL,
                   timeframe TEXT NOT NULL,
                   updated_at TEXT NOT NULL
               )"""
        )
        columns = {str(item[1]) for item in conn.execute("PRAGMA table_info(runtime_preferences)").fetchall()}
        if "selection_profile_version" not in columns:
            conn.execute("ALTER TABLE runtime_preferences ADD COLUMN selection_profile_version INTEGER NOT NULL DEFAULT 0")
        if "active_display_symbol" not in columns:
            conn.execute("ALTER TABLE runtime_preferences ADD COLUMN active_display_symbol TEXT")
        conn.execute(
            """INSERT INTO runtime_preferences(
                   preference_id,selected_symbols_json,timeframe,updated_at,selection_profile_version)
               VALUES(1,?,?,?,?) ON CONFLICT(preference_id) DO UPDATE SET
               selected_symbols_json=excluded.selected_symbols_json,
               timeframe=excluded.timeframe,updated_at=excluded.updated_at,
               selection_profile_version=excluded.selection_profile_version""",
            (json.dumps(symbols), tf, now, SELECTION_PROFILE_VERSION),
        )
        conn.commit()


def save_active_display_symbol(db_path: str | Path, symbol: Any) -> None:
    """Persist the cross-tab display symbol without changing the loaded universe."""
    path = Path(db_path)
    if not path.exists():
        return
    sym = normalize_symbol(symbol)
    with sqlite3.connect(str(path), timeout=10) as conn:
        conn.execute("PRAGMA busy_timeout=8000")
        columns = {str(item[1]) for item in conn.execute("PRAGMA table_info(runtime_preferences)").fetchall()}
        if not columns:
            return
        if "active_display_symbol" not in columns:
            conn.execute("ALTER TABLE runtime_preferences ADD COLUMN active_display_symbol TEXT")
        conn.execute("UPDATE runtime_preferences SET active_display_symbol=? WHERE preference_id=1", (sym,))
        conn.commit()


__all__ = [
    "TOP_10_CURRENCY_PAIRS", "SUPPORTED_TIMEFRAMES", "TIMEFRAME_SECONDS",
    "SELECTED_KEY", "CANONICAL_SELECTION_KEY", "normalize_symbol",
    "normalize_symbols", "normalize_timeframe", "timeframe_seconds",
    "latest_completed_candle", "cache_identity", "synchronize_runtime_selection",
    "load_runtime_preferences", "save_runtime_preferences", "save_active_display_symbol", "SELECTION_PROFILE_VERSION", "DEFAULT_TIMEFRAME",
]
