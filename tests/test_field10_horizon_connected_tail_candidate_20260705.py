from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import shutil
import sqlite3

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.field10_research_common_20260705 import (
    CanonicalIdentity, HORIZONS, MODEL_VERSION, REQUIRED_H1_ROWS, deterministic_hash,
)
from core.field10_har_semivariance_20260705 import har_h1_forecasts, realized_semivariance
from core.field10_gas_tailrisk_20260705 import bounded_gas_update, directional_var_es
from core.field10_fx_connectedness_20260705 import (
    FREQUENCY_BANDS, duplicate_currency_exposure, full_connectedness_bundle,
)
from core.field10_model_selection_20260705 import (
    CANDIDATE_MODELS, candidate_registry_hash, chronological_sample_splits,
    model_confidence_set,
)
from core.field10_rank_utility_v2_20260705 import horizon_managed_utility, rank_shadow_candidates
from core.field10_research_orchestrator_20260705 import _finalize
from core.field10_institutional_shadow_20260704 import normalize_completed_h1
from scripts.migrate_field10_horizon_connected_tail_20260705 import apply as apply_migration

LIVE_DB = ROOT / "data" / "multi_symbol_field10_20260701.sqlite3"


def synthetic_h1(rows: int = 600, seed: int = 42, *, end: str = "2026-07-05T10:00:00Z") -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    time = pd.date_range(end=pd.Timestamp(end), periods=rows, freq="h", tz="UTC")
    # Negative jumps make positive and negative semivariance observably asymmetric.
    returns = rng.normal(0.00008, 0.0008, rows)
    returns[::37] -= 0.0045
    close = 1.10 * np.exp(np.cumsum(returns))
    opening = np.r_[close[0], close[:-1]]
    return pd.DataFrame({
        "time": time,
        "open": opening,
        "high": np.maximum(opening, close) * 1.0003,
        "low": np.minimum(opening, close) * 0.9997,
        "close": close,
        "tick_volume": rng.integers(100, 800, rows),
        "spread": 0.00008,
    })


def identity(symbol: str = "EURUSD") -> CanonicalIdentity:
    return CanonicalIdentity(
        daily_snapshot_id="TEST-SNAPSHOT", parent_run_id="TEST-RUN", child_run_id="TEST-CHILD",
        canonical_run_id="TEST-CANONICAL", symbol=symbol, timeframe="H1", broker_day="2026-07-05",
        completed_h1_candle="2026-07-05T10:00:00+00:00", source_id=f"SRC-{symbol}",
        source_hash=f"HASH-{symbol}", snapshot_hash=f"SNAP-{symbol}", universe_hash="UNIVERSE",
        ordered_symbol_universe=(symbol,),
    )


def test_no_forming_candle_is_used():
    frame = synthetic_h1(601, end="2026-07-05T11:00:00Z")
    result, reasons = normalize_completed_h1(
        frame, cutoff="2026-07-05T10:00:00Z", max_rows=600, required_rows=600,
    )
    assert not reasons
    assert len(result) == 600
    assert result["time"].max() == pd.Timestamp("2026-07-05T10:00:00Z")
    assert pd.Timestamp("2026-07-05T11:00:00Z") not in set(result["time"])


def test_har_uses_independent_horizon_targets_and_exact_window():
    result = har_h1_forecasts(synthetic_h1())
    assert result["status"] == "AVAILABLE"
    assert result["horizon_independence"] is True
    assert set(result["horizons"]) == set(HORIZONS)
    assert len({result["horizons"][h]["target_hash"] for h in HORIZONS}) == len(HORIZONS)
    assert result["sample_count"] == REQUIRED_H1_ROWS


def test_har_does_not_copy_one_horizon_into_another():
    result = har_h1_forecasts(synthetic_h1(seed=11))
    forecasts = [result["horizons"][h]["forecast_volatility"] for h in HORIZONS]
    assert len({round(float(v), 12) for v in forecasts if v is not None}) > 2


def test_semivariance_proxy_is_explicit_and_missing_not_zero():
    result = realized_semivariance(synthetic_h1(), None)
    assert result["semivariance_method"] == "H1_SIGNED_VARIANCE_PROXY"
    assert result["semivariance_validation_status"] == "PROXY_RELIABILITY_PENALTY"
    assert result["missing_reason"]
    assert result["positive_realized_semivariance"] is not None
    assert result["negative_realized_semivariance"] is not None


def test_buy_and_sell_tail_risk_differ_under_asymmetry():
    frame = synthetic_h1(seed=7)
    buy = directional_var_es(frame, bias="BUY")["horizons"][6]
    sell = directional_var_es(frame, bias="SELL")["horizons"][6]
    assert buy["directional_expected_shortfall_95"] != sell["directional_expected_shortfall_95"]
    assert buy["directional_var_95"] != sell["directional_var_95"]


def test_tail_backtest_purge_and_embargo_equal_horizon():
    result = directional_var_es(synthetic_h1(), bias="BUY")["horizons"]
    for horizon in HORIZONS:
        assert result[horizon]["purge_hours"] == horizon
        assert result[horizon]["embargo_hours"] == horizon
        assert result[horizon]["training_rows_strictly_before_origin"] is True


def test_gas_is_bounded_deterministic_and_cannot_modify_bias():
    returns = np.log(synthetic_h1()["close"] / synthetic_h1()["close"].shift(1)).dropna()
    first = bounded_gas_update(returns, transition_risk=70, reliability=80)
    second = bounded_gas_update(returns, transition_risk=70, reliability=80)
    assert first == second
    assert first["locked_bias_modified"] is False
    for row in first["states"].values():
        assert row["finite_validation"] and row["bound_validation"]
        assert row["lower_bound"] <= row["resulting_state"] <= row["upper_bound"]


def test_currency_leg_exposure_is_direction_aware():
    same = duplicate_currency_exposure("EURUSD", "BUY", "GBPUSD", "BUY")
    opposite = duplicate_currency_exposure("EURUSD", "BUY", "GBPUSD", "SELL")
    assert same["duplicate_directional_exposure"] != opposite["duplicate_directional_exposure"]
    assert same["legs_a"]["USD"] == -1.0
    assert opposite["legs_b"]["USD"] == 1.0


def test_connectedness_supports_ten_symbols_and_distinct_frequency_bands():
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY", "XAUUSD"]
    frames = {symbol: synthetic_h1(rows=260, seed=100 + i) for i, symbol in enumerate(symbols)}
    biases = {symbol: "BUY" if i % 2 == 0 else "SELL" for i, symbol in enumerate(symbols)}
    result = full_connectedness_bundle(frames, biases)
    assert result["asymmetric"]["status"] == "AVAILABLE"
    assert result["frequency"]["status"] == "AVAILABLE"
    assert set(result["frequency"]["symbols"]) == set(symbols)
    assert set(FREQUENCY_BANDS) == {"short", "medium", "persistent"}
    for row in result["frequency"]["symbols"].values():
        assert {"connectedness_short", "connectedness_medium", "connectedness_persistent"} <= set(row)


def test_sample_split_registration_is_frozen_before_testing():
    rows = chronological_sample_splits(synthetic_h1(), bias="BUY", horizon=6)
    assert rows
    assert all(row["candidate_registered_before_test"] for row in rows)
    assert all(row["purge_hours"] == 6 and row["embargo_hours"] == 6 for row in rows)
    assert all(row["candidate_registry_hash"] == candidate_registry_hash() for row in rows)


def test_mcs_does_not_claim_validation_without_settled_oos_losses():
    rows = model_confidence_set(pd.DataFrame())
    assert {row["model_name"] for row in rows} == set(CANDIDATE_MODELS)
    assert all(row["mcs_status"] == "INSUFFICIENT_SETTLED_OOS_LOSSES" for row in rows)
    assert not any(row["mcs_membership"] for row in rows)


def test_managed_utility_refuses_to_invent_missing_costs():
    result = horizon_managed_utility(
        synthetic_h1(), bias="BUY", horizon=6, forecast_volatility=0.01,
        expected_shortfall=-0.02, transition_risk_pct=20, bad_spillover_pct=30,
        prediction_interval_width=0.02, model_disagreement=10,
        spread_cost=None, slippage_cost=None,
    )
    assert result["execution_cost_status"] == "MISSING_EXECUTION_COST"
    assert result["net_expected_value"] is None
    assert result["managed_utility"] is None
    assert result["gross_expected_value"] is not None


def test_shadow_rank_is_deterministic_and_keeps_production_rank_as_data():
    records = [
        {"symbol": "EURUSD", "production_rank": 2, "managed_utility_weighted": 0.2, "calibrated_probability": 60, "expected_shortfall_95": -0.01, "volatility_safety": .8, "regime_stability": 80, "transition_risk_6h": 20, "adverse_semivariance_pressure": .4, "adverse_connectedness_score": 25, "persistent_connectedness": 20, "tail_crowding_penalty": 10, "duplicate_exposure_penalty": 15, "mcs_membership_score": 0, "split_robustness_score": 70, "data_quality_score": 90, "settlement_completeness": 50},
        {"symbol": "GBPUSD", "production_rank": 1, "managed_utility_weighted": 0.1, "calibrated_probability": 55, "expected_shortfall_95": -0.02, "volatility_safety": .7, "regime_stability": 70, "transition_risk_6h": 30, "adverse_semivariance_pressure": .6, "adverse_connectedness_score": 45, "persistent_connectedness": 40, "tail_crowding_penalty": 30, "duplicate_exposure_penalty": 35, "mcs_membership_score": 0, "split_robustness_score": 60, "data_quality_score": 85, "settlement_completeness": 40},
    ]
    a = rank_shadow_candidates(records, seed_key="same")
    b = rank_shadow_candidates(records, seed_key="same")
    assert a == b
    assert {row["production_rank"] for row in a["rows"]} == {1, 2}
    assert a["production_rank_modified"] is False


def test_evidence_duplication_penalty_is_applied_for_near_identical_components():
    base = []
    for i, symbol in enumerate(("A", "B", "C", "D")):
        value = 10.0 + i
        base.append({
            "symbol": symbol, "managed_utility_weighted": value, "calibrated_probability": value,
            "expected_shortfall_95": -value, "volatility_safety": value, "regime_stability": value,
            "transition_risk_6h": 100-value, "adverse_semivariance_pressure": 100-value,
            "adverse_connectedness_score": 100-value, "persistent_connectedness": 100-value,
            "tail_crowding_penalty": 100-value, "duplicate_exposure_penalty": 100-value,
            "mcs_membership_score": value, "split_robustness_score": value,
            "data_quality_score": value, "settlement_completeness": value,
        })
    result = rank_shadow_candidates(base, seed_key="dup")
    assert result["duplicate_evidence"]
    assert any(row["duplicate_penalty"] < 1.0 for row in result["components"])


def test_content_hash_is_deterministic_and_verifiable():
    payload = {"daily_snapshot_id": "X", "symbol": "EURUSD", "value": 1.25, "content_hash": "old"}
    finalized = _finalize(payload.copy())
    expected = deterministic_hash({k: v for k, v in finalized.items() if k != "content_hash"})
    assert finalized["content_hash"] == expected


def test_migration_is_additive_idempotent_and_preserves_parent_hashes(tmp_path: Path):
    db = tmp_path / "field10.sqlite3"
    shutil.copy2(LIVE_DB, db)
    first = apply_migration(db, backup_dir=tmp_path / "backups")
    second = apply_migration(db, backup_dir=tmp_path / "backups")
    assert first["status"] == second["status"] == "PASS"
    assert first["parent_before"] == first["parent_after"]
    assert second["parent_before"] == second["parent_after"]
    assert first["parent_after"] == second["parent_after"]
    assert second["idempotent_registry_row_count"] == 1


def test_candidate_tables_are_append_only_after_migration(tmp_path: Path):
    db = tmp_path / "field10.sqlite3"
    shutil.copy2(LIVE_DB, db)
    apply_migration(db, backup_dir=tmp_path / "backups")
    con = sqlite3.connect(db)
    triggers = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
    con.close()
    assert "trg_field10_rank_components_v2_no_update" in triggers
    assert "trg_field10_rank_components_v2_no_delete" in triggers


def test_ui_is_read_only_and_does_not_publish_or_migrate():
    source = (ROOT / "ui" / "lunch_field10_multi_symbol_20260701.py").read_text(encoding="utf-8")
    assert "publish_horizon_connected_tail_candidate" not in source
    assert "migrate_field10_horizon_connected_tail_20260705" not in source
    assert "load_candidate_summary" in source
    assert "SHADOW VALIDATION — NO PRODUCTION INFLUENCE" in source


def test_heavy_candidate_runs_only_from_settings_orchestrator():
    source = (ROOT / "core" / "multi_symbol_field10_20260701.py").read_text(encoding="utf-8")
    publish_position = source.index("publish_horizon_connected_tail_candidate")
    parent_position = source.index("publish_daily_snapshot")
    assert publish_position > parent_position
    assert 'manifest["field10_horizon_connected_tail_candidate_v1"]' in source


def test_direction_contract_uses_parent_locked_bias_and_never_reverses():
    source = (ROOT / "core" / "field10_research_orchestrator_20260705.py").read_text(encoding="utf-8")
    assert 'parent.get("less_risky_bias") or parent.get("stable_daily_bias")' in source
    assert '"locked_bias_modified": False' in source
    assert '"production_rank_modified": False' in source


def test_restart_read_path_cannot_republish_daily_snapshot():
    ui_source = (ROOT / "ui" / "lunch_field10_multi_symbol_20260701.py").read_text(encoding="utf-8")
    assert "load_current_daily_snapshot" in ui_source
    assert "publish_daily_snapshot(" not in ui_source


def test_frequency_horizon_mapping_is_not_one_score_for_all_horizons():
    source = (ROOT / "core" / "field10_research_orchestrator_20260705.py").read_text(encoding="utf-8")
    assert 'if horizon <= 6' in source
    assert 'if horizon <= 24' in source
    assert 'freq.get(f"connectedness_{band}")' in source


def test_partial_evidence_is_labelled_not_fabricated():
    har = har_h1_forecasts(pd.DataFrame())
    tail = directional_var_es(pd.DataFrame(), bias="BUY")
    assert har["status"] == "INSUFFICIENT_EXACT_H1_WINDOW"
    assert har["horizons"] == {}
    assert tail["status"] == "DIRECTION_OR_SAMPLE_UNAVAILABLE"
    assert tail["horizons"] == {}


def test_model_and_feature_versions_are_explicit():
    assert MODEL_VERSION == "field10-horizon-connected-tail-20260705-v1"
    assert candidate_registry_hash()
