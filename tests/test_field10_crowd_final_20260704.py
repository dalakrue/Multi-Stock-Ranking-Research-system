from __future__ import annotations

import json
from pathlib import Path
import shutil
import sqlite3
from typing import Any

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
CUTOFF = pd.Timestamp("2026-07-04T05:00:00Z")
SNAPSHOT_ID = "F10-CROWD-FINAL-TEST"
SYMBOLS = ("EURUSD", "USDJPY")


def _synthetic_frame(symbol: str, drift_sign: int, *, rows: int = 601) -> pd.DataFrame:
    """600 completed rows ending at CUTOFF plus one forming row."""
    rng = np.random.default_rng(110 if symbol == "EURUSD" else 220)
    times = pd.date_range(end=CUTOFF + pd.Timedelta(hours=1), periods=rows, freq="h", tz="UTC")
    returns = rng.normal(drift_sign * 0.00005, 0.00070, rows)
    start = 1.08 if symbol == "EURUSD" else 150.0
    close = start * np.exp(np.cumsum(returns))
    open_ = np.r_[close[0], close[:-1]]
    return pd.DataFrame(
        {
            "time": times,
            "open": open_,
            "high": np.maximum(open_, close) * (1.0 + 0.00020),
            "low": np.minimum(open_, close) * (1.0 - 0.00020),
            "close": close,
            "tick_volume": rng.integers(100, 600, rows).astype(float),
            "spread_pct": np.full(rows, 0.008),
            "slippage_pct": np.full(rows, 0.002),
        }
    )


def _insert_snapshot(path: Path) -> None:
    from core.field10_unified_migration_20260703 import migrate_and_verify_field10

    report = migrate_and_verify_field10(path)
    assert report["ok"], report
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(
            """INSERT INTO field10_daily_snapshot(
                daily_snapshot_id,broker_day,cutoff_broker_time,latest_completed_h1,
                ordered_symbol_universe_json,universe_hash,main_symbol,secondary_symbols_json,
                provider_aliases_json,symbol_count,parent_run_id,child_run_ids_json,
                canonical_run_ids_json,source_ids_json,snapshot_hashes_json,model_version,
                formula_version,threshold_version,content_hash,publication_status,
                published_at_broker_time,locked_until_broker_time,metadata_json,created_at_broker_time
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                SNAPSHOT_ID,
                "2026-07-04",
                "2026-07-04T06:00:00+00:00",
                CUTOFF.isoformat(),
                json.dumps(list(SYMBOLS)),
                "universe-hash-test",
                "EURUSD",
                json.dumps(["USDJPY"]),
                json.dumps({"EURUSD": "EURUSD", "USDJPY": "USDJPY"}),
                2,
                "PARENT-RUN-TEST",
                json.dumps({"EURUSD": "CHILD-EURUSD", "USDJPY": "CHILD-USDJPY"}),
                json.dumps({"EURUSD": "RUN-EURUSD", "USDJPY": "RUN-USDJPY"}),
                json.dumps({"EURUSD": "SOURCE-EURUSD", "USDJPY": "SOURCE-USDJPY"}),
                json.dumps({"EURUSD": "SNAP-HASH-EURUSD", "USDJPY": "SNAP-HASH-USDJPY"}),
                "existing-field10-model",
                "existing-field10-formula",
                "existing-field10-threshold",
                "snapshot-content-hash",
                "PUBLISHED_LOCKED",
                "2026-07-04T06:00:00+00:00",
                "2026-07-04T23:00:00+00:00",
                "{}",
                "2026-07-04T06:00:00+00:00",
            ),
        )
        rows = (
            (1, "EURUSD", "BUY", 82.0, 21.0, 33.0, "BULL_NORMAL"),
            (2, "USDJPY", "SELL", 76.0, 24.0, 38.0, "BEAR_NORMAL"),
        )
        for rank, symbol, bias, score, risk6, risk24, regime in rows:
            conn.execute(
                """INSERT INTO field10_daily_snapshot_symbol(
                    daily_snapshot_id,broker_day,symbol,role,daily_rank,daily_grade,
                    eligibility_status,trade_permission,sample_count,sample_complete_status,
                    content_hash,row_json,score_explanation_json,stable_daily_bias,
                    less_risky_bias,institutional_score,existing_rank_score,
                    transition_risk_6h,transition_risk_24h,completed_candle,
                    canonical_run_id,source_id,snapshot_hash,higher_standard_regime
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    SNAPSHOT_ID,
                    "2026-07-04",
                    symbol,
                    "MAIN" if rank == 1 else "SECONDARY",
                    rank,
                    "A",
                    "ELIGIBLE",
                    "ALLOW",
                    600,
                    "COMPLETE",
                    f"technical-hash-{symbol}",
                    json.dumps({"Symbol": symbol, "Rank": rank, "Less-Risky Bias": bias}),
                    "{}",
                    bias,
                    bias,
                    score,
                    score,
                    risk6,
                    risk24,
                    CUTOFF.isoformat(),
                    f"RUN-{symbol}",
                    f"SOURCE-{symbol}",
                    f"SNAP-HASH-{symbol}",
                    regime,
                ),
            )
            conn.execute(
                """INSERT INTO field10_daily_news_event_rank(
                    daily_snapshot_id,broker_day,symbol,event_id,news_rank,sentiment_bias,
                    sentiment_probability,headline,source,source_quality,release_utc,
                    current_broker_time,event_age_minutes,pair_relevance,impact_remaining_pct,
                    absorption_pct,event_risk_permission,evidence_sample_size,model_version,
                    formula_version,threshold_version,data_provider,provider_authentication,
                    timestamp_provenance,content_hash,row_json,publication_status,stored_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    SNAPSHOT_ID,
                    "2026-07-04",
                    symbol,
                    f"EVENT-{symbol}",
                    rank,
                    bias,
                    70.0,
                    f"Authenticated test event for {symbol}",
                    "TestWire",
                    85.0,
                    "2026-07-04T04:00:00+00:00",
                    "2026-07-04T06:00:00+00:00",
                    120.0,
                    90.0,
                    20.0,
                    80.0,
                    "ALLOW",
                    20,
                    "finnhub-event-model",
                    "finnhub-event-formula",
                    "finnhub-event-threshold",
                    "FINNHUB",
                    "FINNHUB_AUTHENTICATED_API",
                    "PERSISTED_BROKER_SNAPSHOT",
                    f"news-hash-{symbol}",
                    "{}",
                    "PUBLISHED_LOCKED_CHILD",
                    "2026-07-04T06:00:00+00:00",
                ),
            )
        conn.commit()


@pytest.fixture(scope="module")
def published_db(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    from core import field10_crowd_final_20260704 as module

    path = tmp_path_factory.mktemp("field10_crowd_final") / "field10.sqlite3"
    _insert_snapshot(path)
    states = {
        "EURUSD": {"canonical_completed_ohlc_df_20260617": _synthetic_frame("EURUSD", 1)},
        "USDJPY": {"canonical_completed_ohlc_df_20260617": _synthetic_frame("USDJPY", -1)},
    }
    original = module._load_states
    module._load_states = lambda symbols: {symbol: states[symbol] for symbol in symbols}
    try:
        state: dict[str, Any] = {}
        report = module.publish_crowd_and_final_tables(
            state,
            daily_snapshot_id=SNAPSHOT_ID,
            selected_symbols=list(SYMBOLS),
            path=path,
        )
    finally:
        module._load_states = original
    assert report["ok"], report
    return {"path": path, "report": report, "states": states}


# 1
def test_exactly_600_completed_h1_candles_are_used(published_db: dict[str, Any]) -> None:
    from core.field10_crowd_final_20260704 import extract_exact_completed_h1

    frame, report = extract_exact_completed_h1(published_db["states"]["EURUSD"], CUTOFF)
    assert len(frame) == 600
    assert report["sample_count"] == 600
    assert report["status"] == "PASS"


# 2
def test_forming_h1_candle_is_excluded(published_db: dict[str, Any]) -> None:
    from core.field10_crowd_final_20260704 import extract_exact_completed_h1

    raw = published_db["states"]["EURUSD"]["canonical_completed_ohlc_df_20260617"]
    assert pd.to_datetime(raw["time"], utc=True).max() > CUTOFF
    frame, report = extract_exact_completed_h1(published_db["states"]["EURUSD"], CUTOFF)
    assert frame["time"].max() == CUTOFF
    assert report["forming_candle_excluded"] is True


# 3
def test_all_symbols_share_parent_run_and_completed_candle(published_db: dict[str, Any]) -> None:
    with sqlite3.connect(published_db["path"]) as conn:
        rows = conn.execute(
            "SELECT DISTINCT parent_run_id,completed_h1_candle FROM field10_daily_crowd_psychology_rank"
        ).fetchall()
    assert rows == [("PARENT-RUN-TEST", CUTOFF.isoformat())]


# 4
def test_symbol_local_values_are_not_copied_between_symbols(published_db: dict[str, Any]) -> None:
    with sqlite3.connect(published_db["path"]) as conn:
        rows = conn.execute(
            "SELECT symbol,crowd_psychology_score,crowd_momentum_6h,content_hash "
            "FROM field10_daily_crowd_psychology_rank ORDER BY symbol"
        ).fetchall()
    assert len(rows) == 2
    assert rows[0][1:] != rows[1][1:]


# 5
def test_crowd_table_is_persisted_and_renderer_is_read_only(published_db: dict[str, Any]) -> None:
    from core.field10_crowd_final_20260704 import load_crowd_psychology_rank

    frame = load_crowd_psychology_rank(daily_snapshot_id=SNAPSHOT_ID, path=published_db["path"])
    assert len(frame) == 2
    source = (ROOT / "ui" / "lunch_field10_multi_symbol_20260701.py").read_text()
    segment = source[source.index("def _render_crowd_psychology_rank"):source.index("def _render_final_multi_symbol_rank")]
    assert "publish_crowd_and_final_tables" not in segment
    assert "migrate_crowd_final_database" not in segment
    assert "fetch_" not in segment


# 6
def test_final_table_reads_all_four_persisted_source_families(published_db: dict[str, Any]) -> None:
    with sqlite3.connect(published_db["path"]) as conn:
        lineage = conn.execute(
            "SELECT evidence_lineage_json FROM field10_daily_final_multi_symbol_rank WHERE symbol='EURUSD'"
        ).fetchone()[0]
    payload = json.loads(lineage)
    assert set(payload["source_rows"]) == {"technical_fundamental", "sessions", "news", "crowd"}
    assert set(payload["source_hashes"]) == {"technical_fundamental", "sessions", "news", "crowd"}


# 7
@pytest.mark.parametrize(
    "symbol,currency,positive,expected",
    [
        ("EURUSD", "EUR", True, "BUY"), ("EURUSD", "USD", True, "SELL"),
        ("USDJPY", "USD", True, "BUY"), ("USDJPY", "JPY", True, "SELL"),
        ("GBPCHF", "GBP", False, "SELL"), ("GBPCHF", "CHF", False, "BUY"),
        ("AUDNZD", "AUD", True, "BUY"), ("AUDNZD", "NZD", True, "SELL"),
        ("USDCAD", "CAD", False, "BUY"),
    ],
)
def test_currency_base_quote_mapping_is_pair_specific(symbol: str, currency: str, positive: bool, expected: str) -> None:
    from core.field10_crowd_final_20260704 import pair_direction_from_currency_evidence

    assert pair_direction_from_currency_evidence(symbol, currency, positive) == expected


# 8
def test_extreme_crowd_pressure_does_not_automatically_force_continuation() -> None:
    from core.field10_crowd_final_20260704 import _crowd_state

    state = _crowd_state(92.0, {"panic": 20.0, "fomo": 50.0, "exhaustion": 88.0, "contrarian": 82.0, "divergence_severity": 80.0, "calculation_status": "CALCULATED_SHADOW"})
    assert state in {"CROWD_EXHAUSTION", "CONTRARIAN_REVERSAL_RISK"}


# 9
def test_contrarian_reversal_logic_is_bounded_and_deterministic() -> None:
    from core.field10_crowd_final_20260704 import _crowd_state

    record = {"panic": 10.0, "fomo": 40.0, "exhaustion": 72.0, "contrarian": 70.0, "divergence_severity": 68.0, "calculation_status": "CALCULATED_SHADOW"}
    outputs = {_crowd_state(80.0, record) for _ in range(10)}
    assert len(outputs) == 1
    assert next(iter(outputs)) in {"CROWD_EXHAUSTION", "CONTRARIAN_REVERSAL_RISK"}


# 10
def test_crowd_transition_risks_are_bounded(published_db: dict[str, Any]) -> None:
    with sqlite3.connect(published_db["path"]) as conn:
        rows = conn.execute(
            "SELECT crowd_transition_risk_1h,crowd_transition_risk_6h,crowd_transition_risk_12h,crowd_transition_risk_24h "
            "FROM field10_daily_crowd_psychology_rank"
        ).fetchall()
    assert rows
    assert all(0.0 <= float(value) <= 100.0 for row in rows for value in row)


# 11
def test_final_transition_risks_are_bounded(published_db: dict[str, Any]) -> None:
    with sqlite3.connect(published_db["path"]) as conn:
        rows = conn.execute(
            "SELECT final_transition_bias_risk_1h,final_transition_bias_risk_6h,final_transition_bias_risk_12h,final_transition_bias_risk_24h "
            "FROM field10_daily_final_multi_symbol_rank"
        ).fetchall()
    assert rows
    assert all(0.0 <= float(value) <= 100.0 for row in rows for value in row)


# 12
def test_probability_remains_and_reverses_are_logically_consistent(published_db: dict[str, Any]) -> None:
    with sqlite3.connect(published_db["path"]) as conn:
        rows = conn.execute(
            "SELECT final_transition_bias_risk_1h,probability_bias_remains_1h,probability_bias_reverses_1h,"
            "final_transition_bias_risk_6h,probability_bias_remains_6h,probability_bias_reverses_6h "
            "FROM field10_daily_final_multi_symbol_rank"
        ).fetchall()
    for risk1, remain1, reverse1, risk6, remain6, reverse6 in rows:
        assert remain1 == pytest.approx(100.0 - risk1)
        assert remain6 == pytest.approx(100.0 - risk6)
        assert 0 <= reverse1 <= risk1
        assert 0 <= reverse6 <= risk6
        assert remain1 + reverse1 <= 100.0 + 1e-9
        assert remain6 + reverse6 <= 100.0 + 1e-9


# 13
def test_expected_value_is_persisted_separately_for_four_horizons(published_db: dict[str, Any]) -> None:
    with sqlite3.connect(published_db["path"]) as conn:
        row = conn.execute(
            "SELECT expected_value_1h,expected_value_6h,expected_value_12h,expected_value_24h,horizon_ev_component_json "
            "FROM field10_daily_final_multi_symbol_rank WHERE symbol='EURUSD'"
        ).fetchone()
    components = json.loads(row[4])
    assert set(map(str, components)) == {"1", "6", "12", "24"}
    assert all(row[index] is not None for index in range(4))


# 14
def test_expected_value_includes_cost_tail_and_transition_penalties(published_db: dict[str, Any]) -> None:
    with sqlite3.connect(published_db["path"]) as conn:
        raw = conn.execute(
            "SELECT horizon_ev_component_json FROM field10_daily_final_multi_symbol_rank WHERE symbol='EURUSD'"
        ).fetchone()[0]
    components = json.loads(raw)
    for horizon in ("1", "6", "12", "24"):
        item = components[horizon]
        assert item["expected_spread_cost"] is not None
        assert item["expected_slippage_cost"] is not None
        assert item["tail_risk_penalty"] is not None
        assert item["transition_risk_penalty"] is not None
        assert item["residual_news_shock_penalty"] is not None


# 15
def test_missing_optional_evidence_is_not_converted_to_zero(published_db: dict[str, Any]) -> None:
    with sqlite3.connect(published_db["path"]) as conn:
        row = conn.execute(
            "SELECT retail_long_percentage,social_sentiment_contribution,retail_positioning_bias,social_evidence_source,component_json "
            "FROM field10_daily_crowd_psychology_rank WHERE symbol='EURUSD'"
        ).fetchone()
    assert row[0] is None and row[1] is None
    assert row[2] == "UNAVAILABLE" and row[3] == "UNAVAILABLE"
    components = json.loads(row[4])["components"]
    assert components["positioning_pressure"]["status"].startswith("UNAVAILABLE")
    assert components["social_sentiment_contribution"]["status"].startswith("UNAVAILABLE")


# 16
def test_locked_final_ranking_is_immutable_before_review(published_db: dict[str, Any]) -> None:
    from core import field10_crowd_final_20260704 as module

    path = published_db["path"]
    with sqlite3.connect(path) as conn:
        before = conn.execute(
            "SELECT symbol,final_rank,content_hash,final_publication_hash FROM field10_daily_final_multi_symbol_rank ORDER BY symbol"
        ).fetchall()
    original = module._load_states
    module._load_states = lambda symbols: {symbol: published_db["states"][symbol] for symbol in symbols}
    try:
        report = module.publish_crowd_and_final_tables({}, daily_snapshot_id=SNAPSHOT_ID, selected_symbols=list(SYMBOLS), path=path)
    finally:
        module._load_states = original
    assert report["ok"]
    with sqlite3.connect(path) as conn:
        after = conn.execute(
            "SELECT symbol,final_rank,content_hash,final_publication_hash FROM field10_daily_final_multi_symbol_rank ORDER BY symbol"
        ).fetchall()
    assert before == after
    assert report["final_rows_inserted"] == 0


# 17
def test_live_safety_downgrades_permission_without_reranking_or_bias_change(published_db: dict[str, Any]) -> None:
    from core.field10_crowd_final_20260704 import apply_live_safety_overlay, load_final_multi_symbol_rank

    frame = load_final_multi_symbol_rank(daily_snapshot_id=SNAPSHOT_ID, path=published_db["path"], apply_live_safety=False)
    before = frame.loc[frame["Symbol"] == "EURUSD"].iloc[0]
    overlaid = apply_live_safety_overlay(frame, {"EURUSD": "BLOCK"})
    after = overlaid.loc[overlaid["Symbol"] == "EURUSD"].iloc[0]
    assert after["Final Rank"] == before["Final Rank"]
    assert after["Final Less-Risky Bias to Hold"] == before["Final Less-Risky Bias to Hold"]
    assert after["Final Entry Permission"] == "BLOCK"


# 18
def test_outcome_settlement_is_append_only_and_predictions_are_not_overwritten(published_db: dict[str, Any]) -> None:
    from core.field10_crowd_final_20260704 import record_immutable_outcome

    path = published_db["path"]
    with sqlite3.connect(path) as conn:
        content_hash = conn.execute(
            "SELECT content_hash FROM field10_daily_final_multi_symbol_rank WHERE symbol='EURUSD'"
        ).fetchone()[0]
    first = record_immutable_outcome(
        table="final", daily_snapshot_id=SNAPSHOT_ID, symbol="EURUSD",
        prediction_content_hash=content_hash, horizon_hours=6, realized_return_pct=0.12,
        realized_direction="BUY", direction_correct=True, realized_mfe_pct=0.20,
        realized_mae_pct=-0.05, realized_net_return_pct=0.10,
        settled_broker_time="2026-07-04T11:00:00+00:00", evaluation={"oos": True}, path=path,
    )
    second = record_immutable_outcome(
        table="final", daily_snapshot_id=SNAPSHOT_ID, symbol="EURUSD",
        prediction_content_hash=content_hash, horizon_hours=6, realized_return_pct=0.12,
        realized_direction="BUY", direction_correct=True, realized_mfe_pct=0.20,
        realized_mae_pct=-0.05, realized_net_return_pct=0.10,
        settled_broker_time="2026-07-04T11:00:00+00:00", evaluation={"oos": True}, path=path,
    )
    assert first["outcome_hash"] == second["outcome_hash"]
    with sqlite3.connect(path) as conn:
        prediction_after = conn.execute(
            "SELECT content_hash FROM field10_daily_final_multi_symbol_rank WHERE symbol='EURUSD'"
        ).fetchone()[0]
        outcome_count = conn.execute("SELECT COUNT(*) FROM field10_final_multi_symbol_outcome").fetchone()[0]
    assert prediction_after == content_hash
    assert outcome_count == 1


# 19
def test_four_source_evidence_hashes_are_persisted(published_db: dict[str, Any]) -> None:
    with sqlite3.connect(published_db["path"]) as conn:
        rows = conn.execute("SELECT four_source_hashes_json FROM field10_daily_final_multi_symbol_rank").fetchall()
    for (raw,) in rows:
        hashes = json.loads(raw)
        assert hashes["technical_fundamental"]
        assert hashes["sessions"]
        assert hashes["news"]
        assert hashes["crowd"]


# 20
def test_database_migration_is_idempotent(published_db: dict[str, Any], tmp_path: Path) -> None:
    from core.field10_unified_migration_20260703 import migrate_and_verify_field10

    copy = tmp_path / "copy.sqlite3"
    shutil.copy2(published_db["path"], copy)
    first = migrate_and_verify_field10(copy)
    second = migrate_and_verify_field10(copy)
    assert first["ok"] and second["ok"]
    assert second["missing_required_indexes"] == {}
    assert second["primary_key_issues"] == {}


# 21
def test_no_duplicate_production_rank_table_exists(published_db: dict[str, Any]) -> None:
    with sqlite3.connect(published_db["path"]) as conn:
        tables = {row[0].lower() for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"field10_rank", "field10_rank_20260704", "field10_production_rank"}.isdisjoint(tables)
    assert "field10_daily_snapshot_symbol" in tables
    assert "field10_daily_final_multi_symbol_rank" in tables


# 22
def test_required_indexes_exist(published_db: dict[str, Any]) -> None:
    expected = {
        "field10_daily_crowd_psychology_rank": {"idx_f10_crowd_broker_day", "idx_f10_crowd_snapshot", "idx_f10_crowd_symbol", "idx_f10_crowd_publication", "idx_f10_crowd_completed"},
        "field10_daily_final_multi_symbol_rank": {"idx_f10_final_broker_day", "idx_f10_final_snapshot", "idx_f10_final_symbol", "idx_f10_final_publication", "idx_f10_final_lock", "idx_f10_final_completed"},
    }
    with sqlite3.connect(published_db["path"]) as conn:
        for table, wanted in expected.items():
            actual = {row[1] for row in conn.execute(f"PRAGMA index_list({table})")}
            assert wanted.issubset(actual)


# 23
def test_no_api_key_or_secret_columns_are_written(published_db: dict[str, Any]) -> None:
    with sqlite3.connect(published_db["path"]) as conn:
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            columns = [row[1].lower() for row in conn.execute(f'PRAGMA table_info("{table}")')]
            assert not any(token in column for column in columns for token in ("api_key", "password", "secret", "credential", "access_token"))


# 24
def test_top_four_full_row_styling_is_implemented() -> None:
    source = (ROOT / "ui" / "lunch_field10_multi_symbol_20260701.py").read_text()
    segment = source[source.index("def _final_row_styler"):source.index("def _render_session_entry_map")]
    for rank in (1, 2, 3, 4):
        assert f"int(rank) == {rank}" in segment
    assert "background-color" in segment
    assert "BLOCK" in segment and "CAUTION" in segment and "EXIT_OR_REDUCE" in segment


# 25
def test_mobile_first_column_order_is_exact() -> None:
    from core.field10_crowd_final_20260704 import MOBILE_FINAL_COLUMNS

    assert MOBILE_FINAL_COLUMNS == (
        "Final Rank", "Symbol", "Final Less-Risky Bias to Hold",
        "Final Hold Permission", "Final Entry Permission", "Final Less-Risky Bias Confidence",
        "Final Transition Bias Risk 1H", "Final Transition Bias Risk 6H",
        "Expected Value 1H", "Expected Value 6H",
    )


# 26
def test_light_and_dark_mode_styles_retain_contrast_and_text() -> None:
    source = (ROOT / "ui" / "lunch_field10_multi_symbol_20260701.py").read_text()
    segment = source[source.index("def _crowd_row_styler"):source.index("def _render_session_entry_map")]
    assert "background-color" in segment and "color:" in segment
    assert "Crowd State" in segment and "Final Less-Risky Bias to Hold" in segment


# 27
def test_shadow_model_versions_are_registered_and_not_promoted(published_db: dict[str, Any]) -> None:
    from core.field10_crowd_final_20260704 import CROWD_MODEL_VERSION, FINAL_MODEL_VERSION, FORMULA_AND_THRESHOLD_REGISTRY

    assert CROWD_MODEL_VERSION == "field10_crowd_psychology_candidate_v1"
    assert FINAL_MODEL_VERSION == "field10_final_multi_symbol_candidate_v1"
    assert FORMULA_AND_THRESHOLD_REGISTRY["status"] == "SHADOW_ONLY_NOT_PRODUCTION_VALIDATED"
    with sqlite3.connect(published_db["path"]) as conn:
        statuses = {row[0] for row in conn.execute("SELECT DISTINCT validation_status FROM field10_daily_final_multi_symbol_rank")}
    assert statuses == {"SHADOW_ONLY_NOT_PROMOTED"}


# 28
def test_python_312_runtime_and_import_contract_are_present() -> None:
    assert (ROOT / ".python-version").read_text().strip() == "3.12"
    source = (ROOT / "core" / "field10_crowd_final_20260704.py").read_text()
    assert "from __future__ import annotations" in source
    compile(source, str(ROOT / "core" / "field10_crowd_final_20260704.py"), "exec")


# 29
def test_field10_table_order_matches_acceptance_order() -> None:
    source = (ROOT / "ui" / "lunch_field10_multi_symbol_20260701.py").read_text()
    whole = source.index("field10_authoritative_rank_table_pinned_20260703")
    session = source.index("_render_session_entry_map(metadata)")
    sentiment = source.index("_render_finnhub_sentiment_rank(metadata, state)")
    crowd = source.index("_render_crowd_psychology_rank(metadata)")
    final = source.index("_render_final_multi_symbol_rank(metadata)")
    history = source.index("Open / Close — Latest 25 broker days immutable history")
    assert whole < session < sentiment < crowd < final < history


# 30
def test_field10_expanders_do_not_trigger_api_or_heavy_model_calls() -> None:
    source = (ROOT / "ui" / "lunch_field10_multi_symbol_20260701.py").read_text()
    start = source.index("def _render_session_entry_map")
    end = source.index("def _render_locked_morning_snapshot")
    segment = source[start:end]
    forbidden = (
        "publish_crowd_and_final_tables", "migrate_crowd_final_database", "refresh_and_persist",
        "fetch_market_news", "run_settings_calculation", "run_selected_symbols", "fit(", "train(",
    )
    assert not any(token in segment for token in forbidden)
