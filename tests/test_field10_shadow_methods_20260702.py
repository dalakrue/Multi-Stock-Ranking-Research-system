from __future__ import annotations

import numpy as np
import pandas as pd

from research_quant.field10_shadow_methods_20260702 import (
    deflated_sharpe_ratio,
    methodology_catalog,
    novelty_adjusted_news_sentiment,
    probability_of_backtest_overfitting,
    run_shadow_validation,
)


def test_catalog_contains_exactly_ten_governed_shadow_methods():
    catalog = methodology_catalog()
    assert len(catalog) == 10
    assert len({item["method_id"] for item in catalog}) == 10
    assert all(item["current_status"] in {"UNAVAILABLE", "SHADOW", "VALIDATED", "PRODUCTION APPROVED"} for item in catalog)
    assert all(item["production_promotion_criteria"] for item in catalog)


def test_normal_quick_run_never_executes_research_or_influences_production():
    result = run_shadow_validation(state={}, canonical={"symbol": "EURUSD", "timeframe": "H1"})
    assert result["status"] == "UNAVAILABLE"
    assert result["production_influence_enabled"] is False
    assert all(item["status"] == "UNAVAILABLE" for item in result["methods"].values())


def test_pbo_and_dsr_do_not_fabricate_when_samples_are_insufficient():
    assert probability_of_backtest_overfitting(pd.DataFrame()) ["status"] == "UNAVAILABLE"
    assert deflated_sharpe_ratio([0.1, -0.1], trial_sharpes=[0.1, 0.2])["status"] == "UNAVAILABLE"


def test_shadow_pbo_and_dsr_keep_protected_calculation_unchanged_with_sufficient_fixture():
    rng = np.random.default_rng(42)
    performance = pd.DataFrame(rng.normal(0.001, 0.01, size=(120, 8)))
    pbo = probability_of_backtest_overfitting(performance, blocks=8)
    returns = rng.normal(0.001, 0.01, size=180)
    trials = rng.normal(0.4, 0.1, size=20)
    dsr = deflated_sharpe_ratio(returns, trial_sharpes=trials)
    assert pbo["status"] == "SHADOW"
    assert dsr["status"] == "SHADOW"
    assert pbo["production_influence_enabled"] is False
    assert dsr["protected_calculation_changed"] is False


def test_news_sentiment_is_as_of_time_decayed_and_requires_prior_similarity():
    news = pd.DataFrame({
        "timestamp": pd.date_range("2026-07-01", periods=36, freq="h", tz="UTC"),
        "sentiment": np.linspace(-0.5, 0.8, 36),
        "relevance": np.linspace(0.6, 1.0, 36),
        "max_prior_similarity": np.linspace(0.1, 0.7, 36),
    })
    result = novelty_adjusted_news_sentiment(news, as_of="2026-07-03T00:00:00Z")
    assert result["status"] == "SHADOW"
    assert -1 <= result["news_sentiment_shadow"] <= 1
    assert result["production_influence_enabled"] is False
    unavailable = novelty_adjusted_news_sentiment(news.drop(columns=["max_prior_similarity"]), as_of="2026-07-03T00:00:00Z")
    assert unavailable["status"] == "UNAVAILABLE"
