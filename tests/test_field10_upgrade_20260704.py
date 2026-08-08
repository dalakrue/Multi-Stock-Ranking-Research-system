from __future__ import annotations

import json
from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import pytest


def synthetic_h1(rows: int = 1200) -> pd.DataFrame:
    rng = np.random.default_rng(20260704)
    returns = rng.normal(0.00004, 0.00085, rows)
    close = 1.08 * np.exp(np.cumsum(returns))
    open_ = np.r_[close[0], close[:-1]]
    return pd.DataFrame({
        "time": pd.date_range("2026-01-01", periods=rows, freq="h", tz="UTC"),
        "open": open_, "high": np.maximum(open_, close) + 0.0002,
        "low": np.minimum(open_, close) - 0.0002, "close": close,
        "tick_volume": np.arange(rows, dtype=float) + 100.0,
    })


def test_transition_risk_uses_matrix_power_or_survival_not_linear_scaling():
    from core.field10_quant_metrics_20260704 import transition_risk_6h
    labels = pd.Series((["BULL", "BULL", "RANGE", "RANGE", "RANGE"] * 80) + ["BULL"] * 20)
    result = transition_risk_6h(labels)
    assert result["method"] in {"MARKOV_P6_SELF_TRANSITION", "SEMI_MARKOV_EMPIRICAL_SURVIVAL"}
    assert 0 <= result["value"] <= 100
    if result["method"] == "MARKOV_P6_SELF_TRANSITION":
        matrix = np.asarray(result["transition_matrix"], dtype=float)
        idx = result["states"].index(result["current_state"])
        expected = 100 * (1 - np.linalg.matrix_power(matrix, 6)[idx, idx])
        assert result["value"] == pytest.approx(expected, abs=1e-5)


def test_ev6_is_cost_adjusted_and_raw_separate_from_risk_adjusted():
    from core.field10_quant_metrics_20260704 import compute_quant_metrics
    frame = synthetic_h1()
    no_cost = compute_quant_metrics(frame, bias="BUY", cost_percent=0.0)
    with_cost = compute_quant_metrics(frame, bias="BUY", cost_percent=0.10)
    assert no_cost["expected_value_6h"] is not None
    assert with_cost["expected_value_6h"] == pytest.approx(no_cost["expected_value_6h"] - 0.10, abs=1e-6)
    assert "risk_adjusted_expected_value_6h" in with_cost
    assert with_cost["risk_adjusted_expected_value_6h"] <= with_cost["expected_value_6h"]


def test_probability_reach_ev_uses_positive_target_not_exact_equality():
    from core.field10_quant_metrics_20260704 import compute_quant_metrics
    result = compute_quant_metrics(synthetic_h1(), bias="BUY")
    for horizon in (1, 6, 12):
        target = result[f"ev_target_{horizon}h"]
        reach = result[f"probability_reach_ev_{horizon}h"]
        profit = result[f"probability_profit_{horizon}h"]
        assert target is not None and target > 0
        assert 0 <= reach <= 100
        assert reach <= profit + 1e-9


def test_volume_12h_is_sum_of_last_12_completed_h1_candles():
    from core.field10_quant_metrics_20260704 import compute_quant_metrics
    frame = synthetic_h1()
    result = compute_quant_metrics(frame, bias="BUY")
    assert result["tick_volume_12h"] == pytest.approx(frame["tick_volume"].tail(12).sum())
    assert result["volume_source"] == "BROKER_TICK_VOLUME"


def test_unexpected_integrity_failure_blocks_but_keeps_diagnostics():
    from core.field10_quant_metrics_20260704 import normalize_h1, unexpected_situation
    result = unexpected_situation(normalize_h1(synthetic_h1()), transition_risk=10, volume_z=0, integrity_failed=True)
    assert result["unexpected_situation_status"] == "BLOCK"
    assert result["validation_permission"] == "BLOCKED"
    assert result["unexpected_situation_severity"] == 100


def test_top15_excludes_three_pairs_and_enforces_median_spread():
    from core.top15_fx_qualification_20260704 import CANDIDATES, EXCLUDED, qualify_from_observations
    rows = []
    now = pd.Timestamp("2026-07-04T07:00:00Z")
    for index, symbol in enumerate(list(CANDIDATES)[:20] + list(EXCLUDED)):
        for sample in range(5):
            rows.append({"provider_symbol": symbol + ".m", "canonical_symbol": symbol,
                         "spread_points": 8 + index % 9 + sample * 0.1, "observed_at": now - pd.Timedelta(minutes=sample),
                         "tradeable": True, "history_bars": 600, "tick_volume_evidence": 600})
    rows.append({"provider_symbol": "AUDUSD.m", "canonical_symbol": "AUDUSD", "spread_points": 80,
                 "observed_at": now, "tradeable": True, "history_bars": 600, "tick_volume_evidence": 600})
    result = qualify_from_observations(pd.DataFrame(rows), now=now, minimum_observations=3)
    selected = result.loc[result["qualified"]].sort_values("rank").head(15)
    assert len(selected) == 15
    assert not set(selected["canonical_symbol"]).intersection(EXCLUDED)
    assert selected["median_spread"].le(20).all()


def test_twelve_token_bucket_limits_to_two_normal_credits_per_minute():
    from core.multi_symbol_api_runtime_20260702 import twelve_token_bucket_acquire
    state = {}
    assert twelve_token_bucket_acquire(state)["allowed"] is True
    assert twelve_token_bucket_acquire(state)["allowed"] is True
    third = twelve_token_bucket_acquire(state)
    assert third["allowed"] is False
    assert third["cooldown_seconds"] > 0


def test_persistent_exact_candle_cache_round_trip(tmp_path: Path):
    from core.multi_symbol_api_runtime_20260702 import _persistent_get, _persistent_put
    db = tmp_path / "api.sqlite3"
    frame = synthetic_h1(120)
    _persistent_put("request", frame, provider="mt5", canonical_symbol="AUDUSD", provider_alias="AUDUSD.m",
                    timeframe="H1", completed="2026-07-04T06:00:00+00:00", candle_count=120,
                    profile_fingerprint="safe-hash", source="MT5", path=db)
    restored, source = _persistent_get("request", path=db)
    assert restored is not None and len(restored) == len(frame)
    assert source == "MT5"


def test_shared_finnhub_news_is_fetched_once_then_deduplicated_locally(tmp_path: Path):
    from core.multi_symbol_api_runtime_20260702 import cache_shared_news_items, load_shared_news
    db = tmp_path / "api.sqlite3"
    items = [
        {"headline": "Fed holds rates", "url": "https://example.test/a?tracking=1", "source": "X"},
        {"headline": "Fed holds rates", "url": "https://example.test/a?tracking=2", "source": "X"},
        {"headline": "ECB updates guidance", "url": "https://example.test/b", "source": "Y"},
    ]
    report = cache_shared_news_items(items, path=db)
    assert report["stored_count"] == 2
    assert report["deduplicated_count"] == 1
    assert len(load_shared_news(path=db)) == 2


def test_guest_routes_to_settings_and_missing_connectors_activate_plan_b():
    from core.startup_lunch_orchestrator_20260704 import run_startup
    state = {"new7_auth_logged_in": True, "new7_auth_guest": True, "active_page": "Settings"}
    report = run_startup(state)
    assert state["active_page"] == "Settings"
    assert state["tab_choice"] == "Settings"
    assert report["status"] == "PLAN_B_REQUIRED"
    assert report["blocking_connectors"]


def test_auto_run_identity_is_idempotent_and_universe_sensitive():
    from core.startup_lunch_orchestrator_20260704 import build_auto_run_identity
    kwargs = dict(user_mode="guest", completed_h1="2026-07-04T06:00:00Z", symbols=["AUDUSD", "NZDUSD"],
                  timeframe="H1", connector_profile_signature="profile")
    first = build_auto_run_identity(**kwargs)
    assert first == build_auto_run_identity(**kwargs)
    assert first != build_auto_run_identity(**{**kwargs, "symbols": ["AUDUSD", "USDCAD"]})


def test_field12_selector_source_has_no_heavy_runner_call():
    source = (Path(__file__).resolve().parents[1] / "ui" / "lunch_multi_symbol_selector_20260704.py").read_text()
    assert "run_settings_calculation" not in source
    assert "run_selected_symbols" not in source
    assert "activate_symbol_result" in source


def _prepare_field10_db(path: Path) -> None:
    from core.multi_symbol_field10_20260701 import migrate_database
    from core.field10_daily_snapshot_contract_20260702 import migrate_daily_snapshot_database
    from core.field10_integrated_evidence_20260702 import migrate_integrated_evidence_database
    from core.child_generation_contract_20260702 import migrate_child_publication_contract
    migrate_database(path); migrate_daily_snapshot_database(path)
    migrate_integrated_evidence_database(path); migrate_child_publication_contract(path)


def test_database_migration_is_idempotent_and_creates_no_second_rank_table(tmp_path: Path):
    from core.field10_unified_migration_20260703 import migrate_and_verify_field10, MIGRATION_VERSION
    db = tmp_path / "field10.sqlite3"
    _prepare_field10_db(db)
    first = migrate_and_verify_field10(db)
    second = migrate_and_verify_field10(db)
    assert first["ok"] and second["ok"]
    assert second["migration_version"] == MIGRATION_VERSION
    with sqlite3.connect(db) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "field10_rank" not in tables and "field10_rank_20260704" not in tables
        for table in ("field10_hourly_quality", "field10_daily_higher_lock", "field10_daily_snapshot_symbol", "field10_integrated_evidence_history"):
            columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            assert {"expected_value_6h", "probability_reach_ev_6h", "tick_volume_12h", "metric_provenance_json"}.issubset(columns)


def test_daily_row_json_backfills_new_physical_columns_causally(tmp_path: Path):
    from core.field10_unified_migration_20260703 import migrate_and_verify_field10
    db = tmp_path / "field10.sqlite3"
    _prepare_field10_db(db)
    payload = {"Expected Value 6H (%)": 0.12, "Probability Reach EV 6H (%)": 63.0,
               "Observed Tick Volume 12H": 12345, "Volume Data Source": "BROKER_TICK_VOLUME",
               "Transition Risk 6H": 22.0, "Unexpected Situation Status": "NORMAL",
               "Validation Permission": "PERMITTED", "Evidence Sample Size": 88,
               "Explanation": json.dumps({"causal": True})}
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO field10_daily_snapshot("
            "daily_snapshot_id,broker_day,cutoff_broker_time,latest_completed_h1,"
            "ordered_symbol_universe_json,universe_hash,main_symbol,secondary_symbols_json,"
            "provider_aliases_json,symbol_count,parent_run_id,child_run_ids_json,"
            "canonical_run_ids_json,source_ids_json,snapshot_hashes_json,model_version,"
            "formula_version,threshold_version,content_hash,publication_status,"
            "published_at_broker_time,locked_until_broker_time,metadata_json,created_at_broker_time"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "S1", "2026-07-04", "2026-07-04T03:00:00+00:00",
                "2026-07-04T02:00:00+00:00", json.dumps(["AUDUSD"]), "universe-hash",
                "AUDUSD", "[]", "{}", 1, "PARENT-1", "[]", "[]", "[]", "[]",
                "model", "formula", "threshold", "parent-content-hash", "PUBLISHED",
                "2026-07-04T03:01:00+00:00", "2026-07-04T23:00:00+00:00", "{}",
                "2026-07-04T03:01:00+00:00",
            ),
        )
        conn.execute("INSERT INTO field10_daily_snapshot_symbol(daily_snapshot_id,broker_day,symbol,role,daily_rank,daily_grade,eligibility_status,trade_permission,sample_count,sample_complete_status,content_hash,row_json,score_explanation_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     ("S1", "2026-07-04", "AUDUSD", "MAIN", 1, "A", "ELIGIBLE", "ALLOWED", 600, "COMPLETE", "h", json.dumps(payload), "{}"))
        conn.commit()
    assert migrate_and_verify_field10(db)["ok"]
    with sqlite3.connect(db) as conn:
        row = conn.execute("SELECT expected_value_6h,probability_reach_ev_6h,tick_volume_12h,volume_source,transition_risk_6h FROM field10_daily_snapshot_symbol WHERE symbol='AUDUSD'").fetchone()
    assert row[0] == pytest.approx(0.12, abs=1e-9)
    assert row[1] == pytest.approx(63.0, abs=1e-9)
    assert row[2] == pytest.approx(12345.0, abs=1e-9)
    assert row[3] == "BROKER_TICK_VOLUME"
    assert row[4] == pytest.approx(22.0, abs=1e-9)


def test_api_audit_schema_never_contains_secret_columns(tmp_path: Path):
    from core.multi_symbol_api_runtime_20260702 import migrate_api_runtime
    db = tmp_path / "api.sqlite3"
    migrate_api_runtime(db)
    with sqlite3.connect(db) as conn:
        columns = {row[1].lower() for row in conn.execute("PRAGMA table_info(api_request_audit_20260704)")}
    assert not any(token in column for column in columns for token in ("api_key", "password", "secret", "credential", "token"))


def test_startup_restores_read_only_and_never_starts_heavy_calculation(monkeypatch):
    import time
    from core import startup_lunch_orchestrator_20260704 as startup
    from core import top15_fx_qualification_20260704 as qualification
    from core import super_quick_service_20260704 as service

    symbols = [
        "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "EURGBP", "EURCHF", "EURCAD",
        "EURAUD", "EURNZD", "GBPCHF", "GBPCAD", "GBPAUD", "GBPNZD", "AUDCAD", "AUDNZD",
    ]
    calls: list[list[str]] = []
    monkeypatch.setattr(qualification, "qualify_mt5_top15", lambda: {
        "ok": True, "status": "QUALIFIED", "qualified_count": 15, "selected": symbols,
    })
    monkeypatch.setattr(service, "run_super_quick", lambda state, selected: (
        calls.append(list(selected)) or {"ok": True, "status": "COMPLETED", "parent_run_id": "P1"}
    ))
    healthy = {
        "mt5": {"configured": True, "healthy": True},
        "twelve_data": {"configured": True, "healthy": True},
        "finnhub": {"configured": True, "healthy": True},
        "checked_at": time.time(), "ttl_seconds": 900, "all_healthy": True,
    }
    state = {
        "new7_auth_logged_in": True,
        "new7_auth_guest": True,
        "connector_health_snapshot_20260704": healthy,
        "market_connector_saved_profile_20260702": {"signature": "SAFE-SIGNATURE", "timeframe": "H1"},
        "canonical_decision_result_20260617": {"completed_broker_candle": "2026-07-04T06:00:00Z"},
    }
    first = startup.run_startup(state)
    second = startup.run_startup(state)
    assert first["status"] == "AUTO_RUN_PUBLISHED"
    assert second["status"] == "AUTO_RUN_PUBLISHED"
    assert second["idempotent_reuse"] is True
    assert calls == []
    assert first.get("heavy_run_started") is False
    assert second.get("heavy_run_started") is False


def test_canonical_and_storage_migration_entry_points_share_unified_version(tmp_path: Path):
    from core.canonical.migrations import migrate_field10_rank_evidence_20260704
    from core.storage.database import migrate_field10_database_20260704, field10_database_health_20260704
    from core.field10_unified_migration_20260703 import MIGRATION_VERSION

    db = tmp_path / "field10.sqlite3"
    _prepare_field10_db(db)
    canonical = migrate_field10_rank_evidence_20260704(db)
    storage = migrate_field10_database_20260704(db)
    health = field10_database_health_20260704(db)
    assert canonical["ok"] and storage["ok"] and health["ok"]
    assert canonical["migration_version"] == storage["migration_version"] == health["migration_version"] == MIGRATION_VERSION
