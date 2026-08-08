from __future__ import annotations

from pathlib import Path
import json
import sqlite3
import sys

import pandas as pd
import pytest


FIRST = ["AUDUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP"]
SECOND = ["NZDUSD", "EURCHF", "EURAUD", "EURCAD", "EURNZD", "GBPCHF"]
THIRD = ["GBPAUD", "GBPCAD", "AUDJPY", "XAUUSD", "XAGUSD", "NAS100"]


def h4_frame(rows: int = 120) -> pd.DataFrame:
    times = pd.date_range("2026-01-01", periods=rows, freq="4h", tz="UTC")
    return pd.DataFrame({
        "open_time": times,
        "open": range(rows),
        "high": [x + 1 for x in range(rows)],
        "low": [x - 1 for x in range(rows)],
        "close": [x + 0.5 for x in range(rows)],
        "volume": [100] * rows,
    })


def payload(symbol: str, timeframe: str = "H4", rows: int = 120) -> dict:
    frame = h4_frame(rows)
    return {
        "ok": True,
        "symbol": symbol,
        "timeframe": timeframe,
        "frame": frame,
        "provider": "TWELVE_DATA",
        "status": "READY",
        "validation_status": "VALID",
        "latest_completed_candle": frame["open_time"].iloc[-1].isoformat(),
    }


def test_explicit_empty_groups_never_revive_defaults():
    from core.multi_symbol_run_groups_20260706 import (
        FIRST_GROUP_KEY, SECOND_GROUP_KEY, THIRD_GROUP_KEY, initialize_groups,
    )
    state = {FIRST_GROUP_KEY: [], SECOND_GROUP_KEY: SECOND, THIRD_GROUP_KEY: []}
    groups = initialize_groups(state, fallback_symbols=FIRST + SECOND + THIRD)
    assert groups["FIRST"] == []
    assert groups["SECOND"] == SECOND
    assert groups["THIRD"] == []


def test_union_supports_eighteen_and_preserves_order():
    from core.multi_symbol_run_groups_20260706 import union_symbols
    assert union_symbols(FIRST, SECOND, THIRD) == FIRST + SECOND + THIRD
    assert len(union_symbols(FIRST, SECOND, THIRD)) == 18
    assert union_symbols(["AUDUSD", "USDCAD"], ["AUDUSD", "NZDUSD"], ["NZDUSD", "XAUUSD"]) == [
        "AUDUSD", "USDCAD", "NZDUSD", "XAUUSD"
    ]


def test_normalized_selection_persistence_restores_empty_and_order(tmp_path: Path):
    from core.data.deployment_migrations_20260705 import migrate_deployment_schema
    from core.normalized_multi_symbol_migration_20260707 import replace_current_selections, load_current_selections
    db = tmp_path / "state.sqlite3"
    migrate_deployment_schema(db)
    replace_current_selections(db, {"FIRST": FIRST, "SECOND": [], "THIRD": THIRD}, "H4")
    restored = load_current_selections(db)
    assert restored is not None
    assert restored["first"] == FIRST
    assert restored["second"] == []
    assert restored["third"] == THIRD


def test_migration_is_idempotent_and_supports_18_symbols(tmp_path: Path):
    from core.data.deployment_migrations_20260705 import migrate_deployment_schema
    from core.normalized_multi_symbol_migration_20260707 import replace_current_selections
    db = tmp_path / "legacy.sqlite3"
    one = migrate_deployment_schema(db)
    two = migrate_deployment_schema(db)
    assert one["ok"] and two["ok"]
    replace_current_selections(db, {"FIRST": FIRST, "SECOND": SECOND, "THIRD": THIRD}, "H4")
    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            "SELECT group_id,position,symbol,selected_timeframe FROM selector_selections WHERE is_current=1 ORDER BY CASE group_id WHEN 'first' THEN 1 WHEN 'second' THEN 2 ELSE 3 END, position"
        ).fetchall()
    assert [row[2] for row in rows] == FIRST + SECOND + THIRD
    assert all(row[3] == "H4" for row in rows)


def test_candle_store_uniqueness(tmp_path: Path):
    from core.data.deployment_migrations_20260705 import migrate_deployment_schema
    db = tmp_path / "candles.sqlite3"
    migrate_deployment_schema(db)
    row = ("AUDUSD", "H4", "2026-07-07T00:00:00+00:00", 1, 2, 0.5, 1.5, 100, "TEST", "2026-07-07T04:00:00+00:00", "VALID", 1, 2026070704)
    with sqlite3.connect(db) as conn:
        conn.execute("INSERT INTO candle_store VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", row)
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO candle_store VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", row)


def test_three_groups_load_exact_selected_symbols_and_h4(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    import core.data.deployment_migrations_20260705 as migrations
    import core.calculation.run_orchestrator as orchestrator
    from core.multi_symbol_load_manager_20260707 import load_group_market_data

    db = tmp_path / "load.sqlite3"
    monkeypatch.setattr(migrations, "DEFAULT_DB_PATH", db)
    calls: list[list[str]] = []

    def fake_prepare(state, *, run_id, selected_symbols, timeframe, progress_callback=None):
        calls.append(list(selected_symbols))
        return {"results": {s: payload(s, timeframe) for s in selected_symbols}}

    monkeypatch.setattr(orchestrator, "prepare_market_data_for_run", fake_prepare)
    state: dict = {"timeframe": "H4"}
    for group, selected in (("FIRST", FIRST), ("SECOND", SECOND), ("THIRD", THIRD)):
        record = load_group_market_data(state, group, selected, "H4")
        assert record["requested_symbols"] == selected
        assert record["loaded_symbols"] == selected
        assert record["failed_symbols"] == []
        assert record["timeframe"] == "H4"
        assert record["status"] == "READY"
    assert calls == [FIRST, SECOND, THIRD]
    assert not ({"EURUSD", "USDJPY", "GBPUSD"} & set(calls[-1]))


def test_reload_retries_only_failed_and_merges_ready(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    import core.data.deployment_migrations_20260705 as migrations
    import core.calculation.run_orchestrator as orchestrator
    from core.multi_symbol_load_manager_20260707 import load_group_market_data, reload_failed_symbols

    db = tmp_path / "retry.sqlite3"
    monkeypatch.setattr(migrations, "DEFAULT_DB_PATH", db)
    calls: list[list[str]] = []

    def fake_prepare(state, *, run_id, selected_symbols, timeframe, progress_callback=None):
        calls.append(list(selected_symbols))
        results = {}
        for symbol in selected_symbols:
            if len(calls) == 1 and symbol in SECOND[1:]:
                results[symbol] = {
                    "ok": False, "symbol": symbol, "timeframe": timeframe,
                    "provider": "TWELVE_DATA", "status": "429 RATE LIMIT", "message": "quota exceeded",
                }
            else:
                results[symbol] = payload(symbol, timeframe)
        return {"results": results}

    monkeypatch.setattr(orchestrator, "prepare_market_data_for_run", fake_prepare)
    state: dict = {"timeframe": "H4"}
    first = load_group_market_data(state, "SECOND", SECOND, "H4")
    assert first["loaded_symbols"] == [SECOND[0]]
    assert first["failed_symbols"] == SECOND[1:]
    assert first["status"] == "PARTIAL_READY"
    assert all(first["validations"][s]["failure_code"] == "PROVIDER_RATE_LIMIT" for s in SECOND[1:])
    second = reload_failed_symbols(state, "SECOND", SECOND, "H4")
    assert calls[1] == SECOND[1:]
    assert second["loaded_symbols"] == SECOND
    assert second["failed_symbols"] == []
    assert second["selection_signature"]
    assert second["retry_count_by_symbol"][SECOND[0]] == 0
    assert all(second["retry_count_by_symbol"][s] == 1 for s in SECOND[1:])


def test_reload_never_adds_unselected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    import core.data.deployment_migrations_20260705 as migrations
    import core.calculation.run_orchestrator as orchestrator
    from core.multi_symbol_load_manager_20260707 import load_group_market_data, reload_failed_symbols

    monkeypatch.setattr(migrations, "DEFAULT_DB_PATH", tmp_path / "exact.sqlite3")
    count = 0
    def fake_prepare(state, *, run_id, selected_symbols, timeframe, progress_callback=None):
        nonlocal count
        count += 1
        if count == 1:
            return {"results": {selected_symbols[0]: payload(selected_symbols[0], timeframe)}}
        return {"results": {**{s: payload(s, timeframe) for s in selected_symbols}, "EURUSD": payload("EURUSD", timeframe)}}
    monkeypatch.setattr(orchestrator, "prepare_market_data_for_run", fake_prepare)
    state = {"timeframe": "H4"}
    load_group_market_data(state, "THIRD", THIRD[:3], "H4")
    record = reload_failed_symbols(state, "THIRD", THIRD[:3], "H4")
    assert record["loaded_symbols"] == THIRD[:3]
    assert "EURUSD" not in record["requested_symbols"]
    assert "EURUSD" not in record["report"]["results"]


def test_h1_and_h4_are_separate_load_identities(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    import core.data.deployment_migrations_20260705 as migrations
    import core.calculation.run_orchestrator as orchestrator
    from core.multi_symbol_load_manager_20260707 import load_group_market_data, loaded_group_status
    monkeypatch.setattr(migrations, "DEFAULT_DB_PATH", tmp_path / "tf.sqlite3")
    monkeypatch.setattr(orchestrator, "prepare_market_data_for_run", lambda state, *, run_id, selected_symbols, timeframe, progress_callback=None: {"results": {s: payload(s, timeframe, 120 if timeframe == "H4" else 120) for s in selected_symbols}})
    state = {"timeframe": "H4"}
    record = load_group_market_data(state, "FIRST", ["AUDUSD"], "H4")
    assert record["timeframe"] == "H4"
    assert loaded_group_status(state, "FIRST", ["AUDUSD"], "H1")["status"] == "STALE"


def test_consolidated_table_uses_loaded_spine_and_required_columns(monkeypatch: pytest.MonkeyPatch):
    import core.system_continuous_validation_20260702 as continuous
    import core.field10_daily_snapshot_contract_20260702 as snapshots
    import ui.lunch_field10_multi_symbol_20260701 as ui

    symbols = ["AUDUSD", "NZDUSD", "GBPAUD"]
    evidence = {s: {"ok": True, "rows": 120, "required_rows": 150, "minimum_rows": 100, "provider": "TEST", "Selector Groups": "first", "Load Status": "READY"} for s in symbols}
    monkeypatch.setattr(ui, "_field10_loaded_symbol_contract", lambda state, universe: (symbols, evidence))
    monkeypatch.setattr(continuous, "build_field3_higher_standard_multi_symbol_table", lambda state, selected_symbols, parent_run_id=None: (
        pd.DataFrame({"Symbol": symbols + ["EURUSD"], "Timeframe": ["H4"] * 4, "Rank": [1,2,3,4], "Higher Standard Regime": ["RANGE"]*4, "Higher-Standard Bias": ["BUY","SELL","WAIT","BUY"], "Less-Risky Bias": ["BUY","SELL","WAIT","BUY"], "Data Quality": ["A"]*4, "Sample Count": [120]*4, "Evidence Source": ["TEST"]*4}), {}
    ))
    monkeypatch.setattr(ui, "_latest_run_main_table_20260706", lambda state, selected, manifest: (pd.DataFrame({"Symbol": symbols, "Final Score": [80,70,60], "Validation Status": ["PASS"]*3}), {"field10_row_count": 3}))
    monkeypatch.setattr(snapshots, "load_current_daily_snapshot", lambda: {"metadata": {}})
    monkeypatch.setattr(ui, "_load_field10_source_frames_20260706", lambda metadata: {})
    monkeypatch.setattr(ui, "_build_visible_four_source_fusion_20260706", lambda latest, sources, completion: pd.DataFrame({"Symbol": symbols}))
    table, report = ui._build_consolidated_field10_table_20260707({"timeframe": "H4"}, {"parent_run_id": "RUN-1"})
    assert table["Symbol"].tolist() == symbols
    assert "EURUSD" not in table["Symbol"].tolist()
    required = {"Final Rank", "Timeframe", "Highest-Impact Current News Title", "Absorption Status", "NLP Sentiment Bias", "Configured Selector Group(s)", "Run ID", "Failure Code"}
    assert required.issubset(table.columns)
    assert table["Timeframe"].eq("H4").all()
    assert table["Highest-Impact Current News Title"].eq("Not available").all()
    assert table["Absorption Status"].eq("UNAVAILABLE").all()
    assert table["NLP Sentiment Bias"].eq("UNAVAILABLE").all()
    assert report["row_count"] == 3


def test_optional_reliability_or_news_does_not_invalidate_core_row(monkeypatch: pytest.MonkeyPatch):
    import core.multi_symbol_completion_contract_20260706 as contract
    monkeypatch.setattr(sys.modules["core.multi_symbol_field10_20260701"], "available_saved_symbols", lambda selected: list(selected))
    frame = pd.DataFrame([{"Symbol": "AUDUSD", "Timeframe": "H4", "Rank": 1, "Higher-Standard Bias": "BUY", "Data Quality Grade": "A", "Calculation Status": "PUBLISHED"}])
    manifest = {"parent_run_id": "R1", "selected_symbols": ["AUDUSD"], "timeframe": "H4", "symbol_status": {"AUDUSD": {"state": "COMPLETED"}}}
    report = contract.validate_multi_symbol_completion({"timeframe": "H4"}, manifest, field10_frame=frame)
    assert report["ok"] is True


def test_mixed_timeframe_and_duplicates_rejected(monkeypatch: pytest.MonkeyPatch):
    import core.multi_symbol_completion_contract_20260706 as contract
    monkeypatch.setattr(sys.modules["core.multi_symbol_field10_20260701"], "available_saved_symbols", lambda selected: list(selected))
    frame = pd.DataFrame([
        {"Symbol": "AUDUSD", "Timeframe": "H1", "Rank": 1, "Higher-Standard Bias": "BUY", "Data Quality Grade": "A", "Calculation Status": "PUBLISHED"},
        {"Symbol": "AUDUSD", "Timeframe": "H1", "Rank": 2, "Higher-Standard Bias": "BUY", "Data Quality Grade": "A", "Calculation Status": "PUBLISHED"},
    ])
    manifest = {"parent_run_id": "R2", "selected_symbols": ["AUDUSD"], "timeframe": "H4", "symbol_status": {"AUDUSD": {"state": "COMPLETED"}}}
    report = contract.validate_multi_symbol_completion({"timeframe": "H4"}, manifest, field10_frame=frame)
    assert report["ok"] is False
    assert report["duplicate_field10_symbols"] == ["AUDUSD"]
    assert report["timeframe_mismatches"]["AUDUSD"] == "H1"


def test_normalized_atomic_publication_writes_one_row_per_symbol(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    import core.multi_symbol_completion_contract_20260706 as contract
    from core.data.deployment_migrations_20260705 import migrate_deployment_schema
    db = tmp_path / "publication.sqlite3"
    migrate_deployment_schema(db)
    monkeypatch.setattr(contract, "_database_path", lambda: db)
    frame = pd.DataFrame([
        {"Symbol": "AUDUSD", "Timeframe": "H4", "Final Rank": 1, "Higher-Standard Bias": "BUY", "Data Quality Grade": "A", "Calculation Status": "PUBLISHED", "Latest Completed Broker Candle": "2026-07-07T12:00:00+00:00"},
        {"Symbol": "NZDUSD", "Timeframe": "H4", "Final Rank": 2, "Higher-Standard Bias": "SELL", "Data Quality Grade": "B", "Calculation Status": "PUBLISHED", "Latest Completed Broker Candle": "2026-07-07T12:00:00+00:00"},
    ])
    report = {"ok": True, "parent_run_id": "RUN-ATOMIC", "selected_symbols": ["AUDUSD", "NZDUSD"], "timeframe": "H4", "generation": 7, "calculation_depth": "FULL", "main_symbol": "AUDUSD"}
    contract._persist_completion_result(report, frame)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT publication_status FROM canonical_runs WHERE run_id='RUN-ATOMIC' AND generation=7").fetchone()[0] == "PUBLISHED"
        rows = conn.execute("SELECT symbol,timeframe,checksum FROM field10_symbol_rows WHERE run_id='RUN-ATOMIC' ORDER BY symbol").fetchall()
        assert [(r[0], r[1]) for r in rows] == [("AUDUSD", "H4"), ("NZDUSD", "H4")]
        assert all(len(r[2]) == 64 for r in rows)
        assert conn.execute("SELECT COUNT(*) FROM symbol_calculation_snapshots WHERE run_id='RUN-ATOMIC'").fetchone()[0] == 2



def test_exact_eighteen_symbol_retry_and_same_universe_for_all_depths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Controlled final scenario: genuine-shaped H4 frames, transient failures, exact retries."""
    import core.data.deployment_migrations_20260705 as migrations
    import core.calculation.run_orchestrator as orchestrator
    from core.multi_symbol_load_manager_20260707 import (
        load_group_market_data, reload_failed_symbols, loaded_universe_status,
        activate_loaded_universe_for_run,
    )
    from core.multi_symbol_run_groups_20260706 import (
        FIRST_GROUP_KEY, SECOND_GROUP_KEY, THIRD_GROUP_KEY,
    )

    monkeypatch.setattr(migrations, "DEFAULT_DB_PATH", tmp_path / "final_scenario.sqlite3")
    attempts: dict[str, int] = {}
    transient = {"EURCHF", "EURAUD", "GBPCAD", "XAGUSD"}

    def fake_prepare(state, *, run_id, selected_symbols, timeframe, progress_callback=None):
        results = {}
        for symbol in selected_symbols:
            attempts[symbol] = attempts.get(symbol, 0) + 1
            if symbol in transient and attempts[symbol] == 1:
                results[symbol] = {
                    "ok": False, "symbol": symbol, "timeframe": timeframe,
                    "provider": "TWELVE_DATA", "status": "429 RATE LIMIT",
                    "message": "simulated transient quota response",
                }
            else:
                results[symbol] = payload(symbol, timeframe)
        return {"results": results}

    monkeypatch.setattr(orchestrator, "prepare_market_data_for_run", fake_prepare)
    configured = {"FIRST": FIRST, "SECOND": SECOND, "THIRD": THIRD}
    state = {
        "timeframe": "H4", FIRST_GROUP_KEY: FIRST,
        SECOND_GROUP_KEY: SECOND, THIRD_GROUP_KEY: THIRD,
    }

    first = load_group_market_data(state, "FIRST", FIRST, "H4")
    second = load_group_market_data(state, "SECOND", SECOND, "H4")
    third = load_group_market_data(state, "THIRD", THIRD, "H4")
    assert first["status"] == "READY"
    assert second["status"] == "PARTIAL_READY"
    assert third["status"] == "PARTIAL_READY"
    assert second["failed_symbols"] == ["EURCHF", "EURAUD"]
    assert third["failed_symbols"] == ["GBPCAD", "XAGUSD"]

    second_retry = reload_failed_symbols(state, "SECOND", SECOND, "H4")
    third_retry = reload_failed_symbols(state, "THIRD", THIRD, "H4")
    assert second_retry["loaded_symbols"] == SECOND
    assert third_retry["loaded_symbols"] == THIRD
    assert attempts["NZDUSD"] == 1 and attempts["GBPAUD"] == 1
    assert attempts["EURCHF"] == 2 and attempts["XAGUSD"] == 2

    cumulative = loaded_universe_status(state, configured, "H4")
    assert cumulative["status"] == "READY"
    assert cumulative["loaded_symbols"] == FIRST + SECOND + THIRD
    assert cumulative["failed_symbols"] == []

    for scope in ("LUNCH_CORE", "QUICK", "FULL"):
        activated = activate_loaded_universe_for_run(state, scope, configured, "H4")
        assert activated["ok"] is True
        assert activated["loaded_symbols"] == FIRST + SECOND + THIRD
        assert state["selected_symbols_for_run_20260705"] == FIRST + SECOND + THIRD
        assert state["timeframe"] == "H4"

def test_ui_source_has_one_authoritative_surface_and_no_duplicate_profile_block():
    settings = Path("ui/multi_symbol_settings_20260701.py").read_text(encoding="utf-8")
    lunch = Path("ui/lunch_field10_multi_symbol_20260701.py").read_text(encoding="utf-8")
    router = Path("tabs/antd_page_router_20260615.py").read_text(encoding="utf-8")
    assert "Reload Failed Symbols" in settings
    assert 'st.markdown("### ▶ 3 Run Calculation Choices — Always Visible")' not in settings
    assert "Load symbols explicitly first; this button never fetches APIs." in router
    assert "Field 3 Higher-Standard Multi-Symbol Bias + Consolidated Field 10 — All Loaded Settings Symbols" in lunch
    render_body = lunch.split("def render_field10_content", 1)[1].split("def _field10_part4", 1)[0]
    assert "Search consolidated multi-symbol table" not in render_body
    assert "allow_cards=False" in render_body
    assert "expanded=False" in render_body


def test_no_live_secrets_in_package_sources():
    forbidden_prefixes = ("sk-or-v1-", "sk-proj-", "AKIA")
    bad = []
    for path in Path(".").rglob("*"):
        if not path.is_file() or ".git" in path.parts or "tests" in path.parts or path.suffix.lower() in {".sqlite3", ".db", ".zip", ".png", ".jpg", ".jpeg", ".pdf", ".pyc"}:
            continue
        if path.name == "secrets.toml":
            bad.append(str(path))
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(prefix in text for prefix in forbidden_prefixes):
            bad.append(str(path))
    assert bad == []
