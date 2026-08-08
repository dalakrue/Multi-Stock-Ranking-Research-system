# ADX Quant Pro — Institutional Quant Upgrade 20260708

## Main architecture added

A new additive canonical institutional layer has been added. It does not remove or rename existing Field 10, Field 3, ML, history, export, copy-button, tab, or UI logic.

The new run-gated publisher is:

- `core.institutional_quant_layer_20260708.publish_institutional_quant_run(...)`

It reads the canonical loaded universe from Settings state, deduplicates it in selector order, caps it at 12 symbols, and publishes one saved evidence store for all tabs:

- `field10_institutional_ranking_20260708`
- `field10_news_nlp_evidence_20260708`
- `field10_rank_explanation_20260708`
- `field10_model_scores_20260708`
- `field3_multisymbol_regime_20260708`
- `field1_canonical_multisymbol_summary_20260708`
- `field2_canonical_projection_20260708`
- `field11_similar_path_multisymbol_20260708`
- `research_model_validation_20260708`
- `canonical_run_identity_20260708`
- `data_visualization_canonical_20260708`

Every saved table carries the same parent run id, generation, snapshot hash, timeframe, broker candle time where available, and canonical symbol universe.

## Loader route repair

The market-data route was repaired from the previous disabled-FCS route to:

1. Local validated cache first.
2. `FCS_API_MAIN` live candle provider when configured.
3. `TWELVE_DATA_KEY_POOL` fallback provider.
4. `LOCAL_VALID_CACHE` emergency last-known valid cache.

FCS is no longer normalized to `DISABLED_REMOVED_PROVIDER`. Finnhub is not used as the main candle route in this institutional path; it remains suitable for news/sentiment elsewhere.

## Field 10 institutional ranking

A new institutional ranking table is displayed above the old consolidated Field 10 table. Existing Field 10 surfaces remain available.

The institutional table includes:

- Rank, symbol, timeframe, provider, candle count, coverage, data quality grade.
- Higher-standard regime and bias.
- Transition risk 1H/3H/6H/12H/24H.
- Expected return 1H/6H/12H/24H/36H.
- Probability of reaching expected value 1H/6H/12H/24H.
- Volatility forecast 1H/6H/12H/24H.
- CVaR/drawdown risk, cost, NetEV, risk-adjusted EV, Wasserstein robust EV.
- Ledoit-Wolf/DCC-style correlation penalty, duplicate exposure penalty, Diebold-Yilmaz-style spillover risk.
- BOCPD-style changepoint risk, conformal interval width, calibration score.
- Brier, log score, CRPS.
- Rank confidence and rank stability.
- SHAP-style explanation.
- Top 4 highlight.
- Final daily less-risky bias and entry permission.
- Missing reason for unavailable/degraded data.
- Latest news title, currency/symbol match, sentiment, relevance, freshness, absorption, conflict flag, NLP source, and missing reason.

Ranking uses the requested institutional formula layer:

- `WeightedNetEV = 0.10*NetEV_1H + 0.20*NetEV_6H + 0.30*NetEV_12H + 0.25*NetEV_24H + 0.15*NetEV_36H`
- `RiskPenalty = 0.25*CVaR + 0.20*transition_risk_6H + 0.15*changepoint_risk + 0.10*conformal_width + 0.10*volatility_expansion + 0.10*correlation_duplicate + 0.05*data_quality + 0.05*spread_slippage`
- `InstitutionalUtility = WeightedNetEV * RobustEV_adjustment - RiskPenalty * CalibrationBonus * RankStabilityBonus * NewsAbsorptionBonus`

## Field 3 / Field 1 / Field 2 / Field 11

- Field 3 now receives a saved multi-symbol regime table with Lower/Middle/Higher standards for all canonical symbols.
- Field 1 receives a canonical multi-symbol latest-decision summary and loaded-symbol selector.
- Field 2 receives a canonical projection table with conformal bands, volatility-adjusted bands, and risk-adjusted central path by loaded symbol.
- Field 11 receives a canonical multi-symbol similar-path snapshot tied back to Field 10 ranks.

## Morning / Dinner / Research / AI-NLP / Data Visualization

- Morning shows top 4 canonical ranking rows and a daily action-plan summary.
- Dinner shows Field 10, Field 3, Field 11, and Research summaries with “why top 4” explanation.
- Research shows calculated validation tables: Brier, log score, CRPS, conformal coverage, SPA/MCS/White/PBO proxies, rank stability, duplicate exposure, changepoint, and data quality.
- AI/NLP shows saved news/NLP evidence by symbol and a copyable NLP summary without needing another run.
- Data Visualization now includes a canonical institutional snapshot view and charts for utility, expected return, transition risk, reliability, news absorption, and related metrics.

## Database migrations

Added idempotent migration:

- `core.institutional_quant_migration_20260708.migrate_institutional_quant_schema(...)`

Tables created/verified:

- `canonical_run_identity`
- `canonical_symbol_evidence`
- `field10_institutional_ranking`
- `field10_news_nlp_evidence`
- `field10_rank_explanation`
- `field10_model_scores`
- `field10_rank_history`
- `field3_multisymbol_regime`
- `field11_similar_path_multisymbol`
- `research_model_validation`
- `data_load_audit`

The migration repairs old `schema_migrations` tables that lack a `version` column by renaming the old table and creating the canonical versioned table. It never deletes user history.

## Screenshot-ready Super Quick Run summary

After loading symbols, clicking **Super Quick — Calculate All Loaded Symbols + Open Lunch** now publishes one canonical institutional snapshot. Field 10, Field 3, Field 1, Field 2, Field 11, Morning, Dinner, Research, AI/NLP, exports, and Data Visualization read the same saved parent_run_id, generation, snapshot_hash, timeframe, broker candle time, and canonical symbol universe. If a symbol is missing or degraded, it remains visible with explicit reason instead of disappearing or silently showing old active-symbol data.
