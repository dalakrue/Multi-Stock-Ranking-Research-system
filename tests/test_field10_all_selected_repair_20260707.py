from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def _seed_completed_child(db: Path, *, symbol: str = "EURUSD", parent: str = "P-OLD", child: str = "C-OLD") -> dict[str, str]:
    from core.child_generation_contract_20260702 import migrate_child_publication_contract

    migrate_child_publication_contract(db)
    identity = {
        "parent_run_id": parent,
        "child_run_id": child,
        "symbol": symbol,
        "timeframe": "H4",
        "canonical_run_id": "RUN-1",
        "snapshot_hash": "HASH-1",
        "completed_candle": "2026-07-06T16:00:00+00:00",
    }
    now = "2026-07-06T16:01:00+00:00"
    with sqlite3.connect(db) as conn:
        conn.execute(
            """INSERT INTO child_generation_registry(
                parent_run_id,child_run_id,symbol,timeframe,canonical_run_id,source_id,
                snapshot_hash,completed_broker_candle,valid_until,runtime_snapshot_path,
                runtime_snapshot_sha256,bundle_fingerprint,calculation_status,
                publication_status,diagnostic,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                parent, child, symbol, "H4", "RUN-1", f"SRC-{symbol}", "HASH-1",
                identity["completed_candle"], "2026-07-06T20:00:00+00:00", "/tmp/example.gz",
                "sha", "fingerprint", "COMPLETED", "COMPLETED", "{}", now, now,
            ),
        )
        conn.execute(
            """INSERT INTO field3_standard_evidence(
                parent_run_id,child_run_id,symbol,timeframe,canonical_run_id,snapshot_hash,
                broker_timestamp,standard,evidence_json,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                parent, child, symbol, "H4", "RUN-1", "HASH-1", identity["completed_candle"],
                "Higher Standard", json.dumps({"Bias": "BUY", "Regime": "BULL", "Reliability": 82}), now,
            ),
        )
        # Minimal exact-identity table used by reload validation.
        conn.execute(
            """CREATE TABLE IF NOT EXISTS field10_integrated_evidence_history(
                parent_run_id TEXT,child_run_id TEXT,symbol TEXT,timeframe TEXT,
                canonical_run_id TEXT,snapshot_hash TEXT,broker_timestamp TEXT
            )"""
        )
        conn.execute(
            "INSERT INTO field10_integrated_evidence_history VALUES(?,?,?,?,?,?,?)",
            (parent, child, symbol, "H4", "RUN-1", "HASH-1", identity["completed_candle"]),
        )
        conn.commit()
    return identity


def test_guest_defaults_and_empty_selector_run_fallback_are_unlocked():
    from core.multi_symbol_run_groups_20260706 import DEFAULT_GROUPS, initialize_groups, resolve_run_symbols

    state: dict[str, object] = {}
    groups = initialize_groups(state)
    assert groups == DEFAULT_GROUPS

    state["multi_symbol_third_selected_20260706"] = []
    assert resolve_run_symbols(state, "FULL") == []


def test_settings_buttons_are_not_disabled_by_empty_groups_and_progress_precedes_connectors():
    source = Path("tabs/antd_page_router_20260615.py").read_text(encoding="utf-8")
    assert "disabled=run_locked_20260624 or not first_group_20260706" not in source
    assert "disabled=run_locked_20260624 or not second_group_20260706" not in source
    assert "disabled=run_locked_20260624 or not third_group_20260706" not in source
    assert source.index('st.markdown("### ⚡ Instant Run Engine")') < source.index('st.markdown("### Connections, API Keys and Provider Health")')
    assert "_open_lunch_ai_after_settings_run(used_previous=nested_status != \"COMPLETED\")" in source


def test_reload_validation_accepts_only_exact_symbol_database_publication(tmp_path: Path):
    from core.child_snapshot_publication_20260706 import _has_field10

    db = tmp_path / "exact.sqlite3"
    identity = _seed_completed_child(db)
    assert _has_field10({}, "EURUSD", db_path=db, identity=identity)
    assert not _has_field10({}, "USDJPY", db_path=db, identity={**identity, "symbol": "USDJPY"})


def test_latest_completed_exact_symbol_is_recovered_across_parent_runs(tmp_path: Path):
    from core.child_generation_contract_20260702 import load_latest_child_contract_tables

    db = tmp_path / "latest.sqlite3"
    _seed_completed_child(db, symbol="EURCHF", parent="P-FIRST", child="C-FIRST")
    loaded = load_latest_child_contract_tables(path=db, symbol="EURCHF", timeframe="H4")
    assert loaded["ok"]
    assert loaded["metadata"]["parent_run_id"] == "P-FIRST"
    higher = loaded["field3_current"]
    assert higher.loc[higher["Standard"] == "Higher Standard", "Bias"].iloc[0] == "BUY"


def test_repair_migration_seeds_defaults_and_exact_lookup_indexes(tmp_path: Path):
    from core.field10_multi_symbol_repair_migration_20260707 import migrate_field10_multi_symbol_repair
    from core.multi_symbol_run_groups_20260706 import DEFAULT_GROUPS, load_group_preferences

    db = tmp_path / "migration.sqlite3"
    report = migrate_field10_multi_symbol_repair(db)
    assert report["ok"]
    saved = load_group_preferences(db)
    assert saved["first"] == DEFAULT_GROUPS["FIRST"]
    assert saved["second"] == DEFAULT_GROUPS["SECOND"]
    assert saved["third"] == DEFAULT_GROUPS["THIRD"]
    with sqlite3.connect(db) as conn:
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(child_generation_registry)").fetchall()}
    assert "idx_child_generation_latest_exact_20260707" in indexes


def test_operational_sync_stamps_nested_adapters_and_reports_one_generation():
    from core.operational_sync_20260618 import collect_sync_health, synchronize_published_generation

    canonical = {
        "run_id": "RUN-SYNC-1",
        "calculation_generation": 7,
        "data_signature": "SIG-7",
        "symbol": "EURUSD",
        "timeframe": "H4",
        "source": "TEST",
        "latest_completed_candle_time": "2026-07-06T16:00:00+00:00",
        "final_decision": {"final_decision": "WAIT"},
        "full_metric_snapshot": {"major_regime": "RANGE"},
    }
    # Nested NLP intentionally has no identity, matching the real pre-fix shape.
    adapter = {
        "nlp": {"summary": {"ranked_items": 0}},
        "regime": {"current": "RANGE"},
        "full_metric_snapshot": {},
    }
    state: dict[str, object] = {
        "canonical_decision_result_20260617": canonical,
        "adx_shared_calc_result_20260615": adapter,
    }
    synchronize_published_generation(state, canonical, adapter)
    rows = collect_sync_health(state)
    core_rows = {row["Component"]: row for row in rows[:8]}
    assert core_rows["Shared adapter"]["Status"] == "SYNCED"
    assert core_rows["NLP"]["Status"] == "SYNCED"
    assert core_rows["Regime history"]["Status"] == "SYNCED"
    assert state["nlp_synced_adapter_20260618"]["run_id"] == "RUN-SYNC-1"
    assert state["full_metric_synced_snapshot_20260618"]["major_regime"] == "RANGE"


def test_lightweight_shared_adapter_source_carries_full_canonical_identity():
    source = Path("core/adx_shared_sync_20260615.py").read_text(encoding="utf-8")
    for field in (
        '"run_id": canonical.get("run_id")',
        '"calculation_generation": canonical.get("calculation_generation")',
        '"data_signature": canonical.get("data_signature")',
        '"full_metric_snapshot": canonical.get("full_metric_snapshot", {})',
    ):
        assert field in source
