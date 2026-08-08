from __future__ import annotations

import sqlite3

from core.field10_integrated_evidence_20260702 import TABLE_NAME, migrate_integrated_evidence_database, query_integrated_history


def _insert(conn, parent, child, symbol, timestamp, snapshot, rank):
    conn.execute(
        f"""INSERT INTO {TABLE_NAME}(
        parent_run_id,child_run_id,canonical_run_id,symbol,timeframe,broker_timestamp,broker_date,
        broker_hour,rank,technical_bias,protected_final_action,snapshot_hash,calculation_version,created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (parent, child, child, symbol, "H1", timestamp, timestamp[:10], int(timestamp[11:13]), rank,
         "BUY", "BUY", snapshot, "v-test", "2026-07-02T00:00:00Z"),
    )


def test_field10_integrated_history_persists_filters_and_paginates(tmp_path):
    db = tmp_path / "history.sqlite3"
    migrate_integrated_evidence_database(db)
    with sqlite3.connect(db) as conn:
        _insert(conn, "P1", "C1", "GBPJPY", "2026-07-01T10:00:00+00:00", "H1", 2)
        _insert(conn, "P1", "C2", "USDJPY", "2026-07-01T11:00:00+00:00", "H2", 1)
        _insert(conn, "P2", "C3", "NAS100", "2026-06-30T11:00:00+00:00", "H3", 1)
        conn.commit()
    first_page, total = query_integrated_history(symbols=["GBPJPY", "USDJPY"], limit=1, offset=0, path=db)
    second_page, _ = query_integrated_history(symbols=["GBPJPY", "USDJPY"], limit=1, offset=1, path=db)
    assert total == 2
    assert first_page.iloc[0]["Symbol"] == "USDJPY"
    assert second_page.iloc[0]["Symbol"] == "GBPJPY"
    reopened, reopened_total = query_integrated_history(search="NAS100", complete_export=True, path=db)
    assert reopened_total == 1
    assert reopened.iloc[0]["Symbol"] == "NAS100"


def test_history_schema_has_requested_composite_primary_key_and_indexes(tmp_path):
    db = tmp_path / "schema.sqlite3"
    migrate_integrated_evidence_database(db)
    with sqlite3.connect(db) as conn:
        info = conn.execute(f"PRAGMA table_info({TABLE_NAME})").fetchall()
        indexes = conn.execute(f"PRAGMA index_list({TABLE_NAME})").fetchall()
    pk = [row[1] for row in sorted((row for row in info if row[5]), key=lambda row: row[5])]
    assert pk == ["parent_run_id", "symbol", "timeframe", "broker_timestamp", "child_run_id", "snapshot_hash"]
    assert len(indexes) >= 6
