from __future__ import annotations

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd

import core.field10_daily_snapshot_contract_20260702 as f10
import core.field11_similar_path_simulator_20260702 as f11


def _identity(day: str = "2026-07-02") -> dict:
    cutoff = pd.Timestamp(f"{day} 03:00:00+00:00")
    return {
        "broker_day": day,
        "broker_time": cutoff,
        "cutoff_broker_time": cutoff,
        "latest_completed_h1": cutoff - pd.Timedelta(hours=1),
        "required_cutoff_completed_h1": cutoff - pd.Timedelta(hours=1),
        "locked_until_broker_time": cutoff + pd.Timedelta(days=1),
        "before_cutoff": False,
        "at_or_after_day_end": False,
    }


def _candidate(symbol: str = "EURUSD") -> dict:
    return {
        "symbol": symbol, "role": "MAIN", "daily_grade": "A", "institutional_morning_score": 85.0,
        "existing_rank_score": 80.0, "eligibility_status": "ELIGIBLE", "stable_daily_bias": "BUY",
        "less_risky_bias": "BUY", "trade_permission": "ALLOWED", "higher_standard_regime": "BULL_NORMAL",
        "data_quality_grade": "A", "data_quality_score": 92.0, "regime_probability": 82.0,
        "regime_entropy": 18.0, "posterior_margin": 64.0, "regime_persistence": 86.0,
        "regime_age": 24.0, "expected_regime_duration": 60.0, "estimated_remaining_duration": 36.0,
        "transition_risk_1h": 5.0, "transition_risk_3h": 10.0, "transition_risk_6h": 18.0,
        "calibrated_bias_probability": 78.0, "brier_score": 0.16, "forecast_accuracy_1h": 72.0,
        "forecast_accuracy_3h": 68.0, "forecast_accuracy_6h": 64.0, "technical_bias": "BUY",
        "technical_reliability": 82.0, "sentiment_bias": "BUY", "sentiment_reliability": 70.0,
        "session_bias": "BUY", "session_reliability": 76.0, "evidence_agreement": 84.0,
        "conflict_index": 16.0, "conformal_coverage": 90.0, "conformal_interval_width": 0.002,
        "structural_break_status": "VALID", "changepoint_probability": 12.0, "spread_percentile": 22.0,
        "cvar_95": -0.01, "correlation_cluster": "C1", "duplicate_exposure_penalty": 8.0,
        "frame_validation": {"status": "COMPLETE", "sample_count": 600},
        "identity": {"canonical_run_id": f"RUN-{symbol}", "source_id": f"SRC-{symbol}", "snapshot_hash": f"HASH-{symbol}", "child_run_id": f"CHILD-{symbol}"},
        "score": {"eligibility_reasons": [], "available_weight": 100.0, "missing_weight": 0.0, "calculation_status": "COMPLETE", "score_confidence": 100.0, "components": {}},
        "research_layers": {"spa": {"status": "VALID"}, "pbo": {"status": "INSUFFICIENT_SAMPLE"}},
    }


def _ohlc(rows: int = 1500) -> pd.DataFrame:
    end = pd.Timestamp("2026-07-02 02:00:00+00:00")
    time = pd.date_range(end=end, periods=rows, freq="h")
    x = np.arange(rows, dtype=float)
    close = 1.08 + 0.00001 * x + 0.0015 * np.sin(x / 20.0) + 0.0005 * np.sin(x / 5.0)
    open_ = close - 0.00015 * np.sin(x / 3.0)
    high = np.maximum(open_, close) + 0.0004 + 0.0001 * np.sin(x / 7.0)
    low = np.minimum(open_, close) - 0.0004 - 0.0001 * np.cos(x / 9.0)
    return pd.DataFrame({"time": time, "open": open_, "high": high, "low": low, "close": close, "volume": 1000 + x})


def _state() -> dict:
    candle = "2026-07-02T02:00:00+00:00"
    return {
        "symbol": "EURUSD", "timeframe": "H1", "data": _ohlc(),
        "canonical_decision_result_20260617": {
            "run_id": "RUN-EURUSD", "generation_id": 1, "symbol": "EURUSD", "timeframe": "H1",
            "completed_broker_candle": candle, "snapshot_hash": "HASH-EURUSD",
        },
    }


def _publish(db: Path) -> dict:
    return f10.publish_daily_snapshot_from_records(
        broker_identity=_identity(), ordered_symbols=["EURUSD"], main_symbol="EURUSD",
        parent_run_id="PARENT-1", candidates=[_candidate()], path=db,
    )


def _prepared(tmp_path: Path):
    f10_db = tmp_path / "field10.sqlite3"
    f11_db = tmp_path / "field11.sqlite3"
    _publish(f10_db)
    state = _state()
    report = f11.prepare_field11_index(state, parent_run_id="PARENT-1", symbols=["EURUSD"], path=f11_db, field10_path=f10_db)
    assert report["ok"], report
    return state, f10_db, f11_db, report


def test_01_schema_migration_is_idempotent(tmp_path: Path):
    db = tmp_path / "f11.sqlite3"
    assert f11.migrate_field11_database(db)["ok"]
    assert f11.migrate_field11_database(db)["ok"]
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM field11_schema_migration").fetchone()[0] == 1


def test_02_field11_selector_is_registered_and_closed_first():
    source = Path("ui/lunch_four_core_fields_20260619.py").read_text(encoding="utf-8")
    assert 'FIELD11_FIELD = "11. Open / Close — Similar Path Simulator"' in source
    assert "FIELD10_FIELD, FIELD11_FIELD" in source
    assert 'CLOSED_LUNCH_FIELD = "All Lunch fields closed"' in source


def test_03_ui_uses_local_symbol_key_and_does_not_assign_global_symbol():
    source = Path("ui/lunch_field11_similar_path_20260702.py").read_text(encoding="utf-8")
    assert '_LOCAL_PREFIX = "field11_local_20260702_"' in source
    assert 'state["symbol"] =' not in source
    assert 'st.session_state["symbol"] =' not in source


def test_04_completed_candle_normalization_excludes_future():
    frame = _ohlc(100)
    future = frame.iloc[[-1]].copy()
    future["time"] = pd.Timestamp("2026-07-02 03:00:00+00:00")
    normalized = f11._normalize_ohlc(pd.concat([frame, future]), symbol="EURUSD", latest_completed="2026-07-02 02:00:00+00:00")
    assert normalized["time"].max() == pd.Timestamp("2026-07-02 02:00:00+00:00")


def test_05_constrained_dtw_is_zero_for_identical_path():
    values = [0, 1, 2, 1, 3]
    assert f11.constrained_dtw_distance(values, values, window=1) == 0


def test_06_constrained_dtw_penalizes_opposite_path():
    a = [0, 1, 2, 3, 4]
    b = [0, -1, -2, -3, -4]
    assert f11.constrained_dtw_distance(a, b, window=1) > 1


def test_07_pip_size_rules():
    assert f11.pip_size("EURUSD") == 0.0001
    assert f11.pip_size("USDJPY") == 0.01
    assert f11.pip_size("XAUUSD") == 0.01


def test_08_path_rebasing_preserves_relative_returns():
    rebased = f11.rebase_path([100, 102, 99], 100, 1.2)
    assert np.allclose(rebased, [1.2, 1.224, 1.188])


def test_09_effective_sample_size():
    assert f11.effective_sample_size([0.25, 0.25, 0.25, 0.25]) == 4
    assert f11.effective_sample_size([1, 0, 0, 0]) == 1


def test_10_prepare_index_persists_identity_matched_artifacts(tmp_path: Path):
    state, f10_db, f11_db, report = _prepared(tmp_path)
    identity = f11.resolve_field11_identity(state, field10_path=f10_db)
    manifest = f11.load_index_manifest(identity=identity, path=f11_db)
    assert manifest["index_id"] == report["index_id"]
    assert Path(manifest["feature_path"]).is_file()
    assert Path(manifest["ohlc_path"]).is_file()
    assert "H1" in manifest["supported_timeframes"]


def test_11_identity_guard_rejects_snapshot_mismatch(tmp_path: Path):
    state, f10_db, f11_db, _ = _prepared(tmp_path)
    identity = f11.resolve_field11_identity(state, field10_path=f10_db)
    manifest = f11.load_index_manifest(identity=identity, path=f11_db)
    bad = dict(identity); bad["snapshot_hash"] = "WRONG"
    guard = f11.validate_index_identity(bad, manifest)
    assert not guard["ok"]
    assert "snapshot_hash mismatch" in guard["errors"]


def test_12_simulation_has_no_future_or_overlapping_candidates(tmp_path: Path):
    state, f10_db, f11_db, _ = _prepared(tmp_path)
    result = f11.simulate_field11(state, f11.Field11Selection(symbol="EURUSD", horizon_hours=6, minimum_similarity=0, requested_analogues=30), path=f11_db, field10_path=f10_db)
    assert result["ok"], result
    source = pd.Timestamp(result["summary"]["source_broker_candle"])
    table = result["analogue_records"]
    historical = pd.to_datetime(table["Historical Broker Date"] + " " + table["Historical Broker Hour"], utc=True)
    assert (historical < source - pd.Timedelta(hours=6)).all()


def test_13_simulation_outputs_multiple_scenarios_and_empirical_bands(tmp_path: Path):
    state, f10_db, f11_db, _ = _prepared(tmp_path)
    result = f11.simulate_field11(state, f11.Field11Selection(symbol="EURUSD", horizon_hours=6, minimum_similarity=0, requested_analogues=50, scenario_count=3), path=f11_db, field10_path=f10_db)
    assert result["ok"]
    assert 1 <= len(result["scenarios"]) <= 3
    summary = result["summary"]
    assert len(summary["central_50_low"]) == 7
    assert len(summary["central_80_high"]) == 7


def test_14_simulator_run_is_cached_by_selection_hash(tmp_path: Path):
    state, f10_db, f11_db, _ = _prepared(tmp_path)
    selection = f11.Field11Selection(symbol="EURUSD", horizon_hours=3, minimum_similarity=0)
    first = f11.simulate_field11(state, selection, path=f11_db, field10_path=f10_db)
    second = f11.simulate_field11(state, selection, path=f11_db, field10_path=f10_db)
    assert first["simulator_run_id"] == second["simulator_run_id"]
    assert second["cached"] is True


def test_15_reliability_can_fail_closed():
    grade = f11._reliability_grade(qualified_count=1, ess=1, median_similarity=90, stability={}, drift_status="NORMAL", feature_coverage=100)
    assert grade == "X"


def test_16_drift_block_caps_grade_at_x():
    grade = f11._reliability_grade(qualified_count=100, ess=50, median_similarity=95, stability={"dominant_scenario_stability": 99, "direction_stability": 99}, drift_status="BLOCKED", feature_coverage=100)
    assert grade == "X"


def test_17_settlement_is_idempotent_when_matured_data_exists(tmp_path: Path):
    state, f10_db, f11_db, _ = _prepared(tmp_path)
    # Historical source leaves completed future bars in the immutable artifact.
    source = (_ohlc().iloc[-30]["time"]).isoformat()
    result = f11.simulate_field11(state, f11.Field11Selection(symbol="EURUSD", source_candle=source, horizon_hours=6, minimum_similarity=0), path=f11_db, field10_path=f10_db)
    assert result["ok"]
    first = f11.settle_matured_simulations(path=f11_db)
    second = f11.settle_matured_simulations(path=f11_db)
    assert first["settled_count"] >= 1
    assert second["settled_count"] == 0


def test_18_validation_history_reads_settled_runs(tmp_path: Path):
    state, f10_db, f11_db, _ = _prepared(tmp_path)
    source = (_ohlc().iloc[-30]["time"]).isoformat()
    f11.simulate_field11(state, f11.Field11Selection(symbol="EURUSD", source_candle=source, horizon_hours=6, minimum_similarity=0), path=f11_db, field10_path=f10_db)
    f11.settle_matured_simulations(path=f11_db)
    history = f11.load_validation_history(days=365, path=f11_db)
    assert not history.empty
    assert "Inside 80% Band" in history.columns


def test_19_run_flow_prepares_field11_only_after_field10_publication():
    source = Path("core/multi_symbol_field10_20260701.py").read_text(encoding="utf-8")
    field10_pos = source.index('manifest["field10_daily_snapshot_contract"]')
    field11_pos = source.index('manifest["field11_historical_index"]')
    assert field11_pos > field10_pos
    assert "prepare_field11_index" in source[field10_pos:field11_pos]


def test_20_field11_renderer_contains_no_market_api_or_field10_rerank_call():
    source = Path("ui/lunch_field11_similar_path_20260702.py").read_text(encoding="utf-8")
    assert "prepare_symbol_market_data" not in source
    assert "publish_daily_snapshot" not in source
    assert "run_selected_symbols" not in source
    assert "activate_symbol_result" not in source


def test_21_invalid_slider_state_is_guarded():
    source = Path("ui/lunch_field11_similar_path_20260702.py").read_text(encoding="utf-8")
    assert "if low == high" in source
    assert "disabled=True" in source


def test_22_mobile_default_limits_chart_to_three_scenarios():
    source = Path("ui/lunch_field11_similar_path_20260702.py").read_text(encoding="utf-8")
    assert "for scenario in scenarios[:3]" in source
    assert "all individual analogue paths" not in source.lower()


def test_23_language_guard_avoids_guaranteed_prediction_claims():
    source = Path("ui/lunch_field11_similar_path_20260702.py").read_text(encoding="utf-8")
    assert "not guaranteed" in source.lower()
    assert "Conditional Historical-Analogue Path Projector" in source


def test_24_new_modules_compile():
    import py_compile
    py_compile.compile("core/field11_similar_path_simulator_20260702.py", doraise=True)
    py_compile.compile("ui/lunch_field11_similar_path_20260702.py", doraise=True)
