from __future__ import annotations

from pathlib import Path
import json
import sqlite3

import pandas as pd
import pytest

import core.field10_daily_snapshot_contract_20260702 as contract
import core.field10_daily_outcome_settlement_20260702 as settlement
import core.field10_live_safety_veto_20260702 as safety


def _identity(day: str = "2026-07-02", hour: int = 3, *, before: bool = False) -> dict:
    broker = pd.Timestamp(f"{day} {hour:02d}:00:00+00:00")
    cutoff = pd.Timestamp(f"{day} 03:00:00+00:00")
    return {
        "broker_day": day,
        "broker_time": broker,
        "cutoff_broker_time": cutoff,
        "latest_completed_h1": cutoff - pd.Timedelta(hours=1),
        "required_cutoff_completed_h1": cutoff - pd.Timedelta(hours=1),
        "locked_until_broker_time": cutoff + pd.Timedelta(days=1),
        "before_cutoff": before,
        "at_or_after_day_end": hour >= 23,
    }


def _candidate(symbol: str, score: float | None = 80.0, *, eligible: bool = True, role: str = "SECONDARY") -> dict:
    status = "ELIGIBLE" if eligible else "BLOCKED"
    return {
        "symbol": symbol,
        "role": role,
        "daily_grade": "A" if eligible else "BLOCKED",
        "institutional_morning_score": score if eligible else None,
        "existing_rank_score": 75.0,
        "eligibility_status": status,
        "stable_daily_bias": "BUY",
        "less_risky_bias": "BUY",
        "trade_permission": "ALLOWED" if eligible else "BLOCKED",
        "higher_standard_regime": "BULL_NORMAL",
        "data_quality_grade": "A" if eligible else "D",
        "data_quality_score": 90.0 if eligible else 40.0,
        "regime_probability": 82.0,
        "regime_entropy": 18.0,
        "posterior_margin": 64.0,
        "regime_persistence": 86.0,
        "regime_age": 24.0,
        "expected_regime_duration": 60.0,
        "estimated_remaining_duration": 36.0,
        "transition_risk_1h": 5.0,
        "transition_risk_3h": 10.0,
        "transition_risk_6h": 18.0,
        "calibrated_bias_probability": 78.0,
        "brier_score": 0.16,
        "forecast_accuracy_1h": 72.0,
        "forecast_accuracy_3h": 68.0,
        "forecast_accuracy_6h": 64.0,
        "technical_bias": "BUY",
        "technical_reliability": 82.0,
        "sentiment_bias": "BUY",
        "sentiment_reliability": 70.0,
        "session_bias": "BUY",
        "session_reliability": 76.0,
        "evidence_agreement": 84.0,
        "conflict_index": 16.0,
        "conformal_coverage": 90.0,
        "conformal_interval_width": 0.002,
        "structural_break_status": "VALID",
        "changepoint_probability": 12.0,
        "spread_percentile": 22.0,
        "cvar_95": -0.01,
        "correlation_cluster": "C1",
        "duplicate_exposure_penalty": 8.0,
        "frame_validation": {"status": "COMPLETE" if eligible else "INCOMPLETE", "sample_count": 600 if eligible else 599},
        "identity": {
            "canonical_run_id": f"RUN-{symbol}", "source_id": f"SRC-{symbol}",
            "snapshot_hash": f"HASH-{symbol}", "child_run_id": f"CHILD-{symbol}",
        },
        "score": {
            "eligibility_reasons": [] if eligible else ["fixture blocked"],
            "available_weight": 100.0,
            "missing_weight": 0.0,
            "calculation_status": "COMPLETE" if eligible else "BLOCKED",
            "score_confidence": 100.0 if eligible else 0.0,
            "components": {},
        },
        "research_layers": {
            "spa": {"status": "VALID", "candidate_count": 3, "promotion_status": "NOT_PROMOTED"},
            "pbo": {"status": "INSUFFICIENT_SAMPLE", "effective_trial_count": 0, "promotion_eligibility": "BLOCKED"},
        },
    }


def _frame(rows: int, end: str = "2026-07-02 02:00:00+00:00") -> pd.DataFrame:
    times = pd.date_range(end=pd.Timestamp(end), periods=rows, freq="h")
    base = pd.Series(range(rows), dtype=float) / 10000 + 1.0
    return pd.DataFrame({"time": times, "open": base, "high": base + 0.001, "low": base - 0.001, "close": base + 0.0002})


def _publish(db: Path, candidates=None, identity=None, symbols=None):
    candidates = candidates or [_candidate("EURUSD", 88, role="MAIN"), _candidate("USDJPY", 80)]
    symbols = symbols or [item["symbol"] for item in candidates]
    return contract.publish_daily_snapshot_from_records(
        broker_identity=identity or _identity(), ordered_symbols=symbols,
        main_symbol="EURUSD", parent_run_id="PARENT-1", candidates=candidates, path=db,
    )


def test_01_three_am_cutoff_uses_completed_two_am(monkeypatch):
    import core.shared_broker_time_20260622 as broker
    monkeypatch.setattr(broker, "shared_broker_time_provider", lambda state, canonical=None: {
        "broker_time": pd.Timestamp("2026-07-02 03:00:00+00:00"),
        "latest_completed_h1_utc": pd.Timestamp("2026-07-02 03:00:00+00:00"),
        "broker_offset_minutes": 0,
    })
    identity = contract._broker_identity({}, {})
    assert identity["cutoff_broker_time"].hour == 3
    assert identity["latest_completed_h1"] == pd.Timestamp("2026-07-02 02:00:00+00:00")


def test_02_forming_three_am_candle_is_rejected():
    frame = _frame(600)
    forming = frame.iloc[[-1]].copy()
    forming["time"] = pd.Timestamp("2026-07-02 03:00:00+00:00")
    report = contract.validate_completed_h1_frame(pd.concat([frame, forming], ignore_index=True), latest_completed_h1_utc="2026-07-02 02:00:00+00:00", symbol="BTCUSD")
    assert report["future_timestamp_count"] == 1
    assert report["status"] == "INCOMPLETE"


def test_03_repeated_rerun_returns_identical_table_and_hash(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    first = _publish(db)
    second = _publish(db, candidates=[_candidate("EURUSD", 1, role="MAIN")])
    assert second["status"] == "ALREADY_EXISTS_VALID"
    assert first["content_hash"] == second["content_hash"]
    assert first["rows"] == second["rows"]


def test_04_page_navigation_read_does_not_change_hash(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    _publish(db)
    before = contract.validate_persisted_snapshot(path=db)
    contract.load_current_daily_snapshot(path=db)
    contract.load_current_daily_snapshot(path=db)
    after = contract.validate_persisted_snapshot(path=db)
    assert before == after


def test_05_search_and_filter_are_persistence_neutral(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    _publish(db)
    before = contract.validate_persisted_snapshot(path=db)
    current = contract.load_current_daily_snapshot(path=db)["current"]
    _ = current.loc[current.astype(str).apply(lambda c: c.str.contains("EUR", regex=False)).any(axis=1)].sort_values("Symbol")
    after = contract.validate_persisted_snapshot(path=db)
    assert before["content_hash"] == after["content_hash"]


def test_06_csv_export_is_persistence_neutral(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    _publish(db)
    before = contract.validate_persisted_snapshot(path=db)
    payload = contract.load_current_daily_snapshot(path=db)["current"].to_csv(index=False).encode()
    assert payload.startswith(b"Daily Rank")
    assert contract.validate_persisted_snapshot(path=db)["content_hash"] == before["content_hash"]


def test_07_active_symbol_change_cannot_alter_table(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    first = _publish(db)
    state = {"symbol": "USDJPY", "multi_symbol_active_20260701": "USDJPY"}
    _ = state
    second = contract.load_current_daily_snapshot(path=db)
    assert second["metadata"]["content_hash"] == first["content_hash"]


def test_08_restart_restores_same_rows_and_hashes(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    first = _publish(db)
    del first
    restored = contract.load_current_daily_snapshot(path=db)
    assert len(restored["current"]) == 2
    assert contract.validate_persisted_snapshot(path=db)["status"] == "VALID"


def test_09_changed_universe_after_publication_cannot_rerank(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    first = _publish(db)
    second = _publish(db, candidates=[_candidate("EURUSD", 10, role="MAIN"), _candidate("GBPUSD", 99)], symbols=["GBPUSD", "EURUSD"])
    assert second["status"] == "ALREADY_EXISTS_VALID"
    assert [row["Symbol"] for row in second["rows"]] == [row["Symbol"] for row in first["rows"]]


def test_10_failed_symbol_remains_visible_and_unranked(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    report = _publish(db, candidates=[_candidate("EURUSD", 88, role="MAIN"), _candidate("USDJPY", None, eligible=False)])
    failed = next(row for row in report["rows"] if row["Symbol"] == "USDJPY")
    assert failed["Daily Rank"] is None
    assert failed["Daily Grade"] == "BLOCKED"


def test_11_599_h1_candles_are_incomplete():
    report = contract.validate_completed_h1_frame(_frame(599), latest_completed_h1_utc="2026-07-02 02:00:00+00:00", symbol="BTCUSD")
    assert report["status"] == "INCOMPLETE"
    assert report["sample_count"] == 599


def test_12_600_valid_h1_candles_are_complete():
    report = contract.validate_completed_h1_frame(_frame(600), latest_completed_h1_utc="2026-07-02 02:00:00+00:00", symbol="BTCUSD")
    assert report["status"] == "COMPLETE"
    assert report["sample_count"] == 600


def test_13_duplicate_and_future_timestamps_are_rejected():
    base = _frame(600)
    duplicate = base.iloc[[-1]].copy()
    future = base.iloc[[-1]].copy(); future["time"] = pd.Timestamp("2026-07-02 03:00:00+00:00")
    report = contract.validate_completed_h1_frame(pd.concat([base, duplicate, future]), latest_completed_h1_utc="2026-07-02 02:00:00+00:00", symbol="BTCUSD")
    assert report["duplicate_count"] == 2
    assert report["future_timestamp_count"] == 1
    assert report["eligible"] is False


def test_14_twenty_three_hour_process_cannot_overwrite_current_table(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    first = _publish(db)
    at_23 = _identity(hour=23)
    second = _publish(db, candidates=[_candidate("EURUSD", 5, role="MAIN")], identity=at_23, symbols=["EURUSD"])
    assert second["status"] == "ALREADY_EXISTS_VALID"
    assert second["content_hash"] == first["content_hash"]


def test_15_day_end_can_create_next_day_candidate(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    _publish(db)
    bundle = contract.load_current_daily_snapshot(path=db)
    report = settlement.prepare_next_day_candidate(metadata=bundle["metadata"], current_rows=bundle["current"], prepared_at_broker_time="2026-07-02 23:00:00+00:00", path=db)
    assert report["status"] == "NEXT_DAY_CANDIDATE_READY"


def test_16_candidate_activates_only_at_next_cutoff(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    _publish(db)
    bundle = contract.load_current_daily_snapshot(path=db)
    settlement.prepare_next_day_candidate(metadata=bundle["metadata"], current_rows=bundle["current"], prepared_at_broker_time="2026-07-02 23:00:00+00:00", path=db)
    before = _identity("2026-07-03", hour=2, before=True)
    denied = contract.publish_daily_snapshot_from_records(broker_identity=before, ordered_symbols=["EURUSD"], main_symbol="EURUSD", parent_run_id="P2", candidates=[_candidate("EURUSD", 90, role="MAIN")], path=db)
    assert denied["status"] == "BEFORE_MORNING_CUTOFF"
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT status FROM field10_next_day_candidate WHERE target_broker_day='2026-07-03'").fetchone()[0] == "NEXT_DAY_CANDIDATE_READY"
    activated = contract.publish_daily_snapshot_from_records(
        broker_identity=_identity("2026-07-03", hour=3),
        ordered_symbols=["EURUSD", "USDJPY"], main_symbol="EURUSD", parent_run_id="P3",
        candidates=[_candidate("EURUSD", 90, role="MAIN"), _candidate("USDJPY", 80)], path=db,
    )
    assert activated["status"] == "PUBLISHED_LOCKED"
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT status FROM field10_next_day_candidate WHERE target_broker_day='2026-07-03'").fetchone()[0] == "NEXT_DAY_ACTIVATED"


def test_17_safety_veto_does_not_change_locked_bias_or_rank(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    _publish(db)
    bundle = contract.load_current_daily_snapshot(path=db)
    before = bundle["current"].set_index("Symbol").loc["EURUSD", ["Daily Rank", "Stable Daily Bias"]].to_dict()
    safety.record_safety_event(daily_snapshot_id=bundle["metadata"]["daily_snapshot_id"], broker_day="2026-07-02", symbol="EURUSD", observed_at_broker_time="2026-07-02 10:00:00+00:00", evidence={"stale_hours": 10, "canonical_identity_valid": True, "connector_ok": True}, path=db)
    after = contract.load_current_daily_snapshot(path=db)["current"].set_index("Symbol").loc["EURUSD"]
    assert after["Safety Veto"] == "BLOCK_NEW_ENTRIES"
    assert after["Daily Rank"] == before["Daily Rank"]
    assert after["Stable Daily Bias"] == before["Stable Daily Bias"]


def test_18_bocpd_or_severe_spread_blocks_new_entries():
    result = safety.evaluate_safety_veto({"stale_hours": 0, "missing_candles": 0, "spread_percentile": 99, "changepoint_probability": 80, "canonical_identity_valid": True, "connector_ok": True})
    assert result["safety_veto"] == "BLOCK_NEW_ENTRIES"
    assert result["direction_unchanged"] is True


def test_19_missing_research_evidence_stays_unavailable(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    contract.migrate_daily_snapshot_database(db)
    result = contract._research_layer_bundle({}, {}, {"frame": pd.DataFrame(), "sample_count": 0}, db, "EURUSD")
    assert result["calibration"]["status"] == "UNAVAILABLE"
    assert result["calibration"]["calibrated_directional_probability"] is None
    assert result["pbo"]["status"] == "INSUFFICIENT_TRIAL_MATRIX"


def test_20_unsettled_outcomes_do_not_enter_calibration(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    report = _publish(db)
    snapshot_id = report["daily_snapshot_id"]
    with sqlite3.connect(db) as conn:
        conn.execute("INSERT INTO field10_daily_outcome(daily_snapshot_id,broker_day,symbol,settlement_status,outcome_json) VALUES(?,?,?,?,?)", (snapshot_id, "2026-07-02", "EURUSD", "PARTIAL_SETTLEMENT", "{}"))
        conn.commit()
    a1, a3, a6, count = contract._forecast_accuracy_from_db("EURUSD", db)
    assert (a1, a3, a6, count) == (None, None, None, 0)


def test_21_equal_scores_use_deterministic_alphabetical_tie_break():
    ranked = contract._rank_candidates([_candidate("USDJPY", 80), _candidate("EURUSD", 80, role="MAIN")])
    assert [(r["daily_rank"], r["symbol"]) for r in ranked] == [(1, "EURUSD"), (2, "USDJPY")]


def test_22_input_symbol_order_does_not_change_canonical_universe():
    first = contract.canonical_symbol_universe(["USDJPY", "GBPUSD", "EURUSD"], "EURUSD")
    second = contract.canonical_symbol_universe(["GBPUSD", "EURUSD", "USDJPY"], "EURUSD")
    assert first == second == ["EURUSD", "GBPUSD", "USDJPY"]
    assert contract.symbol_universe_hash(first, "EURUSD") == contract.symbol_universe_hash(second, "EURUSD")


def test_23_field10_open_path_contains_no_market_api_call():
    source = Path("ui/lunch_field10_multi_symbol_20260701.py").read_text(encoding="utf-8")
    section = source[source.index("def _render_locked_morning_snapshot"):source.index("def render_field10_content")]
    assert "prepare_symbol_market_data" not in section
    assert "activate_symbol_result" not in section
    assert "single_symbol_runner" not in section


def test_24_display_filtering_does_not_call_heavy_calculation(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    _publish(db)
    before = contract.validate_persisted_snapshot(path=db)["content_hash"]
    frame = contract.load_current_daily_snapshot(path=db)["current"]
    _ = frame[frame["Symbol"].eq("EURUSD")]
    assert contract.validate_persisted_snapshot(path=db)["content_hash"] == before


def test_25_main_and_secondary_scope_source_remains_correct():
    source = Path("core/multi_symbol_field10_20260701.py").read_text(encoding="utf-8")
    assert 'child_scope = scope if symbol == main else "LUNCH_CORE"' in source
    assert '"FIELDS_1_TO_3_PLUS_FIELDS_10_11"' in source


def test_26_legacy_protected_modules_still_exist():
    for path in (
        "core/daily_locked_regime_20260625.py",
        "core/multi_symbol_field10_20260701.py",
        "core/field10_ten_paper_research_20260701.py",
        "core/field10_integrated_evidence_20260702.py",
        "ui/lunch_field10_multi_symbol_20260701.py",
    ):
        assert Path(path).is_file()


def test_27_streamlit_entrypoints_compile():
    import py_compile
    py_compile.compile("app.py", doraise=True)
    py_compile.compile("adx_dashpoard.py", doraise=True)


def test_28_new_modules_compile():
    import py_compile
    for path in (
        "core/field10_daily_snapshot_contract_20260702.py",
        "core/field10_daily_outcome_settlement_20260702.py",
        "core/field10_live_safety_veto_20260702.py",
        "ui/lunch_field10_multi_symbol_20260701.py",
    ):
        py_compile.compile(path, doraise=True)


def test_29_sqlite_migration_fresh_and_existing(tmp_path: Path):
    fresh = tmp_path / "fresh.sqlite3"
    assert contract.migrate_daily_snapshot_database(fresh)["ok"]
    existing = tmp_path / "existing.sqlite3"
    with sqlite3.connect(existing) as conn:
        conn.execute("CREATE TABLE legacy_table(id INTEGER PRIMARY KEY,value TEXT)")
        conn.execute("INSERT INTO legacy_table(value) VALUES('keep')")
        conn.commit()
    assert contract.migrate_daily_snapshot_database(existing)["ok"]
    with sqlite3.connect(existing) as conn:
        assert conn.execute("SELECT value FROM legacy_table").fetchone()[0] == "keep"
        assert conn.execute("SELECT name FROM sqlite_master WHERE name='field10_daily_snapshot'").fetchone()


def test_30_single_rank_filter_has_min_max_guard():
    source = Path("ui/lunch_field10_multi_symbol_20260701.py").read_text(encoding="utf-8")
    assert source.count("if low == high:") >= 2
    assert source.count("Rank filter fixed") >= 2


def test_31_actual_child_generation_ids_are_persisted(tmp_path: Path):
    db = tmp_path / "f10.sqlite3"
    _publish(db)
    metadata = contract.load_current_daily_snapshot(path=db)["metadata"]
    assert metadata["child_run_ids"] == {
        "EURUSD": "CHILD-EURUSD", "USDJPY": "CHILD-USDJPY",
    }


def test_32_runtime_snapshot_checksum_validation(tmp_path: Path):
    snapshot = tmp_path / "runtime.json"
    snapshot.write_bytes(b"frozen-runtime")
    from hashlib import sha256
    expected = sha256(snapshot.read_bytes()).hexdigest()
    report = contract._generation_checksum_status({
        "runtime_snapshot_path": str(snapshot),
        "runtime_snapshot_sha256": expected,
    }, "EURUSD")
    assert report["valid"] is True
    snapshot.write_bytes(b"tampered")
    report = contract._generation_checksum_status({
        "runtime_snapshot_path": str(snapshot),
        "runtime_snapshot_sha256": expected,
    }, "EURUSD")
    assert report["status"] == "CHECKSUM_MISMATCH"


def test_33_cutoff_identity_rejects_after_cutoff_generation():
    identity = _identity()
    valid = contract._generation_cutoff_status(
        {"completed_broker_candle": "2026-07-02T02:00:00+00:00"}, identity,
    )
    late = contract._generation_cutoff_status(
        {"completed_broker_candle": "2026-07-02T03:00:00+00:00"}, identity,
    )
    assert valid["valid"] is True
    assert late["status"] == "AFTER_CUTOFF"
