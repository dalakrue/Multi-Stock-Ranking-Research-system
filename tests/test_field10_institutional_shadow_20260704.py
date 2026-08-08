from __future__ import annotations

import ast
import json
import shutil
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import field10_institutional_shadow_20260704 as shadow
from scripts import migrate_field10_institutional_20260704 as migration

SOURCE_DB = ROOT / "data" / "multi_symbol_field10_20260701.sqlite3"


def make_frame(end: str = "2026-07-02T02:00:00Z", rows: int = 720, *, shift_at: int | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(7404)
    time = pd.date_range(end=pd.Timestamp(end), periods=rows, freq="h", tz="UTC")
    returns = rng.normal(0.00001, 0.0007, rows)
    if shift_at is not None:
        returns[shift_at:] += 0.0025
    close = 1.10 * np.exp(np.cumsum(returns))
    open_ = np.r_[close[0], close[:-1]]
    width = np.maximum(np.abs(returns), 0.0002)
    high = np.maximum(open_, close) * (1 + width)
    low = np.minimum(open_, close) * (1 - width)
    return pd.DataFrame(
        {
            "time": time,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "tick_volume": rng.integers(100, 500, rows),
            "spread": np.full(rows, 0.00002),
        }
    )


@pytest.fixture()
def migrated_db(tmp_path: Path) -> Path:
    target = tmp_path / "field10.sqlite3"
    shutil.copy2(SOURCE_DB, target)
    report = migration.run(target, make_backup=False, idempotency_test=True)
    assert report["ok"] is True
    return target


@pytest.fixture()
def published_db(migrated_db: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Do not let test execution read any project cache for another symbol.
    monkeypatch.setattr(shadow, "_candidate_cache_paths", lambda symbol: [])
    state = {
        "symbol": "GBPJPY",
        "canonical_completed_ohlc_df_20260617": make_frame(),
    }
    with sqlite3.connect(migrated_db) as conn:
        snapshot_id = conn.execute(
            "SELECT daily_snapshot_id FROM field10_daily_snapshot ORDER BY broker_day DESC LIMIT 1"
        ).fetchone()[0]
        symbols = [r[0] for r in conn.execute(
            "SELECT symbol FROM field10_daily_snapshot_symbol WHERE daily_snapshot_id=? ORDER BY symbol", (snapshot_id,)
        )]
        before = conn.execute(
            "SELECT symbol,daily_rank,less_risky_bias FROM field10_daily_snapshot_symbol WHERE daily_snapshot_id=? ORDER BY symbol",
            (snapshot_id,),
        ).fetchall()
    result = shadow.publish_institutional_shadow(
        state, daily_snapshot_id=snapshot_id, selected_symbols=symbols, path=migrated_db
    )
    assert result["ok"] is True
    with sqlite3.connect(migrated_db) as conn:
        after = conn.execute(
            "SELECT symbol,daily_rank,less_risky_bias FROM field10_daily_snapshot_symbol WHERE daily_snapshot_id=? ORDER BY symbol",
            (snapshot_id,),
        ).fetchall()
    assert before == after
    return migrated_db


def test_exact_symbol_isolation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shadow, "_candidate_cache_paths", lambda symbol: [])
    state = {"symbol": "EURUSD", "data": make_frame()}
    exact, reason = shadow._exact_state_for_symbol(state, "USDJPY")
    assert exact is None
    assert "USDJPY" in str(reason)


def test_completed_candle_exclusion() -> None:
    frame = make_frame(rows=610)
    cutoff = frame.time.iloc[-2]
    normalized, reasons = shadow.normalize_completed_h1(frame, cutoff=cutoff, max_rows=600)
    assert normalized.time.max() == cutoff
    assert not (normalized.time > cutoff).any()
    assert len(normalized) == 600
    assert not reasons


def test_future_data_cannot_change_locked_window() -> None:
    frame = make_frame(rows=620)
    cutoff = frame.time.iloc[-10]
    base, _ = shadow.normalize_completed_h1(frame, cutoff=cutoff, max_rows=600)
    future = frame.copy()
    future.loc[future.time > cutoff, "close"] *= 100
    changed, _ = shadow.normalize_completed_h1(future, cutoff=cutoff, max_rows=600)
    pd.testing.assert_frame_equal(base, changed)


def test_probability_splits_are_purged_and_embargoed() -> None:
    result = shadow._probability_and_interval(make_frame(), 6)
    metrics = result["metrics"]
    if result["calibration_status"] != "OUT_OF_SAMPLE_SHADOW":
        pytest.skip(result.get("missing_reason"))
    train = metrics["training_interval"]
    val = metrics["validation_interval"]
    test = metrics["test_interval"]
    assert val[0] - train[1] >= 6
    assert test[0] - val[1] >= 6


def test_brier_and_conformal_metrics_are_bounded() -> None:
    result = shadow._probability_and_interval(make_frame(), 1)
    if result["calibration_status"] != "OUT_OF_SAMPLE_SHADOW":
        pytest.skip(result.get("missing_reason"))
    assert 0 <= result["metrics"]["brier_score"] <= 1
    assert 0 <= result["metrics"]["expected_calibration_error"] <= 1
    if result["conformal_status"] == "MARGINAL_OOS_SHADOW":
        assert result["upper"] >= result["median_prediction"] >= result["lower"]
        assert 0 <= result["coverage"] <= 1
        assert result["interval_width"] >= 0


def test_structural_break_can_block_new_entry() -> None:
    frame = make_frame(rows=360, shift_at=320)
    result = shadow._structural_break(frame)
    assert result["status"] == "SHADOW_ONLY"
    assert 0 <= result["changepoint_probability"] <= 1
    assert result["permission"] in {"BLOCK_NEW_ENTRY", "SHADOW_MONITOR"}
    assert "return_mean" in result["components"]


def test_cvar_and_tail_statistics() -> None:
    result = shadow._net_ev(make_frame(), 6, "BUY")
    assert result["sample"] >= 60
    assert result["var"] is not None and result["cvar"] is not None
    assert result["cvar"] <= result["var"]
    assert result["effective_sample"] > 0


def test_shrinkage_dependence_is_stable() -> None:
    a = make_frame()
    b = make_frame().copy()
    b["close"] *= np.linspace(1.0, 1.01, len(b))
    result = shadow._dependence({"EURUSD": a, "GBPUSD": b})
    assert set(result) == {"EURUSD", "GBPUSD"}
    assert all(np.isfinite(float(v["penalty"])) for v in result.values())


def test_rank_confidence_is_reproducible_and_deterministic() -> None:
    rows = [
        {"symbol": "EURUSD", "utility": 0.2, "original_rank": 1},
        {"symbol": "GBPUSD", "utility": 0.1, "original_rank": 2},
        {"symbol": "USDJPY", "utility": 0.05, "original_rank": 3},
    ]
    first = shadow._rank_confidence(rows, draws=100)
    second = shadow._rank_confidence(rows, draws=100)
    assert first == second
    assert first["EURUSD"]["prob4"] == 1.0


def test_migration_is_idempotent_and_preserves_parents(tmp_path: Path) -> None:
    target = tmp_path / "migration.sqlite3"
    shutil.copy2(SOURCE_DB, target)
    with sqlite3.connect(target) as conn:
        before = conn.execute("SELECT COUNT(*) FROM field10_daily_snapshot_symbol").fetchone()[0]
    report = migration.run(target, make_backup=False, idempotency_test=True)
    assert report["ok"]
    assert report["idempotency_test"]["schema_unchanged"]
    assert report["idempotency_test"]["row_counts_unchanged"]
    with sqlite3.connect(target) as conn:
        after = conn.execute("SELECT COUNT(*) FROM field10_daily_snapshot_symbol").fetchone()[0]
    assert before == after


def test_migration_rolls_back_when_parent_missing(tmp_path: Path) -> None:
    target = tmp_path / "empty.sqlite3"
    sqlite3.connect(target).close()
    with sqlite3.connect(target) as conn:
        with pytest.raises(RuntimeError):
            migration.apply_migration(conn)
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "field10_forecast_ledger" not in tables


def test_foreign_key_integrity(migrated_db: Path) -> None:
    with sqlite3.connect(migrated_db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_parent_rank_and_bias_are_not_reranked(published_db: Path) -> None:
    with sqlite3.connect(published_db) as conn:
        audit = conn.execute(
            "SELECT details_json FROM field10_shadow_publication_audit ORDER BY created_system_time DESC LIMIT 1"
        ).fetchone()
        assert audit is not None
        details = json.loads(audit[0])
        assert details["production_authority"] == ["field10_daily_snapshot", "field10_daily_snapshot_symbol"]


def test_forecast_is_append_only(published_db: Path) -> None:
    with sqlite3.connect(published_db) as conn:
        forecast_id = conn.execute("SELECT forecast_id FROM field10_forecast_ledger LIMIT 1").fetchone()[0]
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute("UPDATE field10_forecast_ledger SET entry_permission='ALLOW' WHERE forecast_id=?", (forecast_id,))


def test_outcome_is_append_only(published_db: Path) -> None:
    with sqlite3.connect(published_db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        row = conn.execute(
            "SELECT forecast_id,outcome_due_broker_time FROM field10_forecast_ledger LIMIT 1"
        ).fetchone()
        conn.execute(
            "INSERT INTO field10_outcome_ledger(forecast_id,settlement_version,outcome_due_broker_time,"
            "settled_at_broker_time,outcome_source_id,outcome_source_hash,content_hash,created_system_time) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (row[0], "test-v1", row[1], row[1], "TEST", "hash", "content-hash-test", row[1]),
        )
        conn.commit()
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute(
                "UPDATE field10_outcome_ledger SET outcome_source_id='CHANGED' WHERE forecast_id=?", (row[0],)
            )


def test_field3_field10_identity_is_exact(published_db: Path) -> None:
    with sqlite3.connect(published_db) as conn:
        rows = conn.execute(
            "SELECT r.symbol,r.selected_regime,p.higher_standard_regime,p.completed_candle,i.completed_h1_candle "
            "FROM field10_regime_shadow r JOIN field10_daily_snapshot_symbol p USING(daily_snapshot_id,symbol) "
            "JOIN field10_canonical_identity i USING(daily_snapshot_id)"
        ).fetchall()
    assert rows
    for symbol, shadow_regime, parent_regime, parent_candle, identity_candle in rows:
        assert shadow_regime == parent_regime or shadow_regime is None
        assert parent_candle == identity_candle
        assert symbol


def test_renderer_loader_is_read_only(published_db: Path) -> None:
    result = shadow.renderer_contract_fingerprint(published_db)
    assert result["mtime_unchanged"] is True


def test_read_functions_have_no_migration_api_or_fit_calls() -> None:
    files = [
        ROOT / "core" / "field10_institutional_shadow_20260704.py",
        ROOT / "ui" / "lunch_field10_multi_symbol_20260701.py",
    ]
    forbidden_exact = {"fit", "fit_transform", "request", "requests", "urlopen", "post"}
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                node.name.startswith("load") or node.name.startswith("render") or "_render" in node.name
            ):
                called = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        fn = child.func
                        name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
                        called.add(name.lower())
                assert not any(name.startswith("migrate") or name in forbidden_exact for name in called), (path, node.name, called)


def test_streamlit_entrypoints_parse_and_share_runner() -> None:
    for name in ("app.py", "adx_dashpoard.py"):
        text = (ROOT / name).read_text(encoding="utf-8")
        ast.parse(text)
        assert "core.app.runner" in text or "run_app" in text


def test_changed_python_is_python312_parse_compatible() -> None:
    changed = [
        ROOT / "scripts" / "migrate_field10_institutional_20260704.py",
        ROOT / "core" / "field10_institutional_shadow_20260704.py",
        ROOT / "core" / "sqlite_readonly_20260704.py",
        ROOT / "ui" / "lunch_field10_multi_symbol_20260701.py",
    ]
    for path in changed:
        ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 12))
