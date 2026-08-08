from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path


def test_three_groups_are_capped_and_mapped_to_dedicated_buttons():
    from core.multi_symbol_run_groups_20260706 import (
        FIRST_GROUP_KEY,
        SECOND_GROUP_KEY,
        THIRD_GROUP_KEY,
        initialize_groups,
        symbols_for_scope,
    )

    first = [
        "EURUSD", "USDJPY", "AUDUSD", "GBPUSD", "USDCAD", "USDCHF",
        "EURJPY", "GBPJPY", "EURGBP", "NZDUSD", "XAUUSD", "BTCUSD", "NAS100",
    ]
    second = ["US500", "AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA"]
    third = ["XAGUSD", "ETHUSD", "SOLUSD", "XRPUSD", "BNBUSD", "ADAUSD", "DOGEUSD"]
    state: dict[str, object] = {
        FIRST_GROUP_KEY: first,
        SECOND_GROUP_KEY: second,
        THIRD_GROUP_KEY: third,
    }
    groups = initialize_groups(state, first + second + third)
    assert groups["FIRST"] == state[FIRST_GROUP_KEY]
    assert groups["SECOND"] == state[SECOND_GROUP_KEY]
    assert groups["THIRD"] == state[THIRD_GROUP_KEY]
    assert len(groups["FIRST"]) == 12
    assert len(groups["SECOND"]) == 6
    assert len(groups["THIRD"]) == 6
    assert symbols_for_scope(state, "LUNCH_CORE") == groups["FIRST"]
    assert symbols_for_scope(state, "QUICK") == groups["SECOND"]
    assert symbols_for_scope(state, "FULL") == groups["THIRD"]


def test_partial_group_adds_only_completed_symbols_without_erasing_previous_results():
    from core.multi_symbol_run_groups_20260706 import COMPLETED_UNION_KEY, record_completed_symbols

    state = {COMPLETED_UNION_KEY: ["EURUSD", "USDJPY"]}
    transaction = {
        "status": "COMPLETED",
        "result_payload": {
            "status": "PARTIAL",
            "completed_symbols": 1,
            "failed_symbols": 1,
            "symbol_status": {
                "AUDUSD": {"state": "COMPLETED"},
                "GBPUSD": {"state": "FAILED_VALIDATION"},
            },
        },
    }
    merged = record_completed_symbols(state, ["AUDUSD", "GBPUSD"], transaction)
    assert merged == ["EURUSD", "USDJPY", "AUDUSD"]
    assert state[COMPLETED_UNION_KEY] == merged


def test_preferences_persist_all_three_groups_and_cumulative_results(tmp_path: Path):
    from core.multi_symbol_run_groups_20260706 import (
        COMPLETED_UNION_KEY,
        FIRST_GROUP_KEY,
        SECOND_GROUP_KEY,
        THIRD_GROUP_KEY,
        load_group_preferences,
        save_group_preferences,
    )

    path = tmp_path / "groups.sqlite3"
    state = {
        FIRST_GROUP_KEY: ["EURUSD", "USDJPY"],
        SECOND_GROUP_KEY: ["AUDUSD"],
        THIRD_GROUP_KEY: ["XAUUSD"],
        COMPLETED_UNION_KEY: ["EURUSD", "AUDUSD"],
    }
    save_group_preferences(path, state)
    restored = load_group_preferences(path)
    assert restored["first"] == ["EURUSD", "USDJPY"]
    assert restored["second"] == ["AUDUSD"]
    assert restored["third"] == ["XAUUSD"]
    assert restored["completed"] == ["EURUSD", "AUDUSD"]


def test_field10_daily_view_ranks_latest_row_per_completed_symbol_across_runs(tmp_path: Path):
    from core.multi_symbol_field10_20260701 import DB_PATH, load_field10_tables

    copied = tmp_path / "field10.sqlite3"
    shutil.copy2(DB_PATH, copied)
    rows = [
        ("2026-07-04", "EURUSD", 1, 70.0, "H4", "RUN-1"),
        ("2026-07-05", "EURUSD", 1, 72.0, "H4", "RUN-2"),
        ("2026-07-05", "AUDUSD", 1, 85.0, "H4", "RUN-3"),
        ("2026-07-06", "XAUUSD", 1, 65.0, "H4", "RUN-4"),
    ]
    with sqlite3.connect(copied) as conn:
        conn.execute("DELETE FROM field10_daily_higher_lock")
        for day, symbol, rank, score, timeframe, parent in rows:
            conn.execute(
                """INSERT INTO field10_daily_higher_lock(
                    broker_day,symbol,rank,higher_standard_regime,higher_standard_bias,
                    less_risky_bias,data_quality_grade,data_quality_score,higher_reliability,
                    higher_transition_risk,trade_permission,final_action,rank_score,rank_reason,
                    lock_status,locked_at_broker_time,last_reviewed_broker_time,parent_run_id,
                    timeframe,completed_candle
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    day, symbol, rank, "BULL", "BUY", "BUY", "A", 90.0, 80.0,
                    20.0, "ALLOWED", "BUY", score, "test", "LOCKED",
                    f"{day}T04:00:00", f"{day}T04:00:00", parent, timeframe,
                    f"{day}T04:00:00",
                ),
            )
        conn.commit()

    state = {
        "timeframe": "H4",
        "multi_symbol_completed_union_20260706": ["EURUSD", "AUDUSD", "XAUUSD"],
    }
    daily = load_field10_tables(state, path=copied)["daily"]
    assert daily["Symbol"].tolist() == ["AUDUSD", "EURUSD", "XAUUSD"]
    assert daily["Rank"].astype("Int64").tolist() == [1, 2, 3]
    assert daily.loc[daily["Symbol"] == "EURUSD", "Broker Day"].iloc[0] == "2026-07-05"
    assert "Stored Daily Rank" in daily.columns
    assert daily["Rank Scope"].str.contains(r"First \+ Second \+ Third", regex=True).all()


def test_menu_and_button_contracts_are_explicit_and_mobile_safe():
    popup = Path("ui/liquid_menu_popup_20260615.py").read_text(encoding="utf-8")
    sticky = Path("ui/home_master_control_bar_20260615.py").read_text(encoding="utf-8")
    router = Path("tabs/antd_page_router_20260615.py").read_text(encoding="utf-8")
    settings = Path("ui/multi_symbol_settings_20260701.py").read_text(encoding="utf-8")

    assert 'div[data-testid="stPopoverBody"]{{position:fixed!important;top:16vh!important' in popup
    assert "top:18vh!important" in popup
    assert "top:80vh!important" in sticky
    assert "First Multi-Symbol Selector" in settings
    assert "Second Multi-Symbol Selector" in settings
    assert "Third Multi-Symbol Selector" in settings
    assert "max_selections=limit" in settings
    assert "Super Quick Calculation + Open Lunch — First Selector" in router
    assert "Quick Calculation + Open Lunch — Second Selector" in router
    assert "Full Calculation + Open Lunch — Third Selector" in router
