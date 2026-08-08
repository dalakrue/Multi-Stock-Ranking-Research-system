"""One-page multi-stock ranking research system.

The page combines navigation only.  Existing production calculations, Research
logic, and the AI Assistant remain separate modules and consume the same frozen
Settings publication.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

import pandas as pd
import streamlit as st

from core.multi_stock_thesis_research_20260729 import (
    build_data_analysis_tables,
    build_data_mining_tables,
    build_master_ranking,
    build_nlp_tables,
    export_thesis_package,
    method_registry,
    resolve_research_sources,
    system_field_map,
)


PAGE_NAME = "Multi-Stock Ranking Research System"
WORKSPACE_KEY = "multi_stock_research_workspace_20260729"
WORKSPACE_WIDGET_KEY = "multi_stock_research_workspace_selector_20260729"
WORKSPACES = [
    "Ranking Command Center",
    "Multi-Stock Ranking Data Analysis",
    "Multi-Stock Ranking Data Mining",
    "Multi-Stock Ranking NLP",
    "Multi-Stock Ranking AI Assistant",
    "System Controls & Run",
    "Preserved Original Workspaces",
]


def _inject_css() -> None:
    st.markdown(
        """
<style id="multi-stock-thesis-system-20260729">
.msrs-hero{
  padding:clamp(14px,2vw,24px);border-radius:24px;margin:.1rem 0 .7rem;
  color:#0f172a;border:1px solid rgba(59,130,246,.18);
  background:
    radial-gradient(circle at 88% 8%,rgba(14,165,233,.18),transparent 28%),
    linear-gradient(135deg,rgba(255,255,255,.96),rgba(239,246,255,.88));
  box-shadow:0 18px 44px rgba(15,23,42,.08);
}
.msrs-kicker{font-size:.76rem;letter-spacing:.12em;text-transform:uppercase;color:#0369a1;font-weight:900}
.msrs-title{font-size:clamp(1.48rem,3.6vw,2.45rem);font-weight:950;line-height:1.04;margin:.28rem 0}
.msrs-subtitle{max-width:920px;color:#475569;font-size:.91rem;line-height:1.45}
.msrs-note{padding:10px 12px;border-radius:15px;background:rgba(240,249,255,.82);border:1px solid rgba(14,165,233,.15);color:#334155}
@media(max-width:780px){
  .msrs-hero{padding:13px 12px;border-radius:18px;box-shadow:none}
  .msrs-subtitle{font-size:.82rem}
  div[role="radiogroup"]{gap:.22rem!important}
  div[role="radiogroup"] label{font-size:.74rem!important;padding:.18rem!important}
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _safe_rerun() -> None:
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def _set_workspace(name: str) -> None:
    if name in WORKSPACES:
        st.session_state[WORKSPACE_KEY] = name
        st.session_state["multi_stock_research_workspace"] = name
        st.session_state[WORKSPACE_WIDGET_KEY] = name
        st.session_state["ui_navigation_click_ts"] = pd.Timestamp.now().timestamp()


def _workspace_selector() -> str:
    legacy = str(
        st.session_state.get(WORKSPACE_KEY)
        or st.session_state.get("multi_stock_research_workspace")
        or "Ranking Command Center"
    )
    aliases = {
        "Settings": "System Controls & Run",
        "System Controls": "System Controls & Run",
        "Lunch": "Ranking Command Center",
        "Research": "Multi-Stock Ranking Data Analysis",
        "Data Analysis": "Multi-Stock Ranking Data Analysis",
        "Data Mining": "Multi-Stock Ranking Data Mining",
        "NLP": "Multi-Stock Ranking NLP",
        "AI Assistant": "Multi-Stock Ranking AI Assistant",
        "Morning": "Preserved Original Workspaces",
        "Dinner": "Preserved Original Workspaces",
        "Other": "Preserved Original Workspaces",
    }
    current = aliases.get(legacy, legacy)
    if current not in WORKSPACES:
        current = "Ranking Command Center"
    st.session_state[WORKSPACE_KEY] = current
    st.session_state["multi_stock_research_workspace"] = current
    st.session_state[WORKSPACE_WIDGET_KEY] = current
    try:
        selected = st.radio(
            "Unified research workspace",
            WORKSPACES,
            index=WORKSPACES.index(current),
            horizontal=True,
            key=WORKSPACE_WIDGET_KEY,
            help="Only the selected workspace is rendered. Switching workspaces never starts a production calculation.",
        )
    except Exception:
        selected = st.selectbox(
            "Unified research workspace",
            WORKSPACES,
            index=WORKSPACES.index(current),
            key=f"{WORKSPACE_KEY}_fallback",
        )
        st.session_state[WORKSPACE_KEY] = selected
    st.session_state["multi_stock_research_workspace"] = selected
    return str(selected)


def _metric_text(value: Any, fallback: str = "—") -> str:
    if value is None:
        return fallback
    text = str(value)
    return fallback if text.lower() in {"", "nan", "none", "nat"} else text


def _status_strip(master: pd.DataFrame, meta: Mapping[str, Any]) -> None:
    candidates = (
        int(master.get("Trade Permission", pd.Series(dtype=object)).astype(str).str.upper().eq("TRADE CANDIDATE").sum())
        if not master.empty
        else 0
    )
    trusted = (
        int(master.get("Can Trust Rank", pd.Series(dtype=object)).astype(str).str.upper().eq("YES").sum())
        if not master.empty
        else 0
    )
    columns = st.columns(6)
    columns[0].metric("Research Status", str(meta.get("status") or "NOT READY"))
    columns[1].metric("Loaded Symbols", int(len(master)))
    columns[2].metric("Trade Candidates", candidates)
    columns[3].metric("Trustworthy Ranks", trusted)
    columns[4].metric("Timeframe", _metric_text(meta.get("timeframe"), "UNKNOWN"))
    columns[5].metric("Generation", _metric_text(meta.get("generation"), "—")[:18])
    st.caption(
        f"Run ID: {_metric_text(meta.get('run_id'))} · Snapshot: {_metric_text(meta.get('snapshot_hash'))} · "
        f"Completed broker candle: {_metric_text(meta.get('broker_candle_time'))}"
    )


def _best_row(master: pd.DataFrame) -> tuple[pd.Series | None, bool]:
    if master.empty:
        return None, False
    permission = master.get("Trade Permission", pd.Series("", index=master.index)).astype(str).str.upper()
    trust = master.get("Can Trust Rank", pd.Series("", index=master.index)).astype(str).str.upper()
    approved = master[permission.eq("TRADE CANDIDATE") & trust.eq("YES")]
    if not approved.empty:
        return approved.sort_values("Research Rank", kind="mergesort").iloc[0], True
    candidates = master[permission.eq("TRADE CANDIDATE")]
    if not candidates.empty:
        return candidates.sort_values("Research Rank", kind="mergesort").iloc[0], False
    return master.sort_values("Research Rank", kind="mergesort").iloc[0], False


def _render_selected_symbol(master: pd.DataFrame) -> None:
    if master.empty:
        return
    selected = ""
    try:
        from core.canonical_symbol_selection_20260709 import active_symbol, render_selector

        selected, _, _ = render_selector(
            st,
            st.session_state,
            surface="research",
            title="Global Loaded-Symbol Selector — Synchronizes Ranking, Research and AI",
            expanded=False,
        )
        selected = selected or active_symbol(st.session_state, surface="research")
    except Exception:
        selected = str(st.session_state.get("canonical_display_symbol_20260709") or master.iloc[0].get("Symbol") or "")
    match = master[master["Symbol"].astype(str).str.upper().eq(str(selected).upper())]
    if match.empty:
        match = master.head(1)
    row = match.iloc[0]
    st.markdown(f"#### Selected-symbol evidence — {row.get('Symbol', '—')}")
    metrics = st.columns(6)
    metrics[0].metric("Research Rank", _metric_text(row.get("Research Rank")))
    metrics[1].metric("Production Rank", _metric_text(row.get("Production Rank")))
    metrics[2].metric("Bias", _metric_text(row.get("Direction Bias"), "WAIT"))
    metrics[3].metric("Permission", _metric_text(row.get("Trade Permission"), "WAIT"))
    metrics[4].metric("Trust Rank", _metric_text(row.get("Can Trust Rank"), "CAUTION"))
    score = pd.to_numeric(pd.Series([row.get("Research Score")]), errors="coerce").iloc[0]
    metrics[5].metric("Research Score", f"{score:.4f}" if pd.notna(score) else "—")
    reason = str(row.get("No-Trade Reason") or "").strip()
    if reason:
        st.warning(f"Why entry is not fully approved: {reason}")
    explanation = row.get("SHAP-style explanation")
    if explanation and str(explanation).lower() not in {"nan", "none", ""}:
        st.caption(f"Published driver attribution: {explanation}")


def _render_command_center(master: pd.DataFrame, meta: Mapping[str, Any]) -> None:
    st.markdown("## Multi-Stock Master Ranking")
    st.caption(
        "One read-only decision surface for Field 3 regime evidence, Field 10 ranking, Field 11 similar paths, "
        "Field 12 NLP, uncertainty, data quality and validation. Production Rank is preserved; Research Rank is a separate shadow ranking."
    )
    _status_strip(master, meta)
    if master.empty:
        st.error("No published multi-symbol ranking is available.")
        st.info("Open System Controls & Run, load the symbol universe, then run Super Quick, Quick, or Full Calculation once.")
        st.button(
            "Open System Controls & Run",
            key="msrs_open_controls_empty",
            use_container_width=True,
            on_click=_set_workspace,
            args=("System Controls & Run",),
        )
        return

    best, approved = _best_row(master)
    if best is not None:
        symbol = str(best.get("Symbol") or "—")
        bias = str(best.get("Direction Bias") or "WAIT")
        permission = str(best.get("Trade Permission") or "WAIT")
        rank = best.get("Research Rank")
        if approved:
            st.success(
                f"Highest-ranked symbol with both production permission and research trust: {symbol} "
                f"(Research Rank {rank}, {bias}, {permission}). Recheck the frozen candle and execution risk before any entry."
            )
        else:
            st.warning(
                f"No symbol currently satisfies both production permission and the thesis trust gate. "
                f"Highest research-priority watch symbol: {symbol} (Research Rank {rank}, {bias}, {permission})."
            )
    _render_selected_symbol(master)

    visible = [
        c
        for c in (
            "Research Rank",
            "Production Rank",
            "Symbol",
            "Direction Bias",
            "Probability Direction",
            "Probability Target",
            "Expected Net Value",
            "Risk-Normalized Net Value",
            "Uncertainty",
            "Event Risk",
            "Data Quality",
            "Can Trust Rank",
            "Trade Permission",
            "No-Trade Reason",
        )
        if c in master.columns
    ]
    st.markdown("#### Thesis decision table")
    st.dataframe(master[visible], use_container_width=True, hide_index=True, height=430)

    chart_cols = [c for c in ("Research Score", "Expected Net Value", "Rank Confidence") if c in master.columns]
    if chart_cols:
        chart = master[["Symbol", *chart_cols]].copy()
        for col in chart_cols:
            chart[col] = pd.to_numeric(chart[col], errors="coerce")
        st.markdown("#### Cross-symbol score comparison")
        st.bar_chart(chart.set_index("Symbol"), use_container_width=True)

    with st.expander("Open / Close — Expected Net Value formula and safeguards", expanded=False):
        st.code(
            "Expected Net Value = p(target) × Expected MFE\n"
            "                   − (1 − p(target)) × |Expected MAE|\n"
            "                   − transaction cost\n"
            "                   − event penalty\n"
            "                   − uncertainty penalty",
            language="text",
        )
        st.markdown(
            "The formula is calculated only when target probability and Field 11 MFE/MAE evidence exist. "
            "Otherwise the page displays the already-published Field 10 Net Expected Value and labels the source. "
            "BUY/SELL bias never overrides Trade Permission."
        )

    with st.expander("Open / Close — Complete saved ranking evidence", expanded=False):
        st.dataframe(master, use_container_width=True, hide_index=True, height=520)

    export_columns = st.columns(2)
    export_columns[0].download_button(
        "Download Master Research Ranking CSV",
        data=master.to_csv(index=False).encode("utf-8"),
        file_name=f"multi_stock_master_ranking_{_metric_text(meta.get('snapshot_hash'), 'current')}.csv",
        mime="text/csv",
        use_container_width=True,
        key="msrs_master_csv",
    )
    try:
        package_text = export_thesis_package(st.session_state)
    except Exception as exc:
        package_text = json.dumps({"status": "EXPORT_FAILED", "error": f"{type(exc).__name__}: {exc}"}, indent=2)
    export_columns[1].download_button(
        "Download Thesis Evidence Package JSON",
        data=package_text.encode("utf-8"),
        file_name=f"multi_stock_thesis_evidence_{_metric_text(meta.get('snapshot_hash'), 'current')}.json",
        mime="application/json",
        use_container_width=True,
        key="msrs_thesis_json",
    )

    with st.expander("Open / Close — System migration map", expanded=False):
        st.dataframe(system_field_map(), use_container_width=True, hide_index=True)
    with st.expander("Open / Close — Master's / PhD method registry", expanded=False):
        st.dataframe(method_registry(), use_container_width=True, hide_index=True, height=560)
    with st.expander("Open / Close — Interview demonstration script", expanded=False):
        st.markdown(
            "“This project is a deterministic, multi-symbol decision-support system. A single Settings run freezes one canonical "
            "generation. Field 10 provides the production rank; Field 3 adds multi-scale regime evidence; Field 11 contributes "
            "similar-path MFE/MAE; Field 12 contributes symbol-specific NLP and event risk. The unified research layer preserves "
            "the production decision, creates a separate auditable research rank, exposes uncertainty and no-trade reasons, and "
            "supports data analysis, data mining, NLP, validation, export, and grounded AI questions from the same snapshot.”"
        )


def _render_data_analysis(master: pd.DataFrame) -> None:
    st.markdown("## Multi-Stock Ranking Data Analysis")
    st.caption(
        "Midterm concepts upgraded to the live multi-symbol ranking domain: descriptive statistics, grouping, filtering, "
        "correlation, standardization, normalization, discretization, outliers and an explicitly exploratory hypothesis check."
    )
    if master.empty:
        st.info("Run the multi-symbol system once before opening Data Analysis.")
        return
    tables = build_data_analysis_tables(master)
    score = pd.to_numeric(master.get("Research Score"), errors="coerce")
    columns = st.columns(5)
    columns[0].metric("Symbols", len(master))
    columns[1].metric("Numeric Measures", len(tables["descriptive"]))
    columns[2].metric("Mean Research Score", f"{score.mean():.4f}" if score.notna().any() else "—")
    columns[3].metric("Outlier Flags", len(tables["outliers"]))
    columns[4].metric("Average Completeness", f"{pd.to_numeric(master.get('Evidence Completeness %'), errors='coerce').mean():.1f}%")
    st.markdown("#### Descriptive statistics")
    st.dataframe(tables["descriptive"], use_container_width=True, hide_index=True)
    st.markdown("#### Grouped ranking analysis")
    st.dataframe(tables["groups"], use_container_width=True, hide_index=True, height=360)
    left, right = st.columns(2)
    with left:
        st.markdown("#### Missing-data quality")
        st.dataframe(tables["missingness"].head(30), use_container_width=True, hide_index=True, height=360)
    with right:
        st.markdown("#### IQR outlier review")
        if tables["outliers"].empty:
            st.success("No IQR outliers were found in the current cross-sectional snapshot.")
        else:
            st.dataframe(tables["outliers"], use_container_width=True, hide_index=True, height=360)
    with st.expander("Open / Close — Correlation matrix", expanded=True):
        if tables["correlation"].empty:
            st.info("At least two varying numeric metrics with sufficient rows are required.")
        else:
            st.dataframe(tables["correlation"], use_container_width=True)
    with st.expander("Open / Close — Standardization, normalization and discretization", expanded=False):
        st.dataframe(tables["transforms"], use_container_width=True, hide_index=True)
    with st.expander("Open / Close — Exploratory permutation hypothesis check", expanded=False):
        if tables["hypothesis"].empty:
            st.info("The current snapshot does not contain both candidate and non-candidate groups.")
        else:
            st.dataframe(tables["hypothesis"], use_container_width=True, hide_index=True)
        st.caption("This cross-sectional test is exploratory and is not causal or out-of-sample evidence.")


def _render_data_mining(master: pd.DataFrame, validation: pd.DataFrame) -> None:
    st.markdown("## Multi-Stock Ranking Data Mining")
    st.caption(
        "Research-only KNN peers, clustering, anomaly review, optional Random Forest permission-surrogate explainability, "
        "and the published model-validation evidence. These outputs cannot overwrite Production Rank or Trade Permission."
    )
    if master.empty:
        st.info("Run the multi-symbol system once before opening Data Mining.")
        return
    tables = build_data_mining_tables(master, validation)
    st.markdown("#### Pattern and peer-mining table")
    st.dataframe(tables["patterns"], use_container_width=True, hide_index=True, height=430)
    st.markdown("#### Data-mining model status")
    st.dataframe(tables["model_summary"], use_container_width=True, hide_index=True)
    if isinstance(tables["feature_importance"], pd.DataFrame) and not tables["feature_importance"].empty:
        st.markdown("#### Random Forest surrogate feature importance")
        st.dataframe(tables["feature_importance"], use_container_width=True, hide_index=True)
        st.bar_chart(tables["feature_importance"].set_index("Feature"), use_container_width=True)
        st.caption("This is an in-sample explanation of the saved permission boundary, not a forecast-accuracy claim.")
    with st.expander("Open / Close — Published model-validation evidence", expanded=True):
        if tables["validation"].empty:
            st.info("No model-validation table is published for this generation.")
        else:
            st.dataframe(tables["validation"], use_container_width=True, hide_index=True, height=480)
    with st.expander("Open / Close — Thesis validation contract", expanded=False):
        st.markdown(
            "- Chronological walk-forward evaluation; never random train/test shuffling for time-series claims.\n"
            "- Purge and embargo overlapping labels; keep the final holdout untouched.\n"
            "- Report calibration, Brier/log/CRPS, conformal coverage, rank stability and economic cost.\n"
            "- Control multiple testing with PBO/CSCV, Deflated Sharpe, White Reality Check, SPA and Model Confidence Set.\n"
            "- Freeze the entry snapshot and evaluate settled outcomes without rewriting history."
        )


def _render_nlp(master: pd.DataFrame, news: pd.DataFrame) -> None:
    st.markdown("## Multi-Stock Ranking NLP")
    st.caption(
        "A saved-evidence NLP lab for symbol/entity matching, sentiment, relevance, freshness, absorption, conflict, "
        "event topics, tokens and bigrams. Opening this workspace performs no API request."
    )
    tables = build_nlp_tables(master, news)
    symbols = tables["symbols"]
    if symbols.empty:
        st.info("No saved multi-symbol news/NLP evidence is available for the current generation.")
        return
    # Calculate explicitly to avoid bool/int ambiguity across pandas versions.
    ready = int((~symbols["Evidence Status"].astype(str).str.upper().str.contains("UNAVAILABLE")).sum())
    conflicts = int(symbols["Conflict"].astype(bool).sum())
    metrics = st.columns(5)
    metrics[0].metric("Symbols Scored", len(symbols))
    metrics[1].metric("Evidence Ready", ready)
    metrics[2].metric("News Conflicts", conflicts)
    metrics[3].metric("Topics", int(symbols["Topic"].nunique()))
    metrics[4].metric("Mean NLP Reliability", f"{symbols['NLP Evidence Reliability %'].mean():.1f}%")
    st.markdown("#### Symbol-level NLP ranking evidence")
    st.dataframe(symbols, use_container_width=True, hide_index=True, height=430)
    left, right = st.columns(2)
    with left:
        st.markdown("#### Event topics")
        st.dataframe(tables["topics"], use_container_width=True, hide_index=True)
    with right:
        st.markdown("#### Sentiment distribution")
        st.dataframe(tables["sentiment"], use_container_width=True, hide_index=True)
    with st.expander("Open / Close — Token frequency", expanded=False):
        st.dataframe(tables["tokens"], use_container_width=True, hide_index=True)
    with st.expander("Open / Close — Bigram frequency", expanded=False):
        st.dataframe(tables["bigrams"], use_container_width=True, hide_index=True)
    st.info(
        "NLP bias is supporting evidence only. Missing news, stale news, low entity relevance, or a news/technical conflict "
        "must reduce trust or block permission; sentiment alone never creates an entry."
    )


def _render_ai(runtime_context: Mapping[str, Any] | None) -> None:
    st.markdown("## Multi-Stock Ranking AI Assistant")
    st.caption(
        "The original Assistant remains logically separate. It is placed inside this unified page and upgraded to answer "
        "ranking, comparison, data-quality, risk, news, validation, methodology and system-health questions from saved evidence."
    )
    try:
        from pages.ai_assistant import show as show_ai

        show_ai(runtime_context=runtime_context)
    except Exception as exc:
        st.error(f"AI Assistant could not be rendered: {type(exc).__name__}: {exc}")


def _render_settings() -> None:
    st.markdown("## System Controls & Run")
    st.caption(
        "The original Settings logic is preserved here. Load symbols, choose the timeframe and publish one canonical generation; "
        "successful runs return to the Ranking Command Center."
    )
    try:
        from tabs.antd_page_router_20260615 import _render_settings as render_settings

        render_settings()
    except Exception as exc:
        st.error(f"System Controls could not be rendered: {type(exc).__name__}: {exc}")


def _render_preserved_originals() -> None:
    st.markdown("## Preserved Original Workspaces")
    st.caption(
        "Nothing was deleted. Original renderers are archived behind a load gate so they do not compete with the master ranking "
        "or consume resources during normal use."
    )
    choices = [
        "Original Lunch / Fields 1–3 and 10–12",
        "Original Dinner / Fields 4–9",
        "Original Morning / Account Workspace",
        "Original Research",
        "Original Data Visualization / PowerBI",
        "Original Other / Engine and Tools",
    ]
    selected = st.selectbox("Original workspace", choices, key="msrs_preserved_original_choice")
    if not st.toggle("Open selected original workspace", value=False, key="msrs_preserved_original_gate"):
        st.info("Select a workspace and open the gate only when you need the previous layout.")
        st.dataframe(system_field_map(), use_container_width=True, hide_index=True)
        return
    try:
        import tabs.antd_page_router_20260615 as router

        if selected.startswith("Original Lunch"):
            router._render_lunch(router._home_ns(), "")
        elif selected.startswith("Original Dinner"):
            router._render_dinner(router._home_ns(), "")
        elif selected.startswith("Original Morning"):
            router._render_morning()
        elif selected.startswith("Original Research"):
            import tabs.research as research

            research.show()
        elif selected.startswith("Original Data Visualization"):
            router._render_lunch(router._home_ns(), "PowerBI Projection")
        else:
            router._render_other()
    except Exception as exc:
        st.warning(f"The selected original workspace was skipped safely: {type(exc).__name__}: {exc}")


def show(runtime_context: Mapping[str, Any] | None = None) -> None:
    _inject_css()
    st.markdown(
        """
<div class="msrs-hero">
  <div class="msrs-kicker">Canonical multi-symbol decision research</div>
  <div class="msrs-title">Multi-Stock Ranking Research System</div>
  <div class="msrs-subtitle">
    End-to-end ranking, regime evidence, uncertainty, risk, data analysis, data mining, NLP,
    validation, exports and a grounded AI Assistant — all reading one frozen generation.
    Original models and workspaces are preserved.
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    workspace = _workspace_selector()
    sources = resolve_research_sources(st.session_state)
    master, meta = build_master_ranking(st.session_state)

    if workspace == "Ranking Command Center":
        _render_command_center(master, meta)
    elif workspace == "Multi-Stock Ranking Data Analysis":
        _render_data_analysis(master)
    elif workspace == "Multi-Stock Ranking Data Mining":
        _render_data_mining(master, sources["validation"])
    elif workspace == "Multi-Stock Ranking NLP":
        _render_nlp(master, sources["news"])
    elif workspace == "Multi-Stock Ranking AI Assistant":
        _render_ai(runtime_context)
    elif workspace == "System Controls & Run":
        _render_settings()
    else:
        _render_preserved_originals()


__all__ = ["PAGE_NAME", "WORKSPACES", "show"]
