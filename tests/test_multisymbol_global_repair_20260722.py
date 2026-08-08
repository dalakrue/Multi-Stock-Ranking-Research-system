from __future__ import annotations

import pandas as pd


def test_persisted_h1_wins_over_fresh_session_h4_default() -> None:
    from core.runtime_selection_20260705 import SELECTION_PROFILE_VERSION, synchronize_runtime_selection

    state = {"timeframe": "H4", "symbol": "EURUSD"}
    persisted = {
        "selected_symbols": ["USDJPY", "AUDUSD"],
        "timeframe": "H1",
        "active_display_symbol": "AUDUSD",
        "selection_profile_version": SELECTION_PROFILE_VERSION,
    }
    result = synchronize_runtime_selection(state, persisted=persisted)
    assert result["timeframe"] == "H1"
    assert state["selected_timeframe"] == "H1"
    assert state["canonical_display_symbol_20260709"] == "AUDUSD"


def test_field12_ranks_only_news_and_blocks_missing_news() -> None:
    from core.field12_fundamental_nlp_20260722 import TABLE_KEY, build_field12_fundamental_rank

    state = {
        "canonical_loaded_symbols": ["USDJPY", "AUDUSD", "GBPUSD"],
        "canonical_run_identity_20260708": {
            "loaded_symbols": ["USDJPY", "AUDUSD", "GBPUSD"],
            "timeframe": "H1", "parent_run_id": "RUN-1", "snapshot_hash": "SNAP-1",
        },
        "field10_news_nlp_evidence_20260708": pd.DataFrame([
            {
                "Symbol": "AUDUSD", "Latest News Title": "Australia inflation surprise lifts rate expectations",
                "News Sentiment": "POSITIVE", "News Relevance Score": 0.95,
                "News Freshness Minutes": 30, "News Absorption Score": 0.8,
                "News Conflict Flag": False, "NLP Evidence Source": "TEST", "NLP Missing Reason": "",
            },
            {
                "Symbol": "USDJPY", "Latest News Title": "Japan policy outlook remains mixed",
                "News Sentiment": "NEUTRAL", "News Relevance Score": 0.60,
                "News Freshness Minutes": 900, "News Absorption Score": 0.4,
                "News Conflict Flag": True, "NLP Evidence Source": "TEST", "NLP Missing Reason": "",
            },
        ]),
    }
    report = build_field12_fundamental_rank(state)
    table = state[TABLE_KEY]
    assert report["ok"] is True
    assert table.iloc[0]["Symbol"] == "AUDUSD"
    assert table.iloc[0]["Fundamental Bias"] == "BUY"
    assert table.iloc[0]["Technical Influence"] == "NONE — NEWS/NLP ONLY"
    missing = table.loc[table["Symbol"].eq("GBPUSD")].iloc[0]
    assert missing["News Permission"] == "BLOCK_NO_RECENT_SYMBOL_NEWS"
    assert missing["Evidence Status"] == "NEWS_UNAVAILABLE"


def test_ai_best_symbol_uses_field10_not_field1() -> None:
    from core.ai_canonical_intents_v10 import ParsedQuestion, _answer

    contract = {
        "identity": {"run_id": "RUN-1"},
        "session": {"broker_candle_time": "2026-07-22T08:00:00Z"},
        "field10_multi_symbol_ranking": [
            {"Rank": 1, "Symbol": "EURUSD", "Entry permission": "WAIT", "Less-Risky Bias": "WAIT", "InstitutionalUtility": 0.9},
            {"Rank": 2, "Symbol": "AUDUSD", "Entry permission": "TRADE CANDIDATE", "Less-Risky Bias": "BUY", "InstitutionalUtility": 0.8},
        ],
        "field12_fundamental_news_ranking": [
            {"Symbol": "AUDUSD", "Fundamental Bias": "BUY", "News Permission": "FUNDAMENTAL_NEWS_CANDIDATE", "Latest High-Impact Symbol News": "Test headline"},
        ],
    }
    answer = _answer(ParsedQuestion(intent="best_symbol"), contract)
    assert "AUDUSD" in answer
    assert "Field 10" in answer
    assert "not Field 1" in answer
    assert "Field 12" in answer


def test_ai_contract_is_ready_from_field10_identity_without_field1() -> None:
    from core.ai_canonical_intents_v10 import answer_canonical_question

    state = {
        "canonical_loaded_symbols": ["AUDUSD", "USDJPY"],
        "canonical_display_symbol_20260709": "AUDUSD",
        "canonical_run_identity_20260708": {
            "parent_run_id": "IQ-RUN-22",
            "generation": "G7",
            "snapshot_hash": "SNAP-22",
            "broker_candle_time": "2026-07-22T08:00:00+00:00",
            "timeframe": "H1",
            "canonical_symbols": ["AUDUSD", "USDJPY"],
        },
        "field10_institutional_ranking_20260708": pd.DataFrame([
            {
                "Rank": 1,
                "Symbol": "AUDUSD",
                "Entry permission": "TRADE CANDIDATE",
                "Less-Risky Bias": "BUY",
                "InstitutionalUtility": 0.88,
            },
            {
                "Rank": 2,
                "Symbol": "USDJPY",
                "Entry permission": "WAIT",
                "Less-Risky Bias": "WAIT",
                "InstitutionalUtility": 0.71,
            },
        ]),
    }

    result = answer_canonical_question("What is the best symbol to enter now?", state)
    assert result["ready"] is True
    assert result["run_id"] == "IQ-RUN-22"
    assert result["missing_components"] == []
    assert "AUDUSD" in result["answer"]
    assert result["evidence"]["session"]["broker_candle_time"] == "2026-07-22T08:00:00+00:00"
