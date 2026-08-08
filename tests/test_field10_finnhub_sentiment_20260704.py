from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd


def _prepare_snapshot(path: Path) -> str:
    from core.multi_symbol_field10_20260701 import migrate_database
    from core.field10_daily_snapshot_contract_20260702 import migrate_daily_snapshot_database
    from core.field10_integrated_evidence_20260702 import migrate_integrated_evidence_database
    from core.child_generation_contract_20260702 import migrate_child_publication_contract

    migrate_database(path)
    migrate_daily_snapshot_database(path)
    migrate_integrated_evidence_database(path)
    migrate_child_publication_contract(path)
    snapshot_id = "F10-TEST-FINNHUB"
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
                snapshot_id, "2026-07-04", "2026-07-04T06:00:00+00:00",
                "2026-07-04T05:00:00+00:00", json.dumps(["EURUSD", "USDJPY"]),
                "universe", "EURUSD", json.dumps(["USDJPY"]), "{}", 2, "PARENT",
                "{}", "{}", "{}", "{}", "model", "formula", "threshold",
                "snapshot-content", "PUBLISHED_LOCKED", "2026-07-04T06:00:00+00:00",
                "2026-07-04T23:00:00+00:00", "{}", "2026-07-04T06:00:00+00:00",
            ),
        )
        for rank, symbol in enumerate(("EURUSD", "USDJPY"), start=1):
            conn.execute(
                """INSERT INTO field10_daily_snapshot_symbol(
                    daily_snapshot_id,broker_day,symbol,role,daily_rank,daily_grade,
                    eligibility_status,trade_permission,sample_count,sample_complete_status,
                    content_hash,row_json,score_explanation_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (snapshot_id, "2026-07-04", symbol, "MAIN" if rank == 1 else "SECONDARY",
                 rank, "A", "ELIGIBLE", "ALLOW", 600, "COMPLETE",
                 f"hash-{symbol}", json.dumps({"Symbol": symbol, "Rank": rank}), "{}"),
            )
        conn.commit()
    return snapshot_id


def test_finnhub_rows_are_persisted_and_pair_mapping_is_correct(tmp_path: Path, monkeypatch) -> None:
    from core import finnhub_connector
    from core.field10_finnhub_sentiment_20260704 import (
        load_finnhub_sentiment_rank,
        refresh_and_persist_finnhub_sentiment,
    )

    db = tmp_path / "field10.sqlite3"
    snapshot_id = _prepare_snapshot(db)
    release = int(pd.Timestamp("2026-07-04T04:00:00Z").timestamp())
    monkeypatch.setattr(finnhub_connector, "connection_status", lambda: {"connected": True, "availability": "AVAILABLE"})
    monkeypatch.setattr(
        finnhub_connector,
        "fetch_market_news",
        lambda *args, **kwargs: [{
            "id": 101,
            "headline": "Fed turns hawkish as US growth strengthens",
            "summary": "Federal Reserve officials signal rates may stay higher.",
            "source": "TestWire",
            "url": "https://example.test/fed-101?tracking=secretless",
            "datetime": release,
            "category": "forex",
            "related": "EURUSD,USDJPY",
        }],
    )
    state: dict = {}
    report = refresh_and_persist_finnhub_sentiment(
        state, daily_snapshot_id=snapshot_id, selected_symbols=["EURUSD", "USDJPY"], path=db
    )
    assert report["ok"] is True
    assert report["provider"] == "FINNHUB"
    assert report["secret_persisted"] is False
    frame = load_finnhub_sentiment_rank(daily_snapshot_id=snapshot_id, path=db)
    assert set(frame["Data Provider"]) == {"FINNHUB"}
    assert set(frame["Provider Authentication"]) == {"FINNHUB_AUTHENTICATED_API"}
    eurusd = frame.loc[frame["Symbol"] == "EURUSD"].iloc[0]
    usdjpy = frame.loc[frame["Symbol"] == "USDJPY"].iloc[0]
    assert eurusd["Affected Currency"] == "USD"
    assert eurusd["Pair Direction Effect"] == "SELL"  # positive quote currency
    assert usdjpy["Pair Direction Effect"] == "BUY"   # positive base currency
    assert eurusd["Event Age Minutes"] >= 0
    assert 0 <= eurusd["Impact Remaining Percentage"] <= 100
    assert 0 <= eurusd["Absorption Percentage"] <= 100
    assert eurusd["Actual Value"] == "UNAVAILABLE"
    assert eurusd["Consensus Value"] == "UNAVAILABLE"


def test_finnhub_migration_is_idempotent_and_has_no_secret_columns(tmp_path: Path) -> None:
    from core.field10_finnhub_sentiment_20260704 import migrate_finnhub_sentiment_database
    from core.field10_unified_migration_20260703 import migrate_and_verify_field10

    db = tmp_path / "field10.sqlite3"
    _prepare_snapshot(db)
    assert migrate_finnhub_sentiment_database(db)["ok"]
    assert migrate_finnhub_sentiment_database(db)["ok"]
    report = migrate_and_verify_field10(db)
    assert report["ok"]
    assert report["finnhub_news_schema_verified"] is True
    assert report["prohibited_rank_tables"] == []
    assert report["secret_column_issues"] == {}
    with sqlite3.connect(db) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "field10_daily_news_event_rank" in tables
        assert "field10_news_event_outcome" in tables
        columns = {row[1].lower() for row in conn.execute("PRAGMA table_info(field10_daily_news_event_rank)")}
    assert not any(token in column for column in columns for token in ("api_key", "password", "secret", "credential", "access_token"))


def test_absorption_fallback_is_bounded_and_monotonic() -> None:
    from core.field10_finnhub_sentiment_20260704 import _absorption

    early = _absorption(10.0, 120.0)
    late = _absorption(240.0, 120.0)
    assert 0 <= early[0] <= 100 and 0 <= early[1] <= 100
    assert 0 <= late[0] <= 100 and 0 <= late[1] <= 100
    assert late[0] < early[0]
    assert late[1] > early[1]


def test_field10_ui_contains_closed_finnhub_sentiment_expander() -> None:
    source = (Path(__file__).resolve().parents[1] / "ui" / "lunch_field10_multi_symbol_20260701.py").read_text()
    assert "Open / Close — Multi-Symbol Sentiment, High-Impact News and Absorption Rank" in source
    assert "load_finnhub_sentiment_rank" in source
    assert "fetch_market_news" not in source
