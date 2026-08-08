from __future__ import annotations

import numpy as np
import pandas as pd

from core.field10_integrated_evidence_20260702 import prepare_evidence_alignment_heatmap


def test_field10_evidence_heatmap_copy_missing_and_rank_order():
    source = pd.DataFrame({
        "Rank": [2, 1], "Symbol": ["GBPJPY", "USDJPY"],
        "Technical Bias": [None, "BUY"], "Sentiment Bias": ["SELL", "WAIT"],
        "Session Bias": ["BUY", "SELL"], "Regime Bias": ["WAIT", "BUY"],
        "Existing Combined Evidence Bias": ["SELL", "BUY"],
        "Evidence Agreement Percentage": [75.0, 0.8], "Calibrated Reliability": [0.7, 90.0],
        "Data Quality Grade": ["B", "A"], "Transition Risk 3H": [0.4, 25.0],
        "Broker Timestamp": ["2026-07-01T10:00:00Z", "2026-07-01T10:00:00Z"],
        "Canonical Run ID": ["R2", "R1"], "Source ID": ["S2", "S1"], "Explanation": ["e2", "e1"],
    })
    before = source.copy(deep=True)
    data, hover = prepare_evidence_alignment_heatmap(source)
    pd.testing.assert_frame_equal(source, before)
    assert list(data.index) == ["USDJPY", "GBPJPY"]
    assert data.loc["USDJPY", "Technical Evidence"] == 1.0
    assert np.isnan(data.loc["GBPJPY", "Technical Evidence"])
    assert data.loc["GBPJPY", "Sentiment Evidence"] == -1.0
    assert data.loc["USDJPY", "Sentiment Evidence"] == 0.0
    assert data.loc["USDJPY", "Transition Safety"] == 0.75
    assert "Canonical Run ID=R1" in hover.loc["USDJPY", "Technical Evidence"]
