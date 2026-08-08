from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from core.institutional_quant_migration_20260708 import TABLES, migrate_institutional_quant_schema
from core.institutional_quant_layer_20260708 import (
    FIELD10_KEY,
    FIELD3_KEY,
    FIELD11_KEY,
    NEWS_KEY,
    RESEARCH_KEY,
    canonical_symbols_from_state,
    publish_institutional_quant_run,
)
from core.multi_symbol_load_manager_20260707 import LOAD_RECORDS_KEY, CANONICAL_GROUP
from core.data.market_data_orchestrator import FCS_PROVIDER, TWELVE_POOL_PROVIDER, provider_priority_for_state


def _frame(seed: int, rows: int = 300) -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=rows, freq="4h", tz="UTC")
    rng = np.random.default_rng(seed)
    close = 1.1 + rng.normal(0, 0.0012, len(idx)).cumsum()
    return pd.DataFrame({
        "open_time": idx,
        "open": close,
        "high": close + 0.001,
        "low": close - 0.001,
        "close": close,
        "volume": 100,
    })


def _state() -> dict:
    return {
        "canonical_selected_symbols": ["EURUSD", "GBPUSD", "EURUSD", "USDJPY", "AUDUSD"],
        "canonical_ranking_timeframe": "H4",
        "field10_news_nlp_evidence_20260708": [
            {"title": "USD gains as inflation risk rises", "time": "2026-07-08T01:00:00Z"},
            {"title": "Euro growth improves after weak data", "time": "2026-07-08T01:05:00Z"},
        ],
        LOAD_RECORDS_KEY: {
            CANONICAL_GROUP: {
                "report": {
                    "results": {
                        "EURUSD": {"frame": _frame(1), "provider": "FCS_API_MAIN", "status": "VALIDATED"},
                        "GBPUSD": {"frame": _frame(2), "provider": "TWELVE_DATA_KEY_POOL", "status": "VALIDATED"},
                        "USDJPY": {"frame": _frame(3), "provider": "LOCAL_VALID_CACHE", "status": "VALIDATED"},
                    }
                }
            }
        },
    }


def test_migration_creates_requested_tables(tmp_path: Path) -> None:
    db = tmp_path / "adx.sqlite3"
    result = migrate_institutional_quant_schema(db)
    assert result["ok"] is True
    with sqlite3.connect(db) as conn:
        existing = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert set(TABLES).issubset(existing)
    assert "schema_migrations" in existing


def test_canonical_symbols_ordered_deduplicated_limit_12() -> None:
    state = {"canonical_selected_symbols": ["EUR/USD", "GBPUSD", "eurusd", "USD_JPY", "XAU USD"]}
    assert canonical_symbols_from_state(state) == ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]


def test_provider_route_uses_fcs_main_then_twelve_fallback() -> None:
    route = provider_priority_for_state({"fcs_api_access_key": "dummy", "twelve_api_key_1": "dummy2"})
    assert route[0] == FCS_PROVIDER
    assert TWELVE_POOL_PROVIDER in route
    assert route[-1] == "LOCAL_VALID_CACHE"


def test_publish_institutional_snapshot_all_tabs_and_news_columns() -> None:
    state = _state()
    status = publish_institutional_quant_run(state, {"run_id": "TEST_RUN"}, reason="pytest")
    assert status["ok"] is True
    ranking = state[FIELD10_KEY]
    assert list(ranking["Symbol"])  # ranked rows exist
    assert set(["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]).issubset(set(ranking["Symbol"]))
    for col in ["Latest News Title", "News Sentiment", "InstitutionalUtility", "Entry permission", "Snapshot Hash"]:
        assert col in ranking.columns
    assert len(state[FIELD3_KEY]["Symbol"].unique()) == 4
    assert not state[FIELD11_KEY].empty
    assert not state[NEWS_KEY].empty
    assert not state[RESEARCH_KEY].empty
    blocked = ranking.loc[ranking["Symbol"].eq("AUDUSD")].iloc[0]
    assert blocked["Entry permission"] in {"BLOCKED", "DATA DEGRADED", "WAIT"}
    assert str(blocked["Missing reason"]).strip()
    assert set(ranking["Timeframe"]) == {"H4"}
