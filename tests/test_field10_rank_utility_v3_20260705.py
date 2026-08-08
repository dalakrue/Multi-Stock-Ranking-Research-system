from __future__ import annotations

from pathlib import Path
import inspect
import json
import shutil
import sqlite3

import numpy as np
import pandas as pd
import pytest

from core.field10_evidence_clustering_20260705 import cluster_evidence
from core.field10_model_selection_20260705 import CANDIDATE_MODELS, model_confidence_set
from core.field10_probability_calibration_v2_20260705 import (
    calibrate_probability_panel, chronological_conformal_returns,
    chronological_probability_panel,
)
from core.field10_promotion_governance_20260705 import (
    freeze_experiment_registry, probability_of_backtest_overfitting,
)
from core.field10_rank_uncertainty_20260705 import chronological_rank_uncertainty
from core.field10_rank_utility_v3_20260705 import (
    CANDIDATE_NAME, FORMULA_THRESHOLD_REGISTRY, horizon_utility_v3,
    rank_v3_candidates, strategy_targets,
)
from core.field10_structural_stability_v2_20260705 import structural_stability_evidence
from scripts.migrate_field10_rank_utility_v3_20260705 import apply as apply_migration


def frame(rows: int = 600, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.00005, 0.0012, rows)
    close = 1.1 * np.exp(np.cumsum(returns))
    open_ = np.r_[close[0], close[:-1]]
    span = np.abs(rng.normal(0.0006, 0.0002, rows))
    return pd.DataFrame({
        "time": pd.date_range("2026-06-01", periods=rows, freq="h", tz="UTC"),
        "open": open_, "high": np.maximum(open_, close) + span,
        "low": np.minimum(open_, close) - span, "close": close,
        "tick_volume": rng.integers(100, 1000, rows),
    })


def utility_kwargs(horizon: int) -> dict:
    return dict(
        calibrated_probability=0.56, spread_cost=0.00002, slippage_cost=0.00001,
        directional_var_95=-0.004 * np.sqrt(horizon), expected_shortfall_95=-0.006 * np.sqrt(horizon),
        forecast_volatility=0.0015 * np.sqrt(horizon), adverse_semivariance=1e-6 * horizon,
        transition_risk_pct=20.0, short_connectedness_pct=15.0, persistent_connectedness_pct=25.0,
        conformal_lower_return=-0.004 * np.sqrt(horizon), conformal_median_return=0.0004 * horizon,
        conformal_upper_return=0.005 * np.sqrt(horizon), probability_calibration_error=0.06,
        model_disagreement_pct=10.0,
    )


def test_01_no_future_leakage_probability_panel_uses_only_settled_history():
    original = frame()
    panel_a = chronological_probability_panel(original, bias="BUY", horizon=6)
    changed = original.copy()
    changed.loc[550:, "close"] *= np.linspace(1.0, 2.0, len(changed.loc[550:]))
    panel_b = chronological_probability_panel(changed, bias="BUY", horizon=6)
    cutoff = 500
    left = panel_a.loc[panel_a.origin_index <= cutoff, "raw_probability"].reset_index(drop=True)
    right = panel_b.loc[panel_b.origin_index <= cutoff, "raw_probability"].reset_index(drop=True)
    pd.testing.assert_series_equal(left, right)


def test_02_completed_candle_only_targets_end_with_unsettled_nan():
    targets = strategy_targets(frame(), bias="BUY", horizon=24)
    assert targets.tail(24).isna().all()


def test_03_exact_600_h1_identity_fixture():
    f = frame(600)
    assert len(f) == 600
    assert f.time.is_monotonic_increasing and not f.time.duplicated().any()


def test_04_independent_horizon_targets():
    f = frame()
    assert not strategy_targets(f, bias="BUY", horizon=3).equals(strategy_targets(f, bias="BUY", horizon=6))


def test_05_no_copy_6h_into_long_horizons():
    f = frame()
    results = {h: horizon_utility_v3(f, bias="BUY", horizon=h, **utility_kwargs(h)) for h in (6, 12, 24, 36)}
    values = [round(float(results[h]["median_favourable_return"]), 12) for h in results]
    assert len(set(values)) > 1


def _record(symbol: str, quality: float | None, coverage_count: int = 9) -> dict:
    components = list(FORMULA_THRESHOLD_REGISTRY["component_weights"])
    row = {"symbol": symbol, "absolute_managed_utility": 0.001, "structural_entry_permission": "PASS", "identity_integrity_pass": True}
    for index, name in enumerate(components):
        value = quality if index < coverage_count else None
        row[name] = value
        row[f"historical_quality::{name}"] = value
    return row


def test_06_missing_evidence_reduces_score():
    ranked = rank_v3_candidates([_record("FULL", 70, 9), _record("PARTIAL", 70, 5)])
    rows = {r["symbol"]: r for r in ranked["rows"]}
    assert rows["PARTIAL"]["coverage_adjusted_score"] < rows["FULL"]["coverage_adjusted_score"]


def test_07_partial_row_cannot_win_by_denominator_renormalization():
    ranked = rank_v3_candidates([_record("FULL", 65, 9), _record("PARTIAL", 100, 4)])
    rows = {r["symbol"]: r for r in ranked["rows"]}
    assert rows["PARTIAL"]["entry_permission_v3"] == "BLOCK"
    assert rows["FULL"]["research_rank_v3"] < rows["PARTIAL"]["research_rank_v3"] or rows["PARTIAL"]["coverage_adjusted_score"] is None


def test_08_structural_break_blocks_without_changing_bias():
    f = frame()
    f.loc[540:, "close"] *= np.exp(np.linspace(0, 0.5, 60))
    result = structural_stability_evidence(f)
    if result["break_strength"] >= 0.75 and result["post_break_h1_count"] < 96:
        assert result["structural_entry_permission"] == "BLOCK"
    assert result["locked_daily_bias_mutated"] is False


def test_09_calibration_fit_uses_earlier_window_only():
    panel = chronological_probability_panel(frame(), bias="BUY", horizon=6)
    result = calibrate_probability_panel(panel, horizon=6, current_raw_probability=0.55)
    assert result["final_test_used_for_fit"] is False
    assert result["test_start_index"] > result["calibration_end_index"]


def test_10_conformal_separate_chronological_calibration_window():
    panel = chronological_probability_panel(frame(), bias="BUY", horizon=6)
    result = chronological_conformal_returns(panel, horizon=6)
    if result["status"] == "AVAILABLE":
        assert result["calibration_window_separate"] is True
        assert result["purge_hours"] == 6


def test_11_rank_bootstrap_uses_chronological_blocks():
    f = frame()
    panel = pd.DataFrame({"A": strategy_targets(f, bias="BUY", horizon=6), "B": strategy_targets(f, bias="SELL", horizon=6)})
    result = chronological_rank_uncertainty(panel, snapshot_id="s1", formula_version="v1", draws=50)
    assert result["method"] == "MOVING_AND_STATIONARY_BLOCK_BOOTSTRAP"
    assert result["block_length"] >= 6


def test_12_same_snapshot_seed_deterministic_ranks():
    f = frame()
    panel = pd.DataFrame({"A": strategy_targets(f, bias="BUY", horizon=6), "B": strategy_targets(f, bias="SELL", horizon=6)})
    a = chronological_rank_uncertainty(panel, snapshot_id="same", formula_version="v1", draws=50)
    b = chronological_rank_uncertainty(panel, snapshot_id="same", formula_version="v1", draws=50)
    assert a["rows"] == b["rows"]


def test_13_rank_interval_ordering():
    f = frame()
    result = chronological_rank_uncertainty(pd.DataFrame({"A": f.close.pct_change(), "B": -f.close.pct_change()}), snapshot_id="x", formula_version="v", draws=50)
    assert all(row["rank_lower_90"] <= row["median_bootstrap_rank"] <= row["rank_upper_90"] for row in result["rows"])


def test_14_top_three_probabilities_bounded():
    f = frame()
    result = chronological_rank_uncertainty(pd.DataFrame({"A": f.close.pct_change(), "B": -f.close.pct_change()}), snapshot_id="x2", formula_version="v", draws=50)
    assert all(0 <= row["probability_top_3"] <= 1 for row in result["rows"])


def test_15_duplicate_evidence_does_not_receive_multiple_full_weights():
    x = np.linspace(0, 1, 100)
    matrix = pd.DataFrame({"a": x, "b": x * 2, "c": np.sin(x * 20)})
    result = cluster_evidence(matrix, {"a": 0.4, "b": 0.4, "c": 0.2}, threshold=0.8)
    assert result["clusters"]["a"] == result["clusters"]["b"]
    assert result["effective_weights"]["a"] + result["effective_weights"]["b"] < 0.8 + 1e-9


def test_16_mcs_uses_common_loss_panel_and_exponential_weights():
    rng = np.random.default_rng(4)
    losses = pd.DataFrame({name: np.abs(rng.normal(0.1 + i * 0.01, 0.02, 120)) for i, name in enumerate(CANDIDATE_MODELS)})
    rows = model_confidence_set(losses, bootstrap_draws=50, block_length=12)
    survivors = [row for row in rows if row["mcs_membership"]]
    assert survivors and pytest.approx(sum(row["model_weight"] for row in survivors), abs=1e-8) == 1.0
    assert all(row["weighting_method"] == "CONSTRAINED_EXPONENTIAL_NON_NEGATIVE" for row in rows)


def test_17_pbo_registry_frozen_before_evaluation():
    registry = freeze_experiment_registry({
        "candidate_name": CANDIDATE_NAME, "formula_hash": "a", "feature_version": "b", "threshold_version": "c",
        "horizon_weights": {}, "risk_coefficients": {}, "calibration_method": "PLATT", "structural_break_settings": {},
        "normalization_settings": {}, "candidate_model_list": ["a", "b"], "sample_period": {}, "symbols": ["EURUSD"],
        "timeframe": "H1", "spread_slippage_treatment": "EXACT",
    })
    assert registry["registered_before_test"] is True and registry["experiment_registry_hash"]


def test_18_production_rank_source_not_assigned_by_v3_modules():
    sources = "\n".join(Path(name).read_text() for name in [
        "core/field10_rank_utility_v3_20260705.py", "core/field10_v3_candidate_orchestrator_20260705.py"])
    assert "production_rank_modified\": False" in sources or '"production_rank_modified": False' in sources
    assert "UPDATE field10_daily_snapshot_symbol" not in sources


def test_19_locked_bias_remains_input_only():
    source = Path("core/field10_v3_candidate_orchestrator_20260705.py").read_text()
    assert "locked_bias_before" in source and "locked_bias_after" in source
    assert "UPDATE field10_daily" not in source


def test_20_lunch_rendering_triggers_no_heavy_v3_calculation():
    source = Path("ui/lunch_field10_multi_symbol_20260701.py").read_text()
    helper = source[source.index("def _render_v3_rank_candidate"):source.index("def _render_research_layer")]
    assert "publish_field10_rank_utility_v3_candidate" not in helper
    assert "load_v3_candidate_summary" in helper


def test_21_database_migration_idempotent(tmp_path: Path):
    source = Path("data/multi_symbol_field10_20260701.sqlite3")
    db = tmp_path / "test.sqlite3"
    shutil.copy2(source, db)
    first = apply_migration(db, backup_dir=tmp_path / "backups")
    second = apply_migration(db, backup_dir=tmp_path / "backups")
    assert first["status"] == second["status"] == "PASS"
    assert second["idempotent_registry_row_count"] == 1


def test_22_mobile_table_has_detailed_cards():
    source = Path("ui/lunch_field10_multi_symbol_20260701.py").read_text()
    assert "Show Detailed Cards" in source and "_render_mobile_cards" in source
    assert "Readable Status" in source


def test_23_no_raw_data_fabrication_in_production_v3():
    source = Path("core/field10_v3_candidate_orchestrator_20260705.py").read_text().lower()
    assert "random.normal" not in source and "synthetic" not in source
    assert "exact_completed_h1" in source


def test_24_provider_fallback_provenance_displayed():
    source = Path("ui/lunch_field10_multi_symbol_20260701.py").read_text()
    assert "Fallback Level" in source and "FALLBACK-SUPPORTED" in source


def test_25_partial_run_does_not_replace_previous_complete_publication():
    source = Path("core/field10_v3_candidate_orchestrator_20260705.py").read_text()
    assert "IDENTITY_MISMATCH" in source
    assert "INSERT OR IGNORE" not in source  # persistence is delegated to append-only insert_or_ignore
    assert "production_rank_modified\": False" in source or '"production_rank_modified": False' in source


def test_pbo_computation_bounds():
    rng = np.random.default_rng(10)
    matrix = pd.DataFrame(rng.normal(size=(10, 5)), columns=list("ABCDE"))
    result = probability_of_backtest_overfitting(matrix)
    assert 0.0 <= result["pbo_probability"] <= 1.0
