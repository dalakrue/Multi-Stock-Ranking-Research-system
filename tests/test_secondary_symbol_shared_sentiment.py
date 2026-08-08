from __future__ import annotations

import pandas as pd

from core.field10_integrated_evidence_20260702 import _shared_news_projection


def test_secondary_symbol_shared_sentiment_is_labelled_projection():
    state = {"nlp_ranked_news_df": pd.DataFrame({
        "Headline": ["Bank of Japan and yen policy outlook", "ECB euro decision"],
        "Sentiment": ["SELL", "BUY"],
        "Published At": ["2026-07-01T09:00:00Z", "2026-07-01T08:00:00Z"],
    })}
    result = _shared_news_projection(state, "GBPJPY")
    assert result["bias"] == "SELL"
    assert result["source"] == "SHARED_NEWS_SYMBOL_PROJECTION"
    assert "JPY" in result["entity_match"] or "YEN" in result["entity_match"]


def test_insufficient_shared_news_remains_unavailable_not_wait():
    state = {"nlp_ranked_news_df": pd.DataFrame({"Headline": ["Unrelated local story"], "Sentiment": ["WAIT"]})}
    result = _shared_news_projection(state, "US500")
    assert result["bias"] is None
    assert result["source"] == "UNAVAILABLE"
