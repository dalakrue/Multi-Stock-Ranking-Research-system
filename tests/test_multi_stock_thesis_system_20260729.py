from __future__ import annotations

import pandas as pd


def _state() -> dict:
    ranking = pd.DataFrame(
        [
            {
                "Rank": 1,
                "Symbol": "EURUSD",
                "Timeframe": "H1",
                "Entry permission": "WAIT",
                "Final daily less-risky bias": "BUY",
                "Regime probability": 0.68,
                "Probability of reaching expected value 6H": 0.62,
                "Net Expected Value": 0.05,
                "Volatility forecast 6H": 0.20,
                "Conformal interval width": 0.08,
                "Calibration score": 0.70,
                "Rank confidence": 0.64,
                "Rank stability": 0.61,
                "Transition Risk 6H": 0.35,
                "CVaR / drawdown-risk estimate": 0.15,
                "Spread/slippage cost if available": 0.01,
                "InstitutionalUtility": 0.44,
                "Data quality grade": "A_INSTITUTIONAL_READY",
                "Candle count": 600,
                "Coverage ratio": 1.0,
                "Provider used": "TEST",
                "News Relevance Score": 0.8,
                "News Absorption Score": 0.8,
                "News Conflict Flag": False,
                "Broker Candle Time": "2026-07-29T12:00:00Z",
                "Parent Run ID": "RUN-29",
                "Generation": "G1",
                "Snapshot Hash": "SNAP-29",
            },
            {
                "Rank": 2,
                "Symbol": "AUDUSD",
                "Timeframe": "H1",
                "Entry permission": "TRADE CANDIDATE",
                "Final daily less-risky bias": "BUY",
                "Regime probability": 0.72,
                "Probability of reaching expected value 6H": 0.66,
                "Net Expected Value": 0.07,
                "Volatility forecast 6H": 0.18,
                "Conformal interval width": 0.06,
                "Calibration score": 0.78,
                "Rank confidence": 0.71,
                "Rank stability": 0.69,
                "Transition Risk 6H": 0.28,
                "CVaR / drawdown-risk estimate": 0.12,
                "Spread/slippage cost if available": 0.01,
                "InstitutionalUtility": 0.52,
                "Data quality grade": "A_INSTITUTIONAL_READY",
                "Candle count": 600,
                "Coverage ratio": 1.0,
                "Provider used": "TEST",
                "News Relevance Score": 0.9,
                "News Absorption Score": 0.9,
                "News Conflict Flag": False,
                "Broker Candle Time": "2026-07-29T12:00:00Z",
                "Parent Run ID": "RUN-29",
                "Generation": "G1",
                "Snapshot Hash": "SNAP-29",
            },
        ]
    )
    field11 = pd.DataFrame(
        [
            {"Symbol": "EURUSD", "Horizon": "6H", "MFE": 0.22, "MAE": -0.11, "Reliability": 0.60},
            {"Symbol": "AUDUSD", "Horizon": "6H", "MFE": 0.25, "MAE": -0.09, "Reliability": 0.70},
        ]
    )
    field12 = pd.DataFrame(
        [
            {
                "Fundamental Rank": 2,
                "Symbol": "EURUSD",
                "Fundamental Bias": "WAIT",
                "News Permission": "WAIT_NEWS_NOT_STRONG_ENOUGH",
                "News Relevance Score": 0.8,
                "News Freshness Minutes": 60,
                "News Absorption Score": 0.8,
                "News Conflict Flag": False,
                "News Sentiment": "NEUTRAL",
                "Latest High-Impact Symbol News": "ECB policy outlook remains mixed",
                "Evidence Status": "RECENT_SYMBOL_NEWS_READY",
            },
            {
                "Fundamental Rank": 1,
                "Symbol": "AUDUSD",
                "Fundamental Bias": "BUY",
                "News Permission": "FUNDAMENTAL_NEWS_CANDIDATE",
                "News Relevance Score": 0.9,
                "News Freshness Minutes": 30,
                "News Absorption Score": 0.9,
                "News Conflict Flag": False,
                "News Sentiment": "POSITIVE",
                "Latest High-Impact Symbol News": "Australia inflation surprise lifts rate expectations",
                "Evidence Status": "RECENT_SYMBOL_NEWS_READY",
            },
        ]
    )
    return {
        "canonical_display_symbol_20260709": "AUDUSD",
        "canonical_run_identity_20260708": {
            "parent_run_id": "RUN-29",
            "generation": "G1",
            "snapshot_hash": "SNAP-29",
            "broker_candle_time": "2026-07-29T12:00:00Z",
            "timeframe": "H1",
            "canonical_symbols": ["EURUSD", "AUDUSD"],
        },
        "field10_institutional_ranking_20260708": ranking,
        "field11_similar_path_multisymbol_20260708": field11,
        "field12_fundamental_nlp_rank_20260722": field12,
    }


def test_master_ranking_preserves_production_and_adds_formula() -> None:
    from core.multi_stock_thesis_research_20260729 import build_master_ranking

    master, meta = build_master_ranking(_state())
    assert meta["status"] == "READY"
    assert list(master.sort_values("Production Rank")["Production Rank"]) == [1, 2]
    assert "Research Rank" in master
    assert "Thesis Expected Net Value" in master
    assert master["Thesis Expected Net Value"].notna().all()
    aud = master.loc[master["Symbol"].eq("AUDUSD")].iloc[0]
    assert aud["Trade Permission"] == "TRADE CANDIDATE"
    assert aud["Can Trust Rank"] == "YES"
    assert aud["Expected Net Value Source"] == "MFE/MAE TARGET-PROBABILITY FORMULA"


def test_nlp_and_analysis_are_multi_symbol() -> None:
    from core.multi_stock_thesis_research_20260729 import (
        build_data_analysis_tables,
        build_master_ranking,
        build_nlp_tables,
        resolve_research_sources,
    )

    state = _state()
    master, _ = build_master_ranking(state)
    analysis = build_data_analysis_tables(master)
    nlp = build_nlp_tables(master, resolve_research_sources(state)["news"])
    assert len(analysis["descriptive"]) > 0
    assert set(nlp["symbols"]["Symbol"]) == {"EURUSD", "AUDUSD"}
    assert not nlp["bigrams"].empty


def test_ai_answers_comparison_and_best_entry_from_saved_evidence() -> None:
    from core.ai_canonical_intents_v10 import _parse, answer_canonical_question

    state = _state()
    best = answer_canonical_question("What stock is best to entry now?", state)
    comparison = answer_canonical_question("Compare EURUSD vs AUDUSD", state)
    why = answer_canonical_question("Why is AUDUSD rank 2?", state)
    assert best["intent"] == "best_symbol"
    assert "AUDUSD" in best["answer"]
    assert comparison["intent"] == "compare_symbols"
    assert "EURUSD" in comparison["answer"] and "AUDUSD" in comparison["answer"]
    assert why["intent"] == "why_rank"
    assert "Permission" in why["answer"]
    assert _parse("Compare AAPL vs MSFT").symbols == ("AAPL", "MSFT")
    assert _parse("Compare EUR/USD vs DXY").symbols == ("EURUSD", "DXY")


def test_legacy_navigation_routes_into_one_visible_page() -> None:
    from core.navigation_state_20260627 import UNIFIED_PAGE, navigate_now

    state: dict = {}
    assert navigate_now(state, "Settings") == UNIFIED_PAGE
    assert state["multi_stock_research_workspace"] == "System Controls & Run"
    assert navigate_now(state, "AI Assistant") == UNIFIED_PAGE
    assert state["multi_stock_research_workspace"] == "Multi-Stock Ranking AI Assistant"
    assert navigate_now(state, "Lunch") == UNIFIED_PAGE
    assert state["multi_stock_research_workspace"] == "Ranking Command Center"


def test_three_selectors_build_a_30_symbol_universe_with_dxy() -> None:
    import sys
    import types

    try:
        import requests  # noqa: F401
    except ModuleNotFoundError:
        requests_stub = types.ModuleType("requests")
        requests_stub.Session = type("Session", (), {})
        requests_stub.Timeout = type("Timeout", (Exception,), {})
        requests_stub.RequestException = type("RequestException", (Exception,), {})
        sys.modules["requests"] = requests_stub

    from core.data.market_data_orchestrator import MarketDataOrchestrator
    from core.field10_research_common_20260705 import MAX_SYMBOL_UNIVERSE
    from core.multi_symbol_load_manager_20260707 import (
        MAX_CANONICAL_SYMBOLS,
        canonical_universe_from_groups,
        group_symbol_limit,
    )
    from core.multi_symbol_run_groups_20260706 import DEFAULT_GROUPS

    universe = canonical_universe_from_groups(DEFAULT_GROUPS)
    assert group_symbol_limit("FIRST") == 10
    assert group_symbol_limit("SECOND") == 10
    assert group_symbol_limit("THIRD") == 10
    assert MAX_CANONICAL_SYMBOLS == 30
    assert MAX_SYMBOL_UNIVERSE == 30
    assert len(universe) == 30
    assert "DXY" in universe
    assert MarketDataOrchestrator.provider_symbol("DXY", "TWELVE_DATA_KEY_POOL") == "DXY"


def test_load_all_runs_the_third_cache_first_provider_worker() -> None:
    import core.multi_symbol_load_manager_20260707 as loader
    from core.multi_symbol_run_groups_20260706 import DEFAULT_GROUPS

    calls: list[tuple[str, list[str]]] = []
    original_assigned = loader.load_selector_with_assigned_key
    original_group = loader.load_group_market_data
    original_merge = loader.merge_selector_load_results
    try:
        loader.load_selector_with_assigned_key = (
            lambda state, selector_id, symbols, timeframe, key_name, **kwargs:
            calls.append((str(selector_id), list(symbols))) or {"status": "READY"}
        )
        loader.load_group_market_data = (
            lambda state, group, symbols, timeframe, **kwargs:
            calls.append((str(group), list(symbols))) or {"status": "READY"}
        )
        loader.merge_selector_load_results = (
            lambda state, configured, timeframe: {"status": "READY", "loaded_symbols": []}
        )
        loader.load_all_selectors_safely({}, DEFAULT_GROUPS, "H1")
    finally:
        loader.load_selector_with_assigned_key = original_assigned
        loader.load_group_market_data = original_group
        loader.merge_selector_load_results = original_merge

    assert [name for name, _ in calls] == ["FIRST", "SECOND", "THIRD"]
    assert all(len(symbols) == 10 for _, symbols in calls)
    assert "DXY" in calls[2][1]
