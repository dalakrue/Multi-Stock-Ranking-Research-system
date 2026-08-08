from pathlib import Path
import sqlite3
import pandas as pd


def test_unified_authority_builds_required_columns():
    from core.field10_unified_authority_20260709 import build_unified_field10_authority, REQUIRED_TRUST_FIELDS
    state = {
        "canonical_selected_symbols": ["EURUSD", "GBPUSD", "USDJPY"],
        "selected_timeframe": "H4",
        "latest_completed_candle_for_run_20260705": "2026-07-09T00:00:00+00:00",
    }
    source = pd.DataFrame([
        {"Symbol":"EURUSD", "Rank":1, "Less-Risky Bias":"BUY", "Rows":600, "Data Quality Grade":"A", "Provider Used":"TEST"},
        {"Symbol":"GBPUSD", "Rank":2, "Less-Risky Bias":"SELL", "Rows":600, "Data Quality Grade":"B", "Provider Used":"TEST"},
        {"Symbol":"USDJPY", "Rank":3, "Less-Risky Bias":"WAIT", "Rows":600, "Data Quality Grade":"B", "Provider Used":"TEST"},
    ])
    result = build_unified_field10_authority(state, source_frame=source, persist=False)
    table = result["table"]
    for col in REQUIRED_TRUST_FIELDS:
        assert col in table.columns
    assert result["snapshot"]["publication_status"] == "COMPLETE"
    assert table["Rank Star"].tolist()[:3] == ["★ 1", "★ 2", "★ 3"]


def test_partial_ready_when_selected_symbols_missing():
    from core.field10_unified_authority_20260709 import build_unified_field10_authority
    state = {"canonical_selected_symbols": ["EURUSD", "GBPUSD"], "selected_timeframe": "H4"}
    source = pd.DataFrame([{"Symbol":"EURUSD", "Rank":1, "Less-Risky Bias":"BUY", "Rows":600}])
    result = build_unified_field10_authority(state, source_frame=source, persist=False)
    assert result["snapshot"]["publication_status"] == "PARTIAL_READY"
    assert int(result["snapshot"]["failed_symbol_count"]) == 1
    assert "No-Trade Reason" in result["table"].columns


def test_migration_idempotent_and_repairs_schema_migrations(tmp_path: Path):
    from core.field10_research_migration_20260709 import migrate_field10_research_authority
    db = tmp_path / "test.sqlite3"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE schema_migrations (migration_id TEXT PRIMARY KEY)")
    conn.execute("INSERT INTO schema_migrations(migration_id) VALUES('old_migration')")
    conn.commit(); conn.close()
    assert migrate_field10_research_authority(db)["ok"] is True
    assert migrate_field10_research_authority(db)["ok"] is True
    conn = sqlite3.connect(db)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(schema_migrations)")}
    assert {"version", "applied_at", "checksum", "status"}.issubset(cols)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "field10_unified_rank_snapshot" in tables
    assert "field10_unified_rank_symbol" in tables
    conn.close()


def test_view_model_sync_ok():
    from core.field10_unified_authority_20260709 import build_unified_field10_authority
    from core.view_model_sync import verify_view_model_sync
    state = {"canonical_selected_symbols":["EURUSD"], "selected_timeframe":"H4"}
    source = pd.DataFrame([{"Symbol":"EURUSD", "Rows":600, "Less-Risky Bias":"BUY"}])
    build_unified_field10_authority(state, source_frame=source, persist=False)
    report = verify_view_model_sync(state)
    assert report["ok"] is True


def test_background_registry_has_required_research_functions():
    from core.background_function_registry import registry_frame
    frame = registry_frame()
    assert len(frame) >= 12
    assert "compute_regime_switch_background" in set(frame["function_name"])
    assert "compute_event_absorption_background" in set(frame["function_name"])
