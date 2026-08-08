"""Read-only thesis research adapter for the unified multi-stock workspace.

This module does not fetch market data, fit the production ranking model, or
change any existing trade decision.  It combines the already-published Field
3/10/11/12 and validation snapshots into research-only views that can be used
for a final-year project, master's thesis, PhD proposal, or technical interview.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import json
import math
import re
from typing import Any

import numpy as np
import pandas as pd


RANKING_SOURCE_KEYS = (
    "field10_institutional_ranking_20260708",
    "field10_consolidated_table_20260707",
    "field10_latest_complete_run_table_20260706",
    "field10_current_table_20260701",
)
FIELD3_SOURCE_KEYS = (
    "field3_multisymbol_regime_20260708",
    "field3_regime_age_ranking_20260701",
)
FIELD11_SOURCE_KEYS = (
    "field11_similar_path_multisymbol_20260708",
    "field11_similar_path_20260702",
)
NEWS_SOURCE_KEYS = (
    "field12_fundamental_nlp_rank_20260722",
    "field10_news_nlp_evidence_20260708",
)
VALIDATION_SOURCE_KEYS = (
    "research_model_validation_20260708",
    "field10_model_scores_20260708",
)

THESIS_VERSION = "multi-stock-thesis-research-v1-20260729"


def _frame(value: Any) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value.copy(deep=False)
    if isinstance(value, list):
        try:
            return pd.DataFrame.from_records(value)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def _first_frame(state: Mapping[str, Any], keys: tuple[str, ...]) -> tuple[pd.DataFrame, str]:
    for key in keys:
        value = _frame(state.get(key))
        if not value.empty:
            return value.copy(), key
    return pd.DataFrame(), ""


def _norm_symbol(value: Any) -> str:
    return str(value or "").strip().upper().replace("/", "").replace("_", "").replace(" ", "")


def _numeric(series: Any, index: pd.Index, default: float = np.nan) -> pd.Series:
    if isinstance(series, pd.Series):
        return pd.to_numeric(series, errors="coerce")
    return pd.Series(default, index=index, dtype=float)


def _coalesce(frame: pd.DataFrame, names: tuple[str, ...], default: Any = np.nan) -> pd.Series:
    result = pd.Series(np.nan, index=frame.index, dtype=object)
    for name in names:
        if name not in frame.columns:
            continue
        values = frame[name]
        if pd.api.types.is_object_dtype(values) or pd.api.types.is_string_dtype(values):
            valid = values.notna() & values.astype(str).str.strip().ne("") & values.astype(str).str.upper().ne("UNAVAILABLE")
        else:
            valid = values.notna()
        result = result.where(result.notna() & result.astype(str).ne(""), values.where(valid))
    if not (isinstance(default, float) and math.isnan(default)):
        result.loc[result.isna()] = default
    return result


def _bool_series(series: Any, index: pd.Index) -> pd.Series:
    if not isinstance(series, pd.Series):
        return pd.Series(False, index=index)
    text = series.astype(str).str.strip().str.upper()
    return text.isin({"TRUE", "YES", "1", "CONFLICT", "HIGH", "BLOCK", "BLOCKED"}) | text.str.contains(
        "CONFLICT", regex=False
    )


def resolve_research_sources(state: Mapping[str, Any]) -> dict[str, Any]:
    ranking, ranking_key = _first_frame(state, RANKING_SOURCE_KEYS)
    field3, field3_key = _first_frame(state, FIELD3_SOURCE_KEYS)
    field11, field11_key = _first_frame(state, FIELD11_SOURCE_KEYS)
    news, news_key = _first_frame(state, NEWS_SOURCE_KEYS)
    validation, validation_key = _first_frame(state, VALIDATION_SOURCE_KEYS)
    identity = state.get("canonical_run_identity_20260708")
    identity = dict(identity) if isinstance(identity, Mapping) else {}
    return {
        "ranking": ranking,
        "field3": field3,
        "field11": field11,
        "news": news,
        "validation": validation,
        "identity": identity,
        "source_keys": {
            "ranking": ranking_key,
            "field3": field3_key,
            "field11": field11_key,
            "news": news_key,
            "validation": validation_key,
        },
    }


def _collapse_field3(field3: pd.DataFrame) -> pd.DataFrame:
    if field3.empty or "Symbol" not in field3.columns:
        return pd.DataFrame()
    work = field3.copy()
    work["Symbol"] = work["Symbol"].map(_norm_symbol)
    if "Standard" not in work.columns:
        keep = [c for c in work.columns if c != "Symbol"]
        return work.drop_duplicates("Symbol", keep="first")[["Symbol", *keep]]
    rows: list[dict[str, Any]] = []
    for symbol, group in work.groupby("Symbol", sort=False):
        row: dict[str, Any] = {"Symbol": symbol}
        for standard in ("Lower", "Middle", "Higher"):
            match = group[group["Standard"].astype(str).str.upper().eq(standard.upper())]
            if match.empty:
                continue
            item = match.iloc[0]
            for source, suffix in (
                ("Bias", "Regime Bias"),
                ("Regime", "Regime"),
                ("Regime age", "Regime Age"),
                ("Reliability", "Reliability"),
                ("Switch probability 6H", "Switch Probability 6H"),
            ):
                if source in match.columns:
                    row[f"{standard} {suffix}"] = item.get(source)
        rows.append(row)
    return pd.DataFrame(rows)


def _collapse_field11(field11: pd.DataFrame) -> pd.DataFrame:
    if field11.empty or "Symbol" not in field11.columns:
        return pd.DataFrame()
    work = field11.copy()
    work["Symbol"] = work["Symbol"].map(_norm_symbol)
    if "Horizon" in work.columns:
        preferred = work[work["Horizon"].astype(str).str.upper().isin({"6H", "H6", "6"})]
        if not preferred.empty:
            work = preferred
    work = work.drop_duplicates("Symbol", keep="first")
    rename = {
        "MFE": "Similar Path MFE",
        "MAE": "Similar Path MAE",
        "Reliability": "Similar Path Reliability",
        "Similar path count": "Similar Path Count",
        "Effective sample size": "Similar Path Effective Sample Size",
        "Drift/changepoint warning": "Similar Path Drift Warning",
    }
    keep = ["Symbol", *[c for c in rename if c in work.columns]]
    return work[keep].rename(columns=rename)


def _collapse_news(news: pd.DataFrame) -> pd.DataFrame:
    if news.empty or "Symbol" not in news.columns:
        return pd.DataFrame()
    work = news.copy()
    work["Symbol"] = work["Symbol"].map(_norm_symbol)
    rank_col = next((c for c in ("Fundamental Rank", "Rank", "Priority Rank") if c in work.columns), None)
    if rank_col:
        work["__rank"] = pd.to_numeric(work[rank_col], errors="coerce")
        work = work.sort_values("__rank", kind="mergesort")
    return work.drop_duplicates("Symbol", keep="first").drop(columns=["__rank"], errors="ignore")


def _merge_without_collisions(left: pd.DataFrame, right: pd.DataFrame, prefix: str) -> pd.DataFrame:
    if right.empty or "Symbol" not in right.columns:
        return left
    rename = {c: f"{prefix}{c}" for c in right.columns if c != "Symbol" and c in left.columns}
    return left.merge(right.rename(columns=rename), on="Symbol", how="left", validate="one_to_one")


def _quality_tier(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text.startswith(("A", "B")):
        return "READY"
    if text.startswith("C"):
        return "CAUTION"
    return "NOT_READY"


def _reason_for_row(row: pd.Series) -> str:
    permission = str(row.get("Trade Permission") or "").strip().upper()
    trust = str(row.get("Can Trust Rank") or "").strip().upper()
    if permission == "TRADE CANDIDATE" and trust == "YES":
        return ""
    reasons: list[str] = []
    existing = str(row.get("Missing reason") or "").strip()
    if existing and existing.upper() not in {"NAN", "NONE", "UNAVAILABLE"}:
        reasons.append(existing)
    if _quality_tier(row.get("Data Quality")) == "NOT_READY":
        reasons.append("DATA_QUALITY_NOT_READY")
    if pd.notna(row.get("Rank Confidence")) and float(row.get("Rank Confidence")) < 0.55:
        reasons.append("LOW_RANK_CONFIDENCE")
    if pd.notna(row.get("Rank Stability")) and float(row.get("Rank Stability")) < 0.45:
        reasons.append("RANK_NOT_STABLE")
    if pd.notna(row.get("Transition Risk")) and float(row.get("Transition Risk")) > 0.62:
        reasons.append("HIGH_REGIME_TRANSITION_RISK")
    if pd.notna(row.get("Calibration")) and float(row.get("Calibration")) < 0.50:
        reasons.append("LOW_PROBABILITY_CALIBRATION")
    if bool(row.get("News Conflict")):
        reasons.append("NEWS_TECHNICAL_CONFLICT")
    if trust == "CAUTION":
        reasons.append("RESEARCH_CAUTION")
    if not reasons and permission != "TRADE CANDIDATE":
        reasons.append(permission or "WAIT_FOR_STRONGER_EVIDENCE")
    return " | ".join(dict.fromkeys(reasons))


def build_master_ranking(state: Mapping[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create a transparent research rank while preserving production ``Rank``."""
    sources = resolve_research_sources(state)
    ranking = sources["ranking"].copy()
    if ranking.empty or "Symbol" not in ranking.columns:
        return pd.DataFrame(), {
            "status": "NOT_READY",
            "reason": "NO_PUBLISHED_MULTI_SYMBOL_RANKING",
            "source_keys": sources["source_keys"],
            "identity": sources["identity"],
        }

    ranking["Symbol"] = ranking["Symbol"].map(_norm_symbol)
    ranking = ranking[ranking["Symbol"].ne("")].drop_duplicates("Symbol", keep="first").reset_index(drop=True)
    rank = pd.to_numeric(_coalesce(ranking, ("Rank", "Research Rank", "Priority Rank")), errors="coerce")
    if rank.isna().all():
        rank = pd.Series(np.arange(1, len(ranking) + 1), index=ranking.index, dtype=float)
    ranking["Production Rank"] = rank

    master = _merge_without_collisions(ranking, _collapse_field3(sources["field3"]), "Field 3 ")
    master = _merge_without_collisions(master, _collapse_field11(sources["field11"]), "Field 11 ")
    master = _merge_without_collisions(master, _collapse_news(sources["news"]), "News ")
    idx = master.index

    master["Direction Bias"] = _coalesce(
        master,
        (
            "Final daily less-risky bias",
            "Less-Risky Bias",
            "Higher-Standard Bias",
            "Higher Regime Bias",
            "Field 3 Higher Regime Bias",
        ),
        "WAIT",
    ).fillna("WAIT")
    master["Probability Direction"] = _numeric(
        _coalesce(master, ("Regime probability", "Probability Direction", "Higher Regime Probability")),
        idx,
    )
    master["Probability Target"] = _numeric(
        _coalesce(
            master,
            (
                "Probability of reaching expected value 6H",
                "Probability of reaching expected value 1H",
                "Probability Target",
            ),
        ),
        idx,
    )
    master["Published Expected Net Value"] = _numeric(
        _coalesce(master, ("Net Expected Value", "WeightedNetEV", "Expected Net Value")),
        idx,
    )
    master["Uncertainty"] = _numeric(
        _coalesce(master, ("Conformal interval width", "Uncertainty", "Prediction Interval Width")),
        idx,
    )
    master["Event Relevance"] = _numeric(
        _coalesce(master, ("News Relevance Score", "News News Relevance Score")),
        idx,
        0.0,
    ).fillna(0.0)
    master["News Absorption"] = _numeric(
        _coalesce(master, ("News Absorption Score", "News News Absorption Score")),
        idx,
        1.0,
    ).fillna(1.0)
    master["News Conflict"] = _bool_series(
        _coalesce(master, ("News Conflict Flag", "News News Conflict Flag"), False),
        idx,
    )
    master["Event Risk"] = (
        master["Event Relevance"].clip(0, 1)
        * (1.0 - master["News Absorption"].clip(0, 1))
        * master["News Conflict"].map({True: 1.0, False: 0.25})
    )
    master["Data Quality"] = _coalesce(
        master,
        ("Data quality grade", "Data Quality", "Research Data Quality"),
        "F_MISSING",
    ).fillna("F_MISSING")
    master["Rank Confidence"] = _numeric(
        _coalesce(master, ("Rank confidence", "Rank Confidence", "Research Reliability")),
        idx,
    )
    master["Rank Stability"] = _numeric(
        _coalesce(master, ("Rank stability", "Rank Stability", "Rank stability report")),
        idx,
    )
    master["Transition Risk"] = _numeric(
        _coalesce(master, ("Transition Risk 6H", "Research Transition Risk 6H", "Field 3 Higher Switch Probability 6H")),
        idx,
    )
    master["Calibration"] = _numeric(
        _coalesce(master, ("Calibration score", "Calibrated Reliability", "Calibration")),
        idx,
    )
    master["CVaR"] = _numeric(
        _coalesce(master, ("CVaR / drawdown-risk estimate", "CVaR 95", "Expected Shortfall")),
        idx,
    )
    master["Volatility"] = _numeric(
        _coalesce(master, ("Volatility forecast 6H", "Volatility forecast 1H", "ATR")),
        idx,
    )
    master["Transaction Cost"] = _numeric(
        _coalesce(master, ("Spread/slippage cost if available", "Transaction Cost", "Spread Cost")),
        idx,
        0.0,
    ).fillna(0.0)
    master["MFE"] = _numeric(
        _coalesce(master, ("Similar Path MFE", "Field 11 Similar Path MFE", "Expected MFE", "MFE")),
        idx,
    )
    master["MAE"] = _numeric(
        _coalesce(master, ("Similar Path MAE", "Field 11 Similar Path MAE", "Expected MAE", "MAE")),
        idx,
    ).abs()
    master["Uncertainty Penalty"] = (
        master["Uncertainty"].clip(lower=0)
        * (1.0 - master["Calibration"].clip(0, 1).fillna(0.0))
    )
    volatility_scale = master["Volatility"].abs().replace(0, np.nan)
    master["Event Penalty"] = master["Event Risk"] * volatility_scale.fillna(0.0)
    formula_ready = master[["Probability Target", "MFE", "MAE"]].notna().all(axis=1)
    p = master["Probability Target"].clip(0, 1)
    thesis_ev = (
        p * master["MFE"]
        - (1.0 - p) * master["MAE"]
        - master["Transaction Cost"]
        - master["Event Penalty"]
        - master["Uncertainty Penalty"]
    )
    master["Thesis Expected Net Value"] = thesis_ev.where(formula_ready)
    master["Expected Net Value"] = master["Thesis Expected Net Value"].where(
        master["Thesis Expected Net Value"].notna(),
        master["Published Expected Net Value"],
    )
    master["Expected Net Value Source"] = np.where(
        formula_ready,
        "MFE/MAE TARGET-PROBABILITY FORMULA",
        "PUBLISHED FIELD 10 NET EV",
    )
    master["Risk-Normalized Net Value"] = master["Expected Net Value"] / volatility_scale
    master["Research Score"] = master["Risk-Normalized Net Value"].replace([np.inf, -np.inf], np.nan)
    existing_utility = _numeric(_coalesce(master, ("InstitutionalUtility", "Authority Score")), idx)
    master["Research Score"] = master["Research Score"].where(master["Research Score"].notna(), existing_utility)
    master["Research Score Source"] = np.where(
        master["Risk-Normalized Net Value"].notna(),
        "RISK-NORMALIZED EXPECTED NET VALUE",
        "PUBLISHED INSTITUTIONAL UTILITY",
    )
    master["Trade Permission"] = _coalesce(
        master,
        ("Entry permission", "Trade Permission", "Research Entry Permission"),
        "WAIT",
    ).fillna("WAIT")

    evidence_columns = [
        "Probability Direction",
        "Probability Target",
        "Expected Net Value",
        "Uncertainty",
        "Data Quality",
        "Rank Confidence",
        "Rank Stability",
        "Transition Risk",
        "Calibration",
        "CVaR",
        "Volatility",
    ]
    completeness = master[evidence_columns].notna().mean(axis=1)
    master["Evidence Completeness %"] = (completeness * 100.0).round(1)
    quality = master["Data Quality"].map(_quality_tier)
    hard_fail = quality.eq("NOT_READY") | master["Trade Permission"].astype(str).str.upper().isin({"BLOCKED", "DATA DEGRADED"})
    thresholds_ready = (
        master["Rank Confidence"].ge(0.55)
        & master["Rank Stability"].ge(0.45)
        & master["Transition Risk"].le(0.62)
        & master["Calibration"].ge(0.50)
        & ~master["News Conflict"]
        & completeness.ge(0.70)
    )
    master["Can Trust Rank"] = np.select(
        [hard_fail, thresholds_ready & quality.eq("READY")],
        ["NO", "YES"],
        default="CAUTION",
    )
    trust_tier = master["Can Trust Rank"].map({"YES": 2, "CAUTION": 1, "NO": 0}).fillna(0)
    order = (
        pd.DataFrame(
            {
                "__index": master.index,
                "__trust": trust_tier,
                "__score": master["Research Score"].fillna(-np.inf),
                "__production": master["Production Rank"].fillna(np.inf),
            }
        )
        .sort_values(["__trust", "__score", "__production"], ascending=[False, False, True], kind="mergesort")
        .reset_index(drop=True)
    )
    research_rank = pd.Series(np.arange(1, len(order) + 1), index=order["__index"].astype(int))
    master["Research Rank"] = research_rank.reindex(master.index).astype("Int64")
    master["No-Trade Reason"] = master.apply(_reason_for_row, axis=1)

    ordered = [
        "Research Rank",
        "Production Rank",
        "Symbol",
        "Direction Bias",
        "Probability Direction",
        "Probability Target",
        "Expected Net Value",
        "Expected Net Value Source",
        "Risk-Normalized Net Value",
        "Uncertainty",
        "Event Risk",
        "Data Quality",
        "Can Trust Rank",
        "Trade Permission",
        "No-Trade Reason",
        "Rank Confidence",
        "Rank Stability",
        "Transition Risk",
        "Calibration",
        "CVaR",
        "Volatility",
        "Research Score",
        "Research Score Source",
        "Evidence Completeness %",
    ]
    master = master.sort_values("Research Rank", kind="mergesort").reset_index(drop=True)
    master = master[[c for c in ordered if c in master.columns] + [c for c in master.columns if c not in ordered]]
    identity = sources["identity"]
    meta = {
        "status": "READY",
        "version": THESIS_VERSION,
        "rows": int(len(master)),
        "symbols": master["Symbol"].tolist(),
        "timeframe": str(identity.get("timeframe") or _coalesce(master, ("Timeframe",), "UNKNOWN").iloc[0]),
        "run_id": str(identity.get("parent_run_id") or _coalesce(master, ("Parent Run ID",), "").iloc[0]),
        "generation": str(identity.get("generation") or _coalesce(master, ("Generation",), "").iloc[0]),
        "snapshot_hash": str(identity.get("snapshot_hash") or _coalesce(master, ("Snapshot Hash",), "").iloc[0]),
        "broker_candle_time": str(identity.get("broker_candle_time") or _coalesce(master, ("Broker Candle Time",), "").iloc[0]),
        "source_keys": sources["source_keys"],
        "production_rank_preserved": True,
        "research_rank_is_shadow_only": True,
        "formula": (
            "p_target*MFE - (1-p_target)*abs(MAE) - transaction_cost "
            "- event_penalty - uncertainty_penalty"
        ),
    }
    return master, meta


def build_data_analysis_tables(master: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if master.empty:
        empty = pd.DataFrame()
        return {"descriptive": empty, "groups": empty, "missingness": empty, "correlation": empty, "outliers": empty, "transforms": empty, "hypothesis": empty}
    numeric_cols = [
        c
        for c in (
            "Probability Direction",
            "Probability Target",
            "Expected Net Value",
            "Risk-Normalized Net Value",
            "Uncertainty",
            "Event Risk",
            "Rank Confidence",
            "Rank Stability",
            "Transition Risk",
            "Calibration",
            "CVaR",
            "Volatility",
            "Research Score",
            "Evidence Completeness %",
        )
        if c in master.columns
    ]
    numeric = master[numeric_cols].apply(pd.to_numeric, errors="coerce")
    descriptive = numeric.describe(percentiles=[0.25, 0.5, 0.75]).T.reset_index().rename(columns={"index": "Metric"})
    for name in ("count", "mean", "std", "min", "25%", "50%", "75%", "max"):
        if name in descriptive.columns:
            descriptive[name] = pd.to_numeric(descriptive[name], errors="coerce").round(5)

    group_keys = [c for c in ("Direction Bias", "Data Quality", "Can Trust Rank", "Trade Permission") if c in master.columns]
    group_rows: list[dict[str, Any]] = []
    for key in group_keys:
        for label, group in master.groupby(key, dropna=False):
            group_rows.append(
                {
                    "Group Field": key,
                    "Group": str(label),
                    "Symbols": int(len(group)),
                    "Mean Research Score": round(float(pd.to_numeric(group.get("Research Score"), errors="coerce").mean()), 5),
                    "Mean Transition Risk": round(float(pd.to_numeric(group.get("Transition Risk"), errors="coerce").mean()), 5),
                    "Mean Rank Confidence": round(float(pd.to_numeric(group.get("Rank Confidence"), errors="coerce").mean()), 5),
                }
            )
    groups = pd.DataFrame(group_rows)
    missingness = pd.DataFrame(
        {
            "Field": master.columns,
            "Non-Missing Rows": [int(master[c].notna().sum()) for c in master.columns],
            "Missing Rows": [int(master[c].isna().sum()) for c in master.columns],
            "Completeness %": [round(float(master[c].notna().mean() * 100.0), 1) for c in master.columns],
        }
    ).sort_values(["Completeness %", "Field"], ascending=[True, True], kind="mergesort")
    correlation = numeric.corr(min_periods=3).round(4) if len(numeric_cols) >= 2 else pd.DataFrame()

    outlier_rows: list[dict[str, Any]] = []
    for metric in numeric_cols:
        series = numeric[metric].dropna()
        if len(series) < 4:
            continue
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        if not math.isfinite(float(iqr)) or float(iqr) <= 0:
            continue
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = numeric[metric].lt(low) | numeric[metric].gt(high)
        for index in numeric.index[mask.fillna(False)]:
            outlier_rows.append(
                {
                    "Symbol": master.loc[index, "Symbol"],
                    "Metric": metric,
                    "Value": round(float(numeric.loc[index, metric]), 5),
                    "IQR Lower": round(float(low), 5),
                    "IQR Upper": round(float(high), 5),
                }
            )
    outliers = pd.DataFrame(outlier_rows)

    transforms = master[["Symbol"]].copy()
    for metric in [c for c in ("Research Score", "Expected Net Value", "Transition Risk", "Rank Confidence") if c in numeric]:
        series = numeric[metric]
        std = float(series.std(ddof=0)) if series.notna().any() else 0.0
        transforms[f"{metric} Z-Score"] = ((series - series.mean()) / std).round(4) if std > 0 else 0.0
        span = float(series.max() - series.min()) if series.notna().any() else 0.0
        transforms[f"{metric} Min-Max"] = ((series - series.min()) / span).round(4) if span > 0 else 0.0
        try:
            transforms[f"{metric} Quartile"] = pd.qcut(series.rank(method="first"), 4, labels=["Q1", "Q2", "Q3", "Q4"])
        except Exception:
            transforms[f"{metric} Quartile"] = "INSUFFICIENT_VARIATION"

    hypothesis_rows: list[dict[str, Any]] = []
    if "Trade Permission" in master.columns and "Research Score" in numeric:
        candidate = numeric.loc[master["Trade Permission"].astype(str).str.upper().eq("TRADE CANDIDATE"), "Research Score"].dropna()
        other = numeric.loc[~master["Trade Permission"].astype(str).str.upper().eq("TRADE CANDIDATE"), "Research Score"].dropna()
        if len(candidate) and len(other):
            observed = float(candidate.mean() - other.mean())
            combined = np.concatenate([candidate.to_numpy(), other.to_numpy()])
            rng = np.random.default_rng(42)
            differences = []
            for _ in range(1000):
                shuffled = rng.permutation(combined)
                differences.append(float(shuffled[: len(candidate)].mean() - shuffled[len(candidate) :].mean()))
            p_value = float(np.mean(np.abs(differences) >= abs(observed)))
            hypothesis_rows.append(
                {
                    "Question": "Do trade candidates have a higher research score than non-candidates?",
                    "Candidate N": int(len(candidate)),
                    "Other N": int(len(other)),
                    "Observed Mean Difference": round(observed, 5),
                    "Permutation P-Value": round(p_value, 4),
                    "Interpretation": "EXPLORATORY ONLY — cross-sectional snapshot, not causal proof",
                }
            )
    hypothesis = pd.DataFrame(hypothesis_rows)
    return {
        "descriptive": descriptive,
        "groups": groups,
        "missingness": missingness.reset_index(drop=True),
        "correlation": correlation,
        "outliers": outliers,
        "transforms": transforms,
        "hypothesis": hypothesis,
    }


def _feature_matrix(master: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    features = [
        c
        for c in (
            "Probability Direction",
            "Probability Target",
            "Expected Net Value",
            "Uncertainty",
            "Event Risk",
            "Rank Confidence",
            "Rank Stability",
            "Transition Risk",
            "Calibration",
            "CVaR",
            "Volatility",
        )
        if c in master.columns
    ]
    matrix = master[features].apply(pd.to_numeric, errors="coerce")
    usable = [c for c in matrix if matrix[c].notna().sum() >= max(2, len(matrix) // 3) and matrix[c].nunique(dropna=True) > 1]
    matrix = matrix[usable]
    for col in usable:
        matrix[col] = matrix[col].fillna(matrix[col].median())
    return matrix, usable


def build_data_mining_tables(master: pd.DataFrame, validation: pd.DataFrame | None = None) -> dict[str, Any]:
    validation = _frame(validation)
    if master.empty:
        return {
            "patterns": pd.DataFrame(),
            "feature_importance": pd.DataFrame(),
            "validation": validation,
            "model_summary": pd.DataFrame(),
        }
    matrix, features = _feature_matrix(master)
    patterns = master[[c for c in ("Research Rank", "Symbol", "Direction Bias", "Trade Permission", "Can Trust Rank") if c in master]].copy()
    model_rows: list[dict[str, Any]] = []
    feature_importance = pd.DataFrame()
    if len(matrix) < 3 or len(features) < 2:
        patterns["Pattern Status"] = "INSUFFICIENT_CROSS_SECTIONAL_FEATURES"
        model_rows.append({"Method": "KNN / clustering / anomaly", "Status": "NOT RUN", "Reason": "Need at least 3 symbols and 2 varying numeric features"})
        return {
            "patterns": patterns,
            "feature_importance": feature_importance,
            "validation": validation,
            "model_summary": pd.DataFrame(model_rows),
        }

    scale = matrix.std(ddof=0).replace(0, 1.0)
    standardized = (matrix - matrix.mean()) / scale
    values = standardized.to_numpy(dtype=float)
    distances = np.sqrt(((values[:, None, :] - values[None, :, :]) ** 2).sum(axis=2))
    peer_labels: list[str] = []
    peer_distances: list[float] = []
    for index in range(len(master)):
        order = np.argsort(distances[index])
        peers = [int(x) for x in order if int(x) != index][:2]
        peer_labels.append(", ".join(master.iloc[x]["Symbol"] for x in peers))
        peer_distances.append(round(float(np.mean([distances[index, x] for x in peers])), 4) if peers else np.nan)
    patterns["Nearest Research Peers"] = peer_labels
    patterns["Peer Distance"] = peer_distances
    model_rows.append({"Method": "KNN peer similarity", "Status": "READY", "Reason": f"Standardized Euclidean distance across {len(features)} features"})

    try:
        from sklearn.cluster import KMeans

        clusters = min(3, max(2, len(master) // 4))
        clusters = min(clusters, len(master) - 1)
        labels = KMeans(n_clusters=clusters, n_init=20, random_state=42).fit_predict(values)
        patterns["Research Cluster"] = [f"C{int(x) + 1}" for x in labels]
        model_rows.append({"Method": "KMeans market-state clustering", "Status": "READY", "Reason": f"{clusters} cross-sectional clusters; research-only"})
    except Exception as exc:
        patterns["Research Cluster"] = "UNAVAILABLE"
        model_rows.append({"Method": "KMeans market-state clustering", "Status": "OPTIONAL", "Reason": f"{type(exc).__name__}: {str(exc)[:80]}"})

    if len(master) >= 8:
        try:
            from sklearn.ensemble import IsolationForest

            detector = IsolationForest(n_estimators=200, contamination="auto", random_state=42)
            raw = -detector.fit(values).score_samples(values)
            prediction = detector.predict(values)
            patterns["Anomaly Score"] = np.round(raw, 5)
            patterns["Anomaly Flag"] = np.where(prediction < 0, "REVIEW", "NORMAL")
            model_rows.append({"Method": "Isolation Forest", "Status": "READY", "Reason": "Cross-sectional anomaly review; not a trade signal"})
        except Exception as exc:
            patterns["Anomaly Score"] = standardized.abs().max(axis=1).round(5).to_numpy()
            patterns["Anomaly Flag"] = np.where(patterns["Anomaly Score"] > 2.5, "REVIEW", "NORMAL")
            model_rows.append({"Method": "Robust anomaly fallback", "Status": "READY", "Reason": f"Isolation Forest unavailable: {type(exc).__name__}"})
    else:
        patterns["Anomaly Score"] = standardized.abs().max(axis=1).round(5).to_numpy()
        patterns["Anomaly Flag"] = np.where(patterns["Anomaly Score"] > 2.5, "REVIEW", "NORMAL")
        model_rows.append({"Method": "Standardized anomaly screen", "Status": "READY", "Reason": "Isolation Forest requires at least 8 symbols"})

    target = master["Trade Permission"].astype(str).str.upper().eq("TRADE CANDIDATE").astype(int)
    if len(master) >= 12 and target.nunique() == 2 and target.value_counts().min() >= 3:
        try:
            from sklearn.ensemble import RandomForestClassifier

            model = RandomForestClassifier(
                n_estimators=250,
                max_depth=4,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=42,
                n_jobs=1,
            )
            model.fit(matrix, target)
            feature_importance = pd.DataFrame(
                {
                    "Feature": features,
                    "Surrogate Importance": model.feature_importances_,
                }
            ).sort_values("Surrogate Importance", ascending=False, kind="mergesort")
            feature_importance["Surrogate Importance"] = feature_importance["Surrogate Importance"].round(5)
            model_rows.append(
                {
                    "Method": "Random Forest permission surrogate",
                    "Status": "READY",
                    "Reason": "Explainability only; in-sample surrogate, not predictive validation",
                }
            )
        except Exception as exc:
            model_rows.append({"Method": "Random Forest permission surrogate", "Status": "OPTIONAL", "Reason": f"{type(exc).__name__}: {str(exc)[:80]}"})
    else:
        model_rows.append(
            {
                "Method": "Random Forest permission surrogate",
                "Status": "NOT RUN",
                "Reason": "Need >=12 symbols and >=3 rows in each permission class",
            }
        )
    return {
        "patterns": patterns,
        "feature_importance": feature_importance,
        "validation": validation,
        "model_summary": pd.DataFrame(model_rows),
    }


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "in", "is", "it",
    "of", "on", "or", "that", "the", "to", "was", "with", "after", "before", "amid", "over",
}


def _topic(text: str) -> str:
    value = text.lower()
    rules = (
        ("Central Bank / Rates", ("fed", "ecb", "boj", "rate", "yield", "hawkish", "dovish")),
        ("Inflation", ("inflation", "cpi", "ppi", "prices")),
        ("Growth / PMI", ("growth", "gdp", "pmi", "recession")),
        ("Labor", ("jobs", "payroll", "nfp", "unemployment", "wages")),
        ("Geopolitical", ("war", "conflict", "tariff", "sanction", "election")),
        ("Commodity", ("oil", "gold", "gas", "commodity")),
    )
    for label, tokens in rules:
        if any(token in value for token in tokens):
            return label
    return "Other / Unclassified"


def build_nlp_tables(master: pd.DataFrame, news: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    news = _collapse_news(_frame(news))
    if not news.empty:
        base = news
    elif not master.empty:
        base = master.copy()
    else:
        empty = pd.DataFrame()
        return {"symbols": empty, "topics": empty, "tokens": empty, "bigrams": empty, "sentiment": empty}
    if "Symbol" not in base.columns:
        base["Symbol"] = "UNKNOWN"
    base["Symbol"] = base["Symbol"].map(_norm_symbol)
    title_col = next(
        (
            c
            for c in (
                "Latest High-Impact Symbol News",
                "Latest News Title",
                "News Latest High-Impact Symbol News",
                "News Latest News Title",
                "Title",
            )
            if c in base.columns
        ),
        None,
    )
    sentiment_col = next((c for c in ("News Sentiment", "Sentiment", "News News Sentiment") if c in base.columns), None)
    relevance_col = next((c for c in ("News Relevance Score", "News News Relevance Score") if c in base.columns), None)
    freshness_col = next((c for c in ("News Freshness Minutes", "News News Freshness Minutes") if c in base.columns), None)
    absorption_col = next((c for c in ("News Absorption Score", "News News Absorption Score") if c in base.columns), None)
    conflict_col = next((c for c in ("News Conflict Flag", "News News Conflict Flag") if c in base.columns), None)
    match_col = next((c for c in ("Currency / Symbol Match", "News Currency/Symbol Match", "News News Currency/Symbol Match") if c in base.columns), None)
    status_col = next((c for c in ("Evidence Status", "News Evidence Status") if c in base.columns), None)

    out = pd.DataFrame({"Symbol": base["Symbol"]})
    out["Headline"] = base[title_col].astype(str) if title_col else "NEWS_UNAVAILABLE"
    out["Sentiment"] = base[sentiment_col].astype(str).str.upper() if sentiment_col else "UNAVAILABLE"
    out["Relevance"] = pd.to_numeric(base[relevance_col], errors="coerce").fillna(0.0) if relevance_col else 0.0
    out["Freshness Minutes"] = pd.to_numeric(base[freshness_col], errors="coerce") if freshness_col else np.nan
    out["Freshness Score"] = (1.0 - out["Freshness Minutes"].fillna(72 * 60) / (72 * 60)).clip(0, 1)
    out["Absorption"] = pd.to_numeric(base[absorption_col], errors="coerce").fillna(0.0) if absorption_col else 0.0
    out["Conflict"] = _bool_series(base[conflict_col], base.index).to_numpy() if conflict_col else False
    if match_col:
        out["Entity Match"] = base[match_col].astype(str)
        entity_score = (~base[match_col].astype(str).str.upper().isin({"", "NO_MATCH", "UNAVAILABLE", "NAN"})).astype(float)
    else:
        out["Entity Match"] = "INFERRED_FROM_SYMBOL ROW"
        entity_score = pd.Series(1.0, index=base.index)
    out["Evidence Status"] = base[status_col].astype(str) if status_col else np.where(
        out["Headline"].str.upper().isin({"", "NEWS_UNAVAILABLE", "UNAVAILABLE", "NAN"}),
        "NEWS_UNAVAILABLE",
        "SAVED_NEWS_READY",
    )
    out["Topic"] = out["Headline"].map(_topic)
    reliability = (
        0.40 * out["Relevance"].clip(0, 1)
        + 0.25 * out["Freshness Score"]
        + 0.20 * out["Absorption"].clip(0, 1)
        + 0.15 * entity_score.to_numpy()
    )
    reliability = reliability * np.where(out["Conflict"], 0.55, 1.0)
    reliability = reliability * np.where(out["Evidence Status"].astype(str).str.upper().str.contains("UNAVAILABLE"), 0.0, 1.0)
    out["NLP Evidence Reliability %"] = (reliability * 100.0).round(1)

    token_counter: Counter[str] = Counter()
    bigram_counter: Counter[tuple[str, str]] = Counter()
    for headline in out["Headline"]:
        tokens = [x for x in re.findall(r"[A-Za-z][A-Za-z0-9]+", str(headline).lower()) if x not in _STOPWORDS]
        token_counter.update(tokens)
        bigram_counter.update(zip(tokens, tokens[1:]))
    tokens = pd.DataFrame(
        [{"Token": token, "Count": count} for token, count in token_counter.most_common(30)]
    )
    bigrams = pd.DataFrame(
        [{"Bigram": f"{left} {right}", "Count": count} for (left, right), count in bigram_counter.most_common(30)]
    )
    topics = (
        out.groupby("Topic", dropna=False)
        .agg(
            Articles=("Symbol", "count"),
            Symbols=("Symbol", "nunique"),
            **{
                "Mean Reliability %": ("NLP Evidence Reliability %", "mean"),
                "Mean Relevance": ("Relevance", "mean"),
                "Conflicts": ("Conflict", "sum"),
            },
        )
        .reset_index()
        .sort_values(["Articles", "Mean Reliability %"], ascending=[False, False], kind="mergesort")
    )
    topics["Mean Reliability %"] = topics["Mean Reliability %"].round(1)
    topics["Mean Relevance"] = topics["Mean Relevance"].round(4)
    sentiment = (
        out.groupby("Sentiment", dropna=False)
        .agg(Articles=("Symbol", "count"), Symbols=("Symbol", "nunique"), Conflicts=("Conflict", "sum"))
        .reset_index()
        .sort_values("Articles", ascending=False, kind="mergesort")
    )
    return {
        "symbols": out.sort_values(["NLP Evidence Reliability %", "Relevance"], ascending=[False, False], kind="mergesort").reset_index(drop=True),
        "topics": topics.reset_index(drop=True),
        "tokens": tokens,
        "bigrams": bigrams,
        "sentiment": sentiment.reset_index(drop=True),
    }


def method_registry() -> pd.DataFrame:
    rows = [
        ("Descriptive statistics + grouped analysis", "Data Analysis", "Mean, dispersion, quartiles and cross-symbol groups", "IMPLEMENTED"),
        ("Standardization, normalization, discretization", "Data Analysis", "Z-score, min-max and quartile bins", "IMPLEMENTED"),
        ("IQR outlier detection", "Data Analysis", "Flags unusual cross-sectional metrics without deleting rows", "IMPLEMENTED"),
        ("Permutation hypothesis check", "Data Analysis", "Exploratory candidate-vs-other score comparison", "IMPLEMENTED — EXPLORATORY"),
        ("KNN similarity", "Data Mining", "Nearest symbols in standardized research-feature space", "IMPLEMENTED"),
        ("KMeans clustering", "Data Mining", "Research-only cross-sectional market-state groups", "IMPLEMENTED WHEN DATA SUFFICIENT"),
        ("Isolation Forest", "Data Mining", "Cross-sectional anomaly review; never a trade signal", "IMPLEMENTED WHEN N≥8"),
        ("Random Forest surrogate", "Data Mining", "Explains permission logic; not predictive validation", "IMPLEMENTED WHEN DATA SUFFICIENT"),
        ("Entity matching + sentiment + n-grams", "NLP", "Symbol relevance, event topic, token and bigram evidence", "IMPLEMENTED"),
        ("Hamilton Markov switching", "Quant Research", "Regime-state evidence retained from the published research layer", "PUBLISHED MODEL EVIDENCE"),
        ("GARCH / volatility forecasting", "Quant Research", "Volatility forecast fields and optional research modules", "EVIDENCE REQUIRED PER RUN"),
        ("DCC + Ledoit-Wolf shrinkage", "Portfolio Risk", "Correlation and duplicate-exposure penalties", "PUBLISHED FIELD 10 EVIDENCE"),
        ("CVaR / Expected Shortfall", "Tail Risk", "Downside-tail penalty in the ranking audit", "PUBLISHED FIELD 10 EVIDENCE"),
        ("Conformal uncertainty", "Uncertainty", "Interval width, coverage and uncertainty penalty", "PUBLISHED FIELD 2/10 EVIDENCE"),
        ("BOCPD / drift controls", "Robustness", "Transition/changepoint risk and similar-path warnings", "PUBLISHED FIELD 10/11 EVIDENCE"),
        ("SHAP-style driver attribution", "Explainability", "Per-symbol contribution narrative from the ranking engine", "PUBLISHED FIELD 10 EVIDENCE"),
        ("Walk-forward + purge + embargo", "Validation", "Required chronological validation contract", "GOVERNANCE REQUIREMENT"),
        ("PBO, Deflated Sharpe, White Reality Check", "Validation", "Controls selection bias and multiple testing", "PUBLISHED VALIDATION / PROXY"),
        ("SPA, MCS, Diebold-Mariano, Giacomini-White", "Validation", "Model-comparison and predictive-ability governance", "PUBLISHED OR THESIS ROADMAP"),
    ]
    return pd.DataFrame(rows, columns=["Method", "Research Area", "Purpose", "Status"])


def system_field_map() -> pd.DataFrame:
    rows = [
        ("Settings + selectors", "System Controls", "Load up to the canonical universe, choose timeframe, run and publish one frozen generation"),
        ("Fields 1–2", "Ranking Command Center", "Current decision and calibrated multi-horizon projection evidence"),
        ("Field 3", "Ranking + Data Analysis", "Lower/middle/higher regime, age, reliability and transition evidence"),
        ("Fields 4–9", "Validation Evidence", "Fusion, drift, calibration, counterfactual and research-governance outputs"),
        ("Field 10", "Master Ranking Authority", "Production rank, utility, risk, probability, data quality and permission"),
        ("Field 11", "Data Mining", "Similar-path MFE/MAE, peer evidence and drift warning"),
        ("Field 12", "NLP", "Multi-symbol fundamental news ranking, freshness, relevance, sentiment and conflict"),
        ("Research", "Analysis / Mining / NLP", "Separate thesis workspaces reading the same frozen generation"),
        ("AI Assistant", "Multi-Stock Ranking AI Assistant", "Grounded answers from saved ranking, news, risk, validation and system methodology"),
        ("Legacy tabs", "Preserved Original Workspaces", "Original renderers remain available on demand and are not deleted"),
    ]
    return pd.DataFrame(rows, columns=["Original System Area", "Unified Destination", "Preserved Responsibility"])


def build_thesis_package(state: Mapping[str, Any]) -> dict[str, Any]:
    sources = resolve_research_sources(state)
    master, meta = build_master_ranking(state)
    return {
        "meta": meta,
        "master_ranking": master,
        "data_analysis": build_data_analysis_tables(master),
        "data_mining": build_data_mining_tables(master, sources["validation"]),
        "nlp": build_nlp_tables(master, sources["news"]),
        "validation": sources["validation"],
        "methods": method_registry(),
        "system_field_map": system_field_map(),
    }


def json_safe(value: Any, *, row_limit: int = 200) -> Any:
    if isinstance(value, pd.DataFrame):
        frame = value.head(row_limit).where(pd.notna(value.head(row_limit)), None)
        return frame.to_dict("records")
    if isinstance(value, pd.Series):
        return value.where(pd.notna(value), None).to_dict()
    if isinstance(value, Mapping):
        return {str(key): json_safe(item, row_limit=row_limit) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item, row_limit=row_limit) for item in list(value)[:row_limit]]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not math.isfinite(float(value)) else float(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    return value


def export_thesis_package(state: Mapping[str, Any]) -> str:
    return json.dumps(json_safe(build_thesis_package(state)), indent=2, ensure_ascii=False, default=str)


__all__ = [
    "THESIS_VERSION",
    "resolve_research_sources",
    "build_master_ranking",
    "build_data_analysis_tables",
    "build_data_mining_tables",
    "build_nlp_tables",
    "method_registry",
    "system_field_map",
    "build_thesis_package",
    "export_thesis_package",
    "json_safe",
]
