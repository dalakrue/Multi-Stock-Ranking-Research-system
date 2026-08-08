from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import ast
import gzip
import sqlite3
import warnings

import pandas as pd

from core.child_generation_contract_20260702 import (
    ChildGenerationBundle,
    FrozenFrame,
    load_child_contract_tables,
    publish_child_generation_to_field10,
    self_heal_field10_from_snapshot,
    validate_bundle,
)
from core.generation_registry_20260702 import (
    SCHEMA_VERSION as REGISTRY_SCHEMA,
    calculate_valid_until,
    latest_valid_generation,
    register_completed_generation,
    verify_registry_snapshot,
)
from core.quick_run_feature_cache_20260702 import (
    append_completed_candle,
    get_or_build_shared_feature_bundle,
)
from core.serialization_compat_20260702 import dumps as serializer_dumps
from core.streamlit_compat_20260615 import _wrap_safe_slider
from core.symbol_context_20260702 import (
    ACTIVE_SNAPSHOT_SYMBOL_KEY,
    CONNECTOR_SYMBOL_KEY,
    LUNCH_DISPLAY_SYMBOL_KEY,
    MAIN_SYMBOL_KEY,
    SELECTED_SYMBOLS_KEY,
    SymbolContext,
    identity_invariants,
    normalize_selected,
    resolve_symbol_context,
)
from ui.lunch_next_hour_bias_history_20260626 import _coalesce_table1_frames


CANDLE = "2026-07-02T10:00:00+00:00"


def _context(symbol: str = "EURUSD") -> SymbolContext:
    return SymbolContext(
        settings_main_symbol="EURUSD",
        connector_symbol="EURUSD",
        calculation_symbol=symbol,
        lunch_display_symbol=symbol,
        active_snapshot_symbol=symbol,
        selected_symbols=("EURUSD", symbol) if symbol != "EURUSD" else ("EURUSD",),
        timeframe="H1",
        parent_run_id="PARENT-1",
        child_run_id=f"PARENT-1:{symbol}",
        canonical_run_id=f"RUN-{symbol}",
        source_id=f"SRC-{symbol}",
        snapshot_hash=f"HASH-{symbol}",
        completed_broker_candle=CANDLE,
        generation_status="COMPLETED",
        valid_until=calculate_valid_until(CANDLE, "H1", grace_seconds=90),
    )


def _table4(symbol: str = "EURUSD", rows: int = 3) -> pd.DataFrame:
    times = pd.date_range("2026-07-02 08:00:00+00:00", periods=rows, freq="h")
    return pd.DataFrame(
        {
            "Symbol": [symbol] * rows,
            "Broker Candle Time": times,
            "Technical Bias": ["BUY"] * rows,
            "Sentiment Bias": ["BUY"] * rows,
            "Session Bias": ["WAIT"] * rows,
            "Data Mining Bias": ["BUY"] * rows,
            "Combined Next-Hour Direction": ["BUY"] * rows,
            "Protected Final Action": ["BUY"] * rows,
        }
    )


def _standard(symbol: str, name: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Symbol": symbol,
                "Standard": name,
                "Regime": "BULL_NORMAL",
                "Regime Bias": "BUY",
                "Less-Risky Bias": "BUY",
                "Reliability": 82.0,
                "Sample Count": 100,
                "Regime Probability": 0.78,
                "Regime Entropy": 0.25,
                "Posterior Margin": 0.42,
                "Completed Broker Candle": CANDLE,
            }
        ]
    )


def _bundle(tmp_path: Path, symbol: str = "EURUSD") -> ChildGenerationBundle:
    snapshot = tmp_path / f"{symbol}.pkl.gz"
    snapshot.write_bytes(b"immutable-child-snapshot")
    from core.generation_registry_20260702 import file_sha256

    context = _context(symbol)
    table4 = _table4(symbol)
    lower = _standard(symbol, "Lower Standard")
    middle = _standard(symbol, "Middle Standard")
    higher = _standard(symbol, "Higher Standard")
    canonical = {
        "run_id": context.canonical_run_id,
        "symbol": symbol,
        "timeframe": "H1",
        "source_id": context.source_id,
        "snapshot_hash": context.snapshot_hash,
        "completed_broker_candle": CANDLE,
        "final_decision": {"action": "BUY"},
    }
    return ChildGenerationBundle(
        context=context,
        canonical=canonical,
        field1_table4_current=FrozenFrame.from_frame(table4.tail(1)),
        field1_table4_history=FrozenFrame.from_frame(table4),
        field1_table4_source_status="PUBLISHED",
        field3_lower_current=FrozenFrame.from_frame(lower),
        field3_middle_current=FrozenFrame.from_frame(middle),
        field3_higher_current=FrozenFrame.from_frame(higher),
        field3_lower_history=FrozenFrame.from_frame(lower),
        field3_middle_history=FrozenFrame.from_frame(middle),
        field3_higher_history=FrozenFrame.from_frame(higher),
        completed_broker_candle=CANDLE,
        source_frame_signature={"rows": 600, "last_rows_hash": "abc"},
        data_quality={"grade": "A", "score": 94, "status": "PASS"},
        protected_final_action="BUY",
        trade_permission="ALLOWED",
        runtime_snapshot_path=str(snapshot),
        runtime_snapshot_sha256=file_sha256(snapshot),
        calculation_timing={"total_seconds": 1.2},
        resource_metrics={"peak_rss_mb": 120},
        calculation_status="COMPLETED",
    )


def test_main_is_first_and_usdjpy_is_never_implicitly_inserted():
    assert normalize_selected(["GBPUSD"], main="EURUSD") == ("EURUSD", "GBPUSD")
    state = {MAIN_SYMBOL_KEY: "EURUSD", SELECTED_SYMBOLS_KEY: ["GBPUSD"]}
    context = resolve_symbol_context(state, "Settings")
    assert context.selected_symbols == ("EURUSD", "GBPUSD")
    assert "USDJPY" not in context.selected_symbols


def test_saved_main_has_priority_over_legacy_generic_usdjpy_and_survives_reruns():
    state = {MAIN_SYMBOL_KEY: "GBPUSD", SELECTED_SYMBOLS_KEY: ["GBPUSD", "EURUSD"], "symbol": "USDJPY"}
    first = resolve_symbol_context(state, "Settings")
    second = resolve_symbol_context(state, "Settings")
    assert first.settings_main_symbol == second.settings_main_symbol == "GBPUSD"
    assert first.selected_symbols[0] == "GBPUSD"


def test_lunch_display_can_differ_without_changing_main_or_connector():
    state = {
        MAIN_SYMBOL_KEY: "EURUSD",
        CONNECTOR_SYMBOL_KEY: "EURUSD",
        SELECTED_SYMBOLS_KEY: ["EURUSD", "GBPUSD"],
        LUNCH_DISPLAY_SYMBOL_KEY: "GBPUSD",
        ACTIVE_SNAPSHOT_SYMBOL_KEY: "GBPUSD",
        "canonical_decision_result_20260617": {
            "symbol": "GBPUSD", "run_id": "R", "snapshot_hash": "H",
            "completed_broker_candle": CANDLE,
        },
    }
    context = resolve_symbol_context(state, "Lunch")
    assert context.settings_main_symbol == "EURUSD"
    assert context.connector_symbol == "EURUSD"
    assert context.lunch_display_symbol == "GBPUSD"
    assert context.active_snapshot_symbol == "GBPUSD"


def test_identity_invariants_report_all_lunch_surfaces():
    state = {
        MAIN_SYMBOL_KEY: "EURUSD",
        CONNECTOR_SYMBOL_KEY: "EURUSD",
        SELECTED_SYMBOLS_KEY: ["EURUSD", "GBPUSD"],
        LUNCH_DISPLAY_SYMBOL_KEY: "GBPUSD",
        ACTIVE_SNAPSHOT_SYMBOL_KEY: "GBPUSD",
        "canonical_decision_result_20260617": {"symbol": "GBPUSD", "run_id": "R", "snapshot_hash": "H", "completed_broker_candle": CANDLE},
        "top_market_symbol_20260702": "GBPUSD",
        "field1_active_symbol_20260702": "GBPUSD",
        "field2_active_symbol_20260702": "GBPUSD",
        "field3_active_symbol_20260702": "GBPUSD",
        "field10_active_symbol_20260702": "GBPUSD",
        "copy_active_symbol_20260702": "GBPUSD",
    }
    report = identity_invariants(state)
    assert report["ok"] is True
    assert not report["failures"]


def test_copy_fingerprint_changes_only_for_identity_not_unrelated_filters():
    context = _context("EURUSD")
    first = context.copy_fingerprint()
    unrelated_filter = "BUY"
    assert unrelated_filter == "BUY" and context.copy_fingerprint() == first
    assert replace(context, lunch_display_symbol="GBPUSD", active_snapshot_symbol="GBPUSD").copy_fingerprint() != first


def test_timeframe_valid_until_boundaries():
    assert calculate_valid_until(CANDLE, "H1", 0) == "2026-07-02T11:00:00+00:00"
    assert calculate_valid_until(CANDLE, "M30", 0) == "2026-07-02T10:30:00+00:00"
    assert calculate_valid_until(CANDLE, "H4", 0) == "2026-07-02T14:00:00+00:00"


def test_generation_registry_restores_before_valid_until_and_rejects_expiry(tmp_path: Path):
    db = tmp_path / "registry.sqlite3"
    snapshot = tmp_path / "saved.pkl.gz"
    snapshot.write_bytes(b"saved")
    context = _context().to_dict() | {"symbol": "EURUSD"}
    result = register_completed_generation(context=context, runtime_snapshot_path=snapshot, publication_status="COMPLETED", path=db)
    assert result["ok"] is True
    valid = latest_valid_generation(path=db, now="2026-07-02T10:30:00+00:00")
    expired = latest_valid_generation(path=db, now="2026-07-02T12:00:00+00:00")
    assert valid["symbol"] == "EURUSD"
    assert verify_registry_snapshot(valid)["ok"] is True
    assert expired == {}
    assert valid["schema_version"] == REGISTRY_SCHEMA


def test_child_cannot_complete_when_table4_or_any_field3_standard_is_missing(tmp_path: Path):
    base = _bundle(tmp_path)
    cases = [
        (replace(base, field1_table4_current=FrozenFrame((), ())), "MISSING_TABLE4_CURRENT"),
        (replace(base, field1_table4_history=FrozenFrame((), ())), "MISSING_TABLE4_HISTORY"),
        (replace(base, field3_lower_current=FrozenFrame((), ())), "MISSING_FIELD3_LOWER"),
        (replace(base, field3_middle_current=FrozenFrame((), ())), "MISSING_FIELD3_MIDDLE"),
        (replace(base, field3_higher_current=FrozenFrame((), ())), "MISSING_FIELD3_HIGHER"),
    ]
    for bundle, expected in cases:
        assert validate_bundle(bundle)[0] == expected
        result = publish_child_generation_to_field10(bundle, path=tmp_path / f"{expected}.sqlite3")
        assert result["ok"] is False
        assert result["status"] == expected


def test_atomic_publish_creates_exact_field10_row_and_three_standard_table(tmp_path: Path):
    db = tmp_path / "field10.sqlite3"
    bundle = _bundle(tmp_path)
    result = publish_child_generation_to_field10(bundle, path=db)
    assert result["ok"] is True
    assert result["verified_count"] == 1
    assert result["field3_standard_count"] == 3
    tables = load_child_contract_tables(path=db, parent_run_id="PARENT-1", symbol="EURUSD")
    assert tables["ok"] is True
    assert set(tables["table4_history"]["Symbol"]) == {"EURUSD"}
    assert list(tables["field3_current"]["Standard"]) == ["Lower Standard", "Middle Standard", "Higher Standard"]
    with sqlite3.connect(db) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM field10_integrated_evidence_history WHERE parent_run_id=? AND child_run_id=? AND symbol=? AND timeframe=? AND canonical_run_id=? AND snapshot_hash=? AND broker_timestamp=?",
            bundle.identity_tuple()[0:2] + ("EURUSD", "H1", "RUN-EURUSD", "HASH-EURUSD", CANDLE),
        ).fetchone()[0]
    assert count == 1


def test_self_heal_republishes_only_from_saved_snapshot_and_never_fabricates(tmp_path: Path, monkeypatch):
    db = tmp_path / "heal.sqlite3"
    snapshot = tmp_path / "EURUSD.pkl.gz"
    bundle = _bundle(tmp_path)
    cached_state = {"canonical_decision_result_20260617": {"symbol": "EURUSD", "run_id": "RUN-EURUSD"}}
    snapshot.write_bytes(gzip.compress(serializer_dumps({"state": cached_state})))
    from core.generation_registry_20260702 import file_sha256
    bundle = replace(bundle, runtime_snapshot_path=str(snapshot), runtime_snapshot_sha256=file_sha256(snapshot))
    assert publish_child_generation_to_field10(bundle, path=db)["ok"] is True
    with sqlite3.connect(db) as conn:
        conn.execute("DELETE FROM field10_integrated_evidence_history")
        conn.commit()
    monkeypatch.setattr("core.child_generation_contract_20260702.build_child_generation_bundle", lambda **kwargs: bundle)
    healed = self_heal_field10_from_snapshot(path=db, parent_run_id="PARENT-1", symbol="EURUSD", completed_broker_candle=CANDLE)
    assert healed["ok"] is True, healed
    assert healed["status"] == "REPAIRED_FROM_VALID_SNAPSHOT"
    missing = self_heal_field10_from_snapshot(path=tmp_path / "empty.sqlite3", parent_run_id="NONE", symbol="GBPUSD")
    assert missing["ok"] is False
    assert missing["status"] == "NO_CHILD_GENERATION"


def test_shared_feature_bundle_is_fingerprint_cached_and_incremental_append_is_deduplicated():
    frame = pd.DataFrame({
        "time": pd.date_range("2026-07-01", periods=40, freq="h", tz="UTC"),
        "open": range(40), "high": [x + 1 for x in range(40)],
        "low": [x - 1 for x in range(40)], "close": [x + 0.5 for x in range(40)],
    })
    state = {}
    first = get_or_build_shared_feature_bundle(state, frame, provider="MT5", symbol="EURUSD", timeframe="H1", completed_broker_candle=frame.time.iloc[-1], calculation_version="v1")
    second = get_or_build_shared_feature_bundle(state, frame, provider="MT5", symbol="EURUSD", timeframe="H1", completed_broker_candle=frame.time.iloc[-1], calculation_version="v1")
    assert first.cache_hit is False and second.cache_hit is True
    assert {"return_1", "volatility_24", "adx_14", "session_input"}.issubset(second.frame.columns)
    old = frame.iloc[:39]
    appended = append_completed_candle(old, frame.iloc[38:], time_column="time")
    assert len(appended) == 40


def test_equal_slider_min_max_uses_read_only_fallback_without_calling_slider():
    calls = []
    wrapped = _wrap_safe_slider(lambda *args, **kwargs: calls.append((args, kwargs)))
    assert wrapped("Hour", min_value=4, max_value=4, value=4) == 4
    assert calls == []


def test_table_coalesce_does_not_emit_incompatible_dtype_futurewarning():
    visible = pd.DataFrame({"Broker Candle Time": [CANDLE], "Hour": [float("nan")]})
    fallback = pd.DataFrame({"Broker Candle Time": [CANDLE], "Hour": ["04:00"]})
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = _coalesce_table1_frames([visible, fallback])
    assert result.iloc[0]["Hour"] == "04:00"
    assert not any("incompatible dtype" in str(item.message).lower() for item in caught)


def test_no_duplicate_keyword_arguments_in_python_source_and_no_field10_activation_call():
    for path in Path(".").rglob("*.py"):
        if any(part in {".pytest_cache", "__pycache__"} for part in path.parts):
            continue
        ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    source = Path("core/child_generation_contract_20260702.py").read_text(encoding="utf-8")
    publisher = source[source.index("def publish_child_generation_to_field10"):source.index("def _decode_evidence_rows")]
    assert "activate_symbol_result" not in publisher
    settings_source = Path("ui/multi_symbol_settings_20260701.py").read_text(encoding="utf-8")
    assert 'state["selected_symbol"] =' not in settings_source
    assert 'state["ws_symbol"] =' not in settings_source


def test_field10_renderer_preserves_required_a_to_f_structure_and_copy_label():
    source = Path("ui/lunch_field10_multi_symbol_20260701.py").read_text(encoding="utf-8")
    headings = [
        "#### A. Field 10 Symbol Selector",
        "#### B. Current Completed H1 Integrated Table",
        "#### C. Field 1 Table 4 History — Last 25 Broker Days",
        "#### D. Field 3 Three-Standard Quick-Look Table",
        "#### E. 25-Day Regime History",
        "#### F. Current Identity and Publication Diagnostics",
    ]
    positions = [source.index(heading) for heading in headings]
    assert positions == sorted(positions)
    copy_source = Path("ui/canonical_copy_export_20260619.py").read_text(encoding="utf-8")
    assert "Current Fields 1–3 + Field 10 Copy — {active_symbol}" in copy_source
    assert copy_source.count('central_copy_button("Copy Short"') >= 1
    assert copy_source.count('central_copy_button("Copy Full"') >= 1
