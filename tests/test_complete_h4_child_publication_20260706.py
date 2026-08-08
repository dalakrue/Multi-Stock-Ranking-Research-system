from __future__ import annotations

from pathlib import Path
import ast
import json
import sqlite3

import pandas as pd
import pytest

from core.h4_acceptance_workflow_20260706 import run_offline_h4_acceptance
from core.multi_symbol_field10_20260701 import _progress_snapshot, TOP_10_CURRENCY_PAIRS
from core.timeframe_window_contract_20260706 import (
    BARS_PER_DAY, TIMEFRAME_SECONDS, horizon_contract, required_candles,
)
from ui.lunch_field10_multi_symbol_20260701 import _display_value

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def acceptance(tmp_path_factory):
    root = tmp_path_factory.mktemp("h4_full_acceptance")
    result = run_offline_h4_acceptance(root)
    assert result["ok"], json.dumps(result, indent=2, default=str)
    return result


def test_01_select_ten_currency_symbols_and_h4(acceptance):
    assert acceptance["selected_symbols"] == list(TOP_10_CURRENCY_PAIRS)
    assert acceptance["timeframe"] == "H4"


def test_02_super_quick_fixture_workflow_passes(acceptance):
    assert acceptance["status"] == "PASSED"


def test_03_all_ten_reach_completed_not_partial(acceptance):
    assert len(acceptance["completed_symbols"]) == 10
    assert acceptance["checks"]["ten_symbols_completed"]


def test_04_h4_higher_standard_requires_150():
    assert BARS_PER_DAY["H4"] == 6
    assert required_candles("H4", "higher") == 150


def test_05_h1_higher_standard_remains_600():
    assert BARS_PER_DAY["H1"] == 24
    assert required_candles("H1", "higher") == 600


def test_06_field1_load_changes_identity_and_history(acceptance):
    assert acceptance["checks"]["field1_load_changed_identity"]
    assert acceptance["field1_load"]["symbol"] == "USDJPY"


def test_07_field2_load_changes_powerbi_bundle(acceptance):
    assert acceptance["checks"]["field2_load_changed_bundle"]
    assert acceptance["field2_loaded_symbol"] == "AUDUSD"


def test_08_switching_does_not_change_settings_main_symbol(acceptance):
    assert acceptance["checks"]["settings_main_symbol_unchanged"]


def test_09_switching_is_read_only_and_does_not_call_api():
    source = (ROOT / "ui/lunch_multi_symbol_selector_20260704.py").read_text(encoding="utf-8")
    load_source = source[source.index("def _load"):source.index("def render")]
    assert "activate_symbol_view" in load_source
    assert "requests." not in load_source
    assert "single_symbol_runner" not in load_source
    assert "heavy_calculation_triggered\": False" in load_source


def test_10_selector_uses_form_and_no_post_widget_key_assignment():
    path = ROOT / "ui/lunch_multi_symbol_selector_20260704.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    render = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "render")
    assert "with st.form" in source
    assert "form_submit_button(\"Load Selected Symbol\"" in source
    assert "Selection alone does nothing" in source
    # The widget-owned key is initialized before selectbox and is not assigned
    # in the submitted branch after widget instantiation.
    submitted_block = source[source.index("    report: Mapping"):source.index("    row = _rank_row")]
    assert "state[key] =" not in submitted_block
    assert render is not None


def test_11_every_symbol_has_distinct_child_snapshot(acceptance):
    db = Path(acceptance["database"]["path"])
    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            "SELECT symbol,child_run_id,snapshot_hash,source_id FROM child_snapshot_publication_20260706 "
            "WHERE publication_status='COMPLETED'"
        ).fetchall()
    assert len(rows) == 10
    assert len({row[1] for row in rows}) == 10
    assert len({row[2] for row in rows}) == 10
    assert len({row[3] for row in rows}) == 10


def test_12_field10_tables_include_time_and_timeframe_columns():
    source = (ROOT / "core/multi_symbol_field10_20260701.py").read_text(encoding="utf-8")
    assert "AS [Completed Broker Candle]" in source
    assert "AS Timeframe" in source
    ui_source = (ROOT / "ui/lunch_field10_multi_symbol_20260701.py").read_text(encoding="utf-8")
    assert '"Time"' in ui_source and '"Timeframe"' in ui_source


def test_13_h4_spacing_and_horizon_duration_are_real():
    assert TIMEFRAME_SECONDS["H4"] == 14_400
    six_bars = horizon_contract(timeframe="H4", horizon_bars=6)
    six_hours = horizon_contract(timeframe="H4", horizon_hours=6)
    assert six_bars["horizon_hours"] == 24.0
    assert six_hours["horizon_bars"] == 2


def test_14_no_symbol_borrows_another_symbols_source(acceptance):
    assert acceptance["checks"]["distinct_exact_symbol_sources"]
    db = Path(acceptance["database"]["path"])
    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            "SELECT symbol,source_id FROM child_snapshot_publication_20260706 WHERE publication_status='COMPLETED'"
        ).fetchall()
    assert all(symbol in source_id for symbol, source_id in rows)


def test_15_powerbi_identity_is_complete_for_every_symbol(acceptance):
    db = Path(acceptance["database"]["path"])
    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            "SELECT symbol,canonical_run_id,generation_id,snapshot_hash,completed_candle,bundle_json "
            "FROM field2_powerbi_publication_20260706"
        ).fetchall()
    assert len(rows) == 10
    for symbol, run_id, generation, snapshot_hash, completed, bundle_json in rows:
        bundle = json.loads(bundle_json)
        assert all((run_id, generation, snapshot_hash, completed))
        assert bundle["symbol"] == symbol
        assert bundle["timeframe"] == "H4"


def test_16_session_clear_reloads_all_ten_from_sqlite(acceptance):
    assert acceptance["checks"]["session_clear_sqlite_reload"]
    assert set(acceptance["reload_after_session_clear"].values()) == {"COMPLETE_CHILD_RESTORED"}


def test_17_100_percent_processing_cannot_false_complete():
    symbols = ["EURUSD", "USDJPY"]
    statuses = {
        "EURUSD": {"percent": 100, "state": "COMPLETED"},
        "USDJPY": {"percent": 100, "state": "FAILED_VALIDATION"},
    }
    snapshot = _progress_snapshot("P", symbols, statuses)
    assert snapshot["progress_percent"] == 100.0
    assert snapshot["publication_status"] == "PARTIAL"
    assert snapshot["completed_symbols"] == 1
    assert snapshot["failed_symbols"] == 1


def test_18_mobile_history_has_actual_rows_not_generated_blanks(acceptance):
    cache_path = Path(acceptance["field1_load"]["path"])
    import gzip
    from core.serialization_compat_20260702 import loads
    payload = loads(gzip.decompress(cache_path.read_bytes()))
    history = payload["state"]["field1_table1_decision_history_20260628"]
    assert isinstance(history, pd.DataFrame)
    assert len(history) == 40
    assert not history.drop(columns=["Decision", "Symbol"], errors="ignore").isna().all(axis=1).any()
    ui = (ROOT / "ui/lunch_four_core_fields_20260619.py").read_text(encoding="utf-8")
    assert "min(560" in ui or "35 * len" in ui or "dynamic" in ui.lower()


def test_19_reliability_and_float_formatting_is_controlled():
    assert _display_value(0.00010000000000000003) == "0.0001"
    assert _display_value(float("nan")) == "—"
    assert _display_value(None) == "—"


def test_20_production_formulas_and_thresholds_are_not_shadow_modified():
    shadow = (ROOT / "core/field10_shadow_research_candidates_20260706.py").read_text(encoding="utf-8")
    assert '"promotion_status": "NOT_PROMOTED"' in shadow
    assert '"production_decision_changed": False' in shadow
    assert "final_decision" not in shadow
    # Existing protected hash tests remain part of the full suite; this module
    # itself is additive and does not import a production decision setter.
    assert "publish_canonical" not in shadow
