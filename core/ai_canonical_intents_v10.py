"""Canonical AI evidence contract and deterministic intent routing for Field 5."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
import re
from typing import Any, Mapping, MutableMapping

import pandas as pd

from core.publication_identity_20260625 import freeze_publication_identity
from core.session_context_20260625 import resolve_session_contract

INTENTS = (
    'tp_sl', 'best_symbol', 'compare_symbols', 'why_rank', 'entry', 'forecast_horizon',
    'green_path', 'session', 'current_decision', 'regime', 'reliability_uncertainty',
    'history', 'reversal', 'model_comparison', 'ranking_methodology', 'news_nlp',
    'data_quality', 'risk_portfolio', 'research_method', 'loaded_universe',
    'field_explain', 'system_health', 'general_system_question',
)


@dataclass(frozen=True)
class ParsedQuestion:
    intent: str
    action: str | None = None
    horizon: int | None = None
    field_number: int | None = None
    last_n_days: int | None = None
    symbols: tuple[str, ...] = ()


def _m(v: Any) -> Mapping[str, Any]:
    return v if isinstance(v, Mapping) else {}


def _f(v: Any, default: float | None = None) -> float | None:
    try:
        x = float(v)
        return x if math.isfinite(x) else default
    except Exception:
        return default


def _canonical(state: Mapping[str, Any]) -> Mapping[str, Any]:
    from core.canonical_lookup_20260626 import resolve_canonical
    return resolve_canonical(state)


def _normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', str(text or '').strip().lower())


def _extract_symbols(text: str) -> tuple[str, ...]:
    raw_upper = str(text or '').upper()
    candidates = re.findall(r'\b[A-Z]{3}[/_][A-Z]{3}\b|\b[A-Z][A-Z0-9.^-]{1,11}\b', raw_upper)
    aliases = {
        'XBTUSD': 'BTCUSD',
        'BTCUSDT': 'BTCUSD',
        'GOLD': 'XAUUSD',
        'USDX': 'DXY',
        'DX-Y.NYB': 'DXY',
        'USTEC': 'NAS100',
        'US100': 'NAS100',
        'NDX': 'NAS100',
        'SPX500': 'US500',
        'SP500': 'US500',
        'GSPC': 'US500',
    }
    try:
        from core.multi_symbol_field10_20260701 import SUPPORTED_SYMBOLS
        supported = set(SUPPORTED_SYMBOLS)
    except Exception:
        supported = {
            'AAPL', 'MSFT', 'NVDA', 'AMZN', 'META', 'TSLA', 'GOOGL', 'AVGO', 'JPM', 'AMD',
            'XAUUSD', 'XAGUSD', 'EURUSD', 'USDJPY', 'GBPUSD', 'AUDUSD', 'DXY',
            'NAS100', 'US500', 'US30', 'BTCUSD', 'ETHUSD',
        }
    fiat = {
        'AUD', 'CAD', 'CHF', 'CNH', 'CNY', 'EUR', 'GBP', 'HKD', 'JPY', 'MXN',
        'NOK', 'NZD', 'SEK', 'SGD', 'TRY', 'USD', 'ZAR',
    }
    asset_bases = fiat | {'XAU', 'XAG', 'XPT', 'XPD', 'BTC', 'ETH', 'SOL', 'XRP', 'BNB'}
    result: list[str] = []
    for token in candidates:
        clean = token.replace('/', '').replace('_', '')
        canonical = aliases.get(clean, clean)
        is_pair = (
            len(canonical) == 6
            and canonical[:3] in asset_bases
            and canonical[3:] in (fiat | {'USD', 'USDT'})
        )
        if (canonical in supported or is_pair) and canonical not in result:
            result.append(canonical)
    return tuple(result)


def _parse(text: str) -> ParsedQuestion:
    q = _normalize(text)
    symbols = _extract_symbols(text)
    action = None
    for candidate in ('buy', 'sell', 'wait'):
        if re.search(rf'\b{candidate}\b', q):
            action = candidate.upper()
            break
    horizon = None
    h = re.search(r'\bh\s*([1236])\b|\b([1236])h\b', q)
    if h:
        horizon = int(next(g for g in h.groups() if g))
    field_number = None
    f = re.search(r'\bfield\s*((?:1[0-3])|[1-9])\b', q)
    if f:
        field_number = int(f.group(1))
    last_n_days = None
    n = re.search(r'last\s+(\d+)\s+days?', q)
    if n:
        last_n_days = int(n.group(1))

    if field_number is not None and any(token in q for token in ('field', 'what does', 'explain')):
        return ParsedQuestion(
            intent='field_explain', action=action, horizon=horizon, field_number=field_number,
            last_n_days=last_n_days, symbols=symbols,
        )

    rules = [
        ('tp_sl', ('tp', 'sl', 'take profit', 'stop loss')),
        ('compare_symbols', ('compare symbol', 'compare pair', ' versus ', ' vs ', 'difference between')),
        ('why_rank', ('why rank', 'why is', 'explain rank', 'why blocked', 'no-trade reason', 'no trade reason')),
        ('best_symbol', (
            'best symbol', 'which symbol', 'top symbol', 'symbol to enter', 'best pair',
            'top pair', 'best trade now', 'best to enter', 'best to entry', 'best stock',
            'what stock',
        )),
        ('entry', ('entry', 'enter', 'entry decision')),
        ('forecast_horizon', ('prediction', 'forecast', 'h1', 'h2', 'h3', 'h6', 'projection')),
        ('green_path', ('green path', 'green line', 'less risky path', 'less-risky path')),
        ('session', ('session', 'london', 'new york', 'overlap', 'asia', 'sydney', 'which session is best')),
        ('current_decision', ('current decision', 'decision now', 'buy or sell')),
        ('regime', ('regime', 'market state', 'transition')),
        ('reliability_uncertainty', ('reliability', 'uncertainty', 'confidence', 'trust')),
        ('history', ('history', 'last 25', 'past', 'previous')),
        ('reversal', ('reverse', 'reversal', 'what will reverse')),
        ('ranking_methodology', ('ranking logic', 'rank formula', 'how rank', 'how is rank', 'research rank', 'production rank')),
        ('news_nlp', ('news', 'fundamental', 'nlp', 'sentiment', 'headline', 'field 12')),
        ('data_quality', ('data quality', 'missing data', 'candle count', 'coverage', 'provider', 'stale data')),
        ('risk_portfolio', ('cvar', 'expected shortfall', 'correlation', 'duplicate exposure', 'portfolio risk', 'spread', 'slippage', 'event risk')),
        ('research_method', ('thesis', 'methodology', 'hamilton', 'garch', 'dcc', 'ledoit', 'conformal', 'pbo', 'deflated sharpe', 'shap', 'walk-forward', 'walk forward', 'embargo')),
        ('loaded_universe', ('loaded universe', 'loaded symbols', 'symbol universe', 'how many symbols', 'all symbols')),
        ('model_comparison', ('model', 'spa', 'cpa', 'best model', 'model confidence set')),
        ('system_health', ('ready', 'run id', 'system health', 'publication', 'sync', 'broker candle')),
    ]
    for intent, phrases in rules:
        if any(phrase in q for phrase in phrases):
            return ParsedQuestion(
                intent=intent, action=action, horizon=horizon, field_number=field_number,
                last_n_days=last_n_days, symbols=symbols,
            )
    if len(symbols) >= 2:
        return ParsedQuestion(
            intent='compare_symbols', action=action, horizon=horizon, field_number=field_number,
            last_n_days=last_n_days, symbols=symbols,
        )
    return ParsedQuestion(
        intent='general_system_question', action=action, horizon=horizon, field_number=field_number,
        last_n_days=last_n_days, symbols=symbols,
    )


def _history_frame(state: Mapping[str, Any], limit: int = 25) -> list[dict[str, Any]]:
    for key in ('full_metric_history_df_20260618', 'prediction_vs_actual_history_df', 'dv_pp_bt_hist'):
        value = state.get(key)
        if isinstance(value, pd.DataFrame) and not value.empty:
            return value.head(limit).to_dict('records')
    return []


def _frame_records(value: Any, limit: int = 24) -> list[dict[str, Any]]:
    if isinstance(value, pd.DataFrame) and not value.empty:
        return value.head(limit).where(pd.notna(value.head(limit)), None).to_dict('records')
    if isinstance(value, list):
        return [dict(row) for row in value[:limit] if isinstance(row, Mapping)]
    return []


def _selected_symbol(state: Mapping[str, Any]) -> str:
    try:
        from core.canonical_symbol_selection_20260709 import active_symbol
        value = active_symbol(state, surface='ai')
    except Exception:
        value = state.get('canonical_display_symbol_20260709') or state.get('symbol')
    return str(value or '').strip().upper().replace('/', '').replace('_', '').replace(' ', '')


def _symbol_row(rows: list[dict[str, Any]], symbol: str) -> dict[str, Any]:
    target = str(symbol or '').strip().upper().replace('/', '').replace('_', '').replace(' ', '')
    for row in rows:
        value = str(row.get('Symbol') or '').strip().upper().replace('/', '').replace('_', '').replace(' ', '')
        if value == target:
            return dict(row)
    return {}


def _best_field10_row(contract: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
    rows = [dict(row) for row in (contract.get('field10_multi_symbol_ranking') or []) if isinstance(row, Mapping)]
    if not rows:
        return {}, False
    def rank_value(row: Mapping[str, Any]) -> float:
        return _f(row.get('Rank'), 10_000.0) or 10_000.0
    rows.sort(key=rank_value)
    candidates = []
    for row in rows:
        permission = str(row.get('Entry permission') or row.get('Trade Permission') or '').upper()
        if any(token in permission for token in ('TRADE CANDIDATE', 'ENTRY_ALLOWED', 'ALLOWED', 'READY_TO_ENTER')) and not any(token in permission for token in ('BLOCK', 'WAIT', 'NO_TRADE')):
            candidates.append(row)
    return (candidates[0], True) if candidates else (rows[0], False)


def build_ai_evidence_contract(state: Mapping[str, Any]) -> dict[str, Any]:
    canonical = _canonical(state)
    identity = dict(freeze_publication_identity(state, canonical))
    institutional_identity = _m(state.get('canonical_run_identity_20260708'))
    # Field 10 is the multi-symbol authority.  A valid institutional publication
    # must remain answerable even when the legacy single-symbol canonical bundle
    # has not been generated in the current process.
    identity['run_id'] = identity.get('run_id') or institutional_identity.get('parent_run_id')
    identity['generation_id'] = (
        identity.get('generation_id')
        or institutional_identity.get('generation')
        or identity.get('run_id')
    )
    identity['snapshot_hash'] = identity.get('snapshot_hash') or institutional_identity.get('snapshot_hash')
    session = dict(resolve_session_contract(state, canonical).to_dict())
    institutional_candle = institutional_identity.get('broker_candle_time')
    if institutional_candle:
        session['broker_candle_time'] = institutional_candle
        session['utc_candle_time'] = institutional_candle
    session['source_run_id'] = identity.get('run_id')
    session['generation_id'] = identity.get('generation_id')
    session['snapshot_hash'] = identity.get('snapshot_hash')
    final = _m(canonical.get('final_decision'))
    regime = _m(canonical.get('regime'))
    forecasts = _m(canonical.get('forecasts'))
    field2 = _m(state.get('session_adaptive_projection_20260625'))
    green_df = state.get('less_risky_projection_20260625')
    green_path = green_df.to_dict('records') if isinstance(green_df, pd.DataFrame) and not green_df.empty else []
    field7 = _m(state.get('field7_session_drift_cpa_20260625') or state.get('field_07_research_summary_v11'))
    field8 = _m(state.get('field8_session_calibration_spa_20260625') or state.get('field8_publication_status_20260624'))
    field9 = _m(state.get('field9_doubly_robust_20260625') or state.get('field9_eurusd_h1_decision_impact'))
    field6 = _m(state.get('field6_session_bayesian_fusion_20260625') or state.get('field6_combined_history_summary_20260622'))
    selected_symbol = _selected_symbol(state)
    field10_source = state.get('field10_institutional_ranking_20260708')
    if not isinstance(field10_source, pd.DataFrame) or field10_source.empty:
        field10_source = state.get('field10_current_table_20260701')
    field10_rows = _frame_records(field10_source, limit=40)
    field12_rows = _frame_records(state.get('field12_fundamental_nlp_rank_20260722'), limit=40)
    field3_rows = _frame_records(state.get('field3_multisymbol_regime_20260708'), limit=120)
    field11_rows = _frame_records(state.get('field11_similar_path_multisymbol_20260708'), limit=160)
    research_validation_rows = _frame_records(state.get('research_model_validation_20260708'), limit=120)
    load_audit_rows = _frame_records(state.get('data_load_audit_20260708'), limit=40)
    research_master_rows: list[dict[str, Any]] = []
    research_methods: list[dict[str, Any]] = []
    system_field_map: list[dict[str, Any]] = []
    try:
        from core.multi_stock_thesis_research_20260729 import (
            build_master_ranking,
            method_registry,
            system_field_map as build_system_field_map,
        )
        research_master, _research_meta = build_master_ranking(state)
        research_master_rows = _frame_records(research_master, limit=40)
        research_methods = _frame_records(method_registry(), limit=40)
        system_field_map = _frame_records(build_system_field_map(), limit=30)
    except Exception:
        research_master_rows = []
    selected_field10 = _symbol_row(field10_rows, selected_symbol)
    selected_field12 = _symbol_row(field12_rows, selected_symbol)
    selected_field3 = _symbol_row(field3_rows, selected_symbol)
    selected_research_master = _symbol_row(research_master_rows, selected_symbol)
    health = {
        'run_id_present': bool(identity['run_id']),
        'generation_id_present': bool(identity['generation_id']),
        'snapshot_hash_present': bool(identity['snapshot_hash']),
        'broker_candle_time_present': bool(session.get('broker_candle_time')),
        'canonical_identity_valid': all(bool(identity[k]) for k in ('run_id', 'generation_id', 'snapshot_hash')),
        'publication_status': 'READY' if all(bool(identity[k]) for k in ('run_id', 'generation_id', 'snapshot_hash')) else 'NOT_READY',
        'calculation_scope': str((state or {}).get('settings_calculation_scope_20260625') or 'FULL').upper(),
    }
    tp = _f(final.get('tp_price'), _f(canonical.get('tp_price')))
    sl = _f(final.get('sl_price'), _f(canonical.get('sl_price')))
    current_price = _f(_m(canonical.get('market')).get('current_price'), _f(canonical.get('current_price')))
    pack = {
        'identity': identity,
        'current_decision': str(final.get('final_decision') or canonical.get('decision') or 'UNAVAILABLE'),
        'entry_decision': str(final.get('entry_decision') or canonical.get('entry_decision') or final.get('final_decision') or 'UNAVAILABLE'),
        'less_risky_decision': str(final.get('less_risky_decision') or canonical.get('less_risky_bias') or 'UNAVAILABLE'),
        'current_price': current_price,
        'tp_sl': {'tp': tp, 'sl': sl},
        'prediction_horizons': forecasts,
        'green_path': green_path,
        'session': session,
        'regime_standards': {
            'major_regime': regime.get('major_regime') or regime.get('current_regime') or canonical.get('regime'),
            'reliability': regime.get('reliability') or regime.get('regime_reliability'),
            'three_standard_agreement': regime.get('three_standard_agreement') or regime.get('agreement_score'),
        },
        'reliability': canonical.get('reliability_score') or _m(canonical.get('reliability')).get('score') or regime.get('reliability'),
        'uncertainty': final.get('uncertainty_pct') or final.get('uncertainty') or canonical.get('uncertainty'),
        'reversal_conditions': field9.get('minimum_reversal_conditions') or _m(field9.get('current_summary')).get('reversal_conditions') or canonical.get('reversal_conditions') or 'UNAVAILABLE',
        'field1_history': _history_frame(state, 25),
        'field2_settled_evidence': field2,
        'field3_regime_evidence': regime,
        'field6_fusion_evidence': field6,
        'field7_drift_cpa_evidence': field7,
        'field8_calibration_spa_evidence': field8,
        'field9_counterfactual_value_evidence': field9,
        'selected_symbol': selected_symbol,
        'field10_multi_symbol_ranking': field10_rows,
        'field10_selected_symbol_row': selected_field10,
        'field12_fundamental_news_ranking': field12_rows,
        'field12_selected_symbol_row': selected_field12,
        'field3_selected_symbol_row': selected_field3,
        'field11_similar_path_evidence': field11_rows,
        'research_model_validation': research_validation_rows,
        'data_load_audit': load_audit_rows,
        'research_master_ranking': research_master_rows,
        'research_selected_symbol_row': selected_research_master,
        'research_method_registry': research_methods,
        'system_field_map': system_field_map,
        'loaded_symbols': list(
            institutional_identity.get('canonical_symbols')
            or institutional_identity.get('loaded_symbols')
            or [row.get('Symbol') for row in field10_rows if row.get('Symbol')]
        ),
        'timeframe': str(institutional_identity.get('timeframe') or state.get('selected_timeframe') or state.get('timeframe') or 'UNKNOWN'),
        'multi_symbol_answer_authority': 'FIELD_10',
        'fundamental_news_authority': 'FIELD_12',
        'system_health': health,
    }
    return pack


def validate_ai_evidence_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    missing = []
    identity = _m(contract.get('identity'))
    for key in ('run_id', 'generation_id', 'snapshot_hash'):
        if not identity.get(key):
            missing.append(key)
    if not _m(contract.get('session')).get('broker_candle_time'):
        missing.append('broker_candle_time')
    decision = str(contract.get('current_decision') or '').strip().upper()
    if decision in {'', 'UNAVAILABLE'} and not contract.get('field10_multi_symbol_ranking'):
        missing.append('current_decision')
    return {"ready": len(missing) == 0, "missing_components": missing}


def _evidence_rows(contract: Mapping[str, Any], parsed: ParsedQuestion) -> list[dict[str, Any]]:
    identity = _m(contract.get('identity'))
    rows = []
    def add(source_field: str, metric: str, value: Any):
        rows.append({
            'source field': source_field,
            'metric': metric,
            'value': value,
            'origin time': _m(contract.get('session')).get('broker_candle_time'),
            'run_id': identity.get('run_id'),
            'generation_id': identity.get('generation_id'),
            'snapshot_hash': identity.get('snapshot_hash'),
        })
    add('identity', 'current_decision', contract.get('current_decision'))
    add('identity', 'less_risky_decision', contract.get('less_risky_decision'))
    add('identity', 'current_price', contract.get('current_price'))
    if parsed.intent in {'best_symbol', 'entry'}:
        best, approved = _best_field10_row(contract)
        add('field10', 'multi_symbol_best_row', best)
        add('field10', 'entry_approved', approved)
        if best:
            symbol = str(best.get('Symbol') or '')
            news = _symbol_row(list(contract.get('field12_fundamental_news_ranking') or []), symbol)
            add('field12', 'fundamental_news_for_best_symbol', news)
    if parsed.intent in {'compare_symbols', 'why_rank', 'risk_portfolio', 'data_quality'}:
        requested = list(parsed.symbols) or [str(contract.get('selected_symbol') or '')]
        rows = [_rank_row(contract, symbol) for symbol in requested if symbol]
        add('unified_research', 'requested_symbol_rows', [row for row in rows if row])
    if parsed.intent == 'news_nlp':
        symbol = _question_symbol(parsed, contract)
        rows = list(contract.get('field12_fundamental_news_ranking') or [])
        add('field12', 'news_nlp_evidence', _symbol_row(rows, symbol) if symbol else rows[:5])
    if parsed.intent in {'ranking_methodology', 'research_method', 'model_comparison'}:
        add('research', 'method_registry', list(contract.get('research_method_registry') or []))
        add('research', 'model_validation', list(contract.get('research_model_validation') or [])[:20])
    if parsed.intent == 'loaded_universe':
        add('identity', 'loaded_symbols', contract.get('loaded_symbols'))
        add('identity', 'timeframe', contract.get('timeframe'))
    if parsed.intent == 'field_explain':
        add('architecture', f'field_{parsed.field_number}', contract.get('system_field_map'))
    if parsed.horizon:
        forecasts = _m(contract.get('prediction_horizons')).get('horizons')
        item = _m(_m(forecasts).get(f'{parsed.horizon}h') if isinstance(forecasts, Mapping) else {})
        add('field2', f'H{parsed.horizon} forecast', item)
    if parsed.intent == 'green_path':
        green = contract.get('green_path') or []
        add('field2', 'green_path_rows', len(green))
    if parsed.intent == 'session':
        add('field2', 'selected_session', _m(contract.get('session')).get('selected_session'))
    return rows


def _horizon_item(contract: Mapping[str, Any], horizon: int | None) -> Mapping[str, Any]:
    forecasts = _m(contract.get('prediction_horizons')).get('horizons')
    if isinstance(forecasts, Mapping):
        if horizon is None:
            horizon = 3
        return _m(forecasts.get(f'{horizon}h') or forecasts.get(str(horizon)) or forecasts.get(horizon))
    return {}


def _ranking_rows(contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    research = [dict(row) for row in (contract.get('research_master_ranking') or []) if isinstance(row, Mapping)]
    if research:
        return research
    return [dict(row) for row in (contract.get('field10_multi_symbol_ranking') or []) if isinstance(row, Mapping)]


def _question_symbol(parsed: ParsedQuestion, contract: Mapping[str, Any]) -> str:
    if parsed.symbols:
        return str(parsed.symbols[0])
    return str(contract.get('selected_symbol') or '')


def _rank_row(contract: Mapping[str, Any], symbol: str) -> dict[str, Any]:
    return _symbol_row(_ranking_rows(contract), symbol)


def _value(row: Mapping[str, Any], *names: str, default: Any = 'UNAVAILABLE') -> Any:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip().upper() not in {'', 'NAN', 'NONE', 'UNAVAILABLE'}:
            return value
    return default


def _compact_symbol_line(row: Mapping[str, Any]) -> str:
    return (
        f"{_value(row, 'Symbol')} — research rank={_value(row, 'Research Rank')}, "
        f"production rank={_value(row, 'Production Rank', 'Rank')}, "
        f"bias={_value(row, 'Direction Bias', 'Less-Risky Bias', 'Final daily less-risky bias')}, "
        f"permission={_value(row, 'Trade Permission', 'Entry permission')}, "
        f"trust={_value(row, 'Can Trust Rank')}, "
        f"score={_value(row, 'Research Score', 'InstitutionalUtility')}, "
        f"transition risk={_value(row, 'Transition Risk', 'Transition Risk 6H')}, "
        f"data quality={_value(row, 'Data Quality', 'Data quality grade')}."
    )


def _answer(parsed: ParsedQuestion, contract: Mapping[str, Any]) -> str:
    identity = _m(contract.get('identity'))
    current_price = _f(contract.get('current_price'))
    session = _m(contract.get('session'))
    if parsed.intent == 'best_symbol':
        best, approved = _best_field10_row(contract)
        if not best:
            return 'Field 10 has no published multi-symbol ranking for the current loaded universe. Run a Settings calculation after loading symbols.'
        symbol = str(best.get('Symbol') or 'UNAVAILABLE')
        rank = best.get('Rank', '—')
        permission = str(best.get('Entry permission') or best.get('Trade Permission') or 'UNAVAILABLE')
        bias = str(best.get('Final daily less-risky bias') or best.get('Less-Risky Bias') or best.get('Higher-Standard Bias') or 'WAIT')
        utility = best.get('InstitutionalUtility', best.get('Authority Score', 'UNAVAILABLE'))
        news = _symbol_row(list(contract.get('field12_fundamental_news_ranking') or []), symbol)
        news_text = 'Field 12 news evidence is unavailable.'
        if news:
            news_text = (
                f"Field 12 fundamental context: bias={news.get('Fundamental Bias', 'WAIT')}, "
                f"permission={news.get('News Permission', 'UNAVAILABLE')}, "
                f"headline={news.get('Latest High-Impact Symbol News', 'NEWS_UNAVAILABLE')}."
            )
        if approved:
            opening = f'Best currently approved symbol from Field 10: {symbol} (rank {rank}).'
        else:
            opening = f'No loaded symbol is currently approved for entry. The highest-ranked Field 10 watch symbol is {symbol} (rank {rank}).'
        return (
            f"{opening}\nField 10 entry permission: {permission}.\nField 10 less-risky bias: {bias}.\n"
            f"Field 10 utility/authority: {utility}.\n{news_text}\n"
            "Authority note: this answer uses Field 10 multi-symbol ranking, not Field 1 single-symbol history."
        )
    if parsed.intent == 'compare_symbols':
        rows = _ranking_rows(contract)
        requested = list(parsed.symbols)
        if len(requested) < 2:
            ordered = sorted(
                rows,
                key=lambda row: _f(row.get('Research Rank'), _f(row.get('Rank'), 10_000.0)) or 10_000.0,
            )
            requested = [str(row.get('Symbol') or '') for row in ordered[:2]]
        selected = [_rank_row(contract, symbol) for symbol in requested]
        selected = [row for row in selected if row]
        if len(selected) < 2:
            return (
                'I need two symbols that exist in the current loaded universe. '
                f"Loaded symbols: {contract.get('loaded_symbols') or 'UNAVAILABLE'}."
            )
        lines = ['Saved-evidence comparison:']
        lines.extend(_compact_symbol_line(row) for row in selected)
        winner = sorted(
            selected,
            key=lambda row: (
                {'YES': 2, 'CAUTION': 1, 'NO': 0}.get(str(row.get('Can Trust Rank') or '').upper(), 0),
                _f(row.get('Research Score'), _f(row.get('InstitutionalUtility'), -1e9)) or -1e9,
            ),
            reverse=True,
        )[0]
        lines.append(
            f"Research-priority result: {_value(winner, 'Symbol')}. "
            "This does not create permission; the saved Trade Permission remains authoritative."
        )
        return '\n'.join(lines)
    if parsed.intent == 'why_rank':
        symbol = _question_symbol(parsed, contract)
        row = _rank_row(contract, symbol)
        if not row:
            return f'No published ranking row exists for {symbol or "the selected symbol"}. Choose a loaded symbol first.'
        return (
            f"Why {_value(row, 'Symbol')} has this rank:\n"
            f"Research Rank: {_value(row, 'Research Rank')} | Production Rank: {_value(row, 'Production Rank', 'Rank')}\n"
            f"Expected Net Value: {_value(row, 'Expected Net Value', 'Net Expected Value', 'WeightedNetEV')}\n"
            f"Rank Confidence: {_value(row, 'Rank Confidence', 'Rank confidence')} | "
            f"Rank Stability: {_value(row, 'Rank Stability', 'Rank stability')}\n"
            f"Transition Risk: {_value(row, 'Transition Risk', 'Transition Risk 6H')} | "
            f"Calibration: {_value(row, 'Calibration', 'Calibration score')}\n"
            f"Data Quality: {_value(row, 'Data Quality', 'Data quality grade')} | "
            f"News Conflict: {_value(row, 'News Conflict', 'News Conflict Flag')}\n"
            f"Permission: {_value(row, 'Trade Permission', 'Entry permission')} | "
            f"No-trade reason: {_value(row, 'No-Trade Reason', 'Missing reason', default='NONE')}\n"
            f"Published driver explanation: {_value(row, 'SHAP-style explanation', default='UNAVAILABLE')}"
        )
    if parsed.intent == 'entry':
        selected = str(contract.get('selected_symbol') or 'UNAVAILABLE')
        row = _m(contract.get('field10_selected_symbol_row'))
        if row:
            permission = str(row.get('Entry permission') or row.get('Trade Permission') or 'UNAVAILABLE')
            bias = str(row.get('Final daily less-risky bias') or row.get('Less-Risky Bias') or row.get('Higher-Standard Bias') or 'WAIT')
            return (
                f"Selected symbol: {selected}\nField 10 entry permission: {permission}\nField 10 less-risky bias: {bias}\n"
                f"Field 10 rank: {row.get('Rank', '—')}\nThis entry answer is sourced from Field 10, not Field 1."
            )
        return f'No Field 10 row is published for the selected loaded symbol {selected}. Choose a loaded symbol or run Settings once.'
    if parsed.intent == 'tp_sl':
        tp = _f(_m(contract.get('tp_sl')).get('tp'))
        sl = _f(_m(contract.get('tp_sl')).get('sl'))
        action = parsed.action or str(contract.get('current_decision') or 'UNAVAILABLE')
        lines = [f'Action: {action}', f'Current price: {current_price if current_price is not None else "UNAVAILABLE"}']
        if tp is not None:
            pips = abs(tp - current_price) * 10000 if current_price is not None else None
            lines.append(f'TP: {tp}')
            lines.append(f'Distance in pips: {pips:.1f}' if pips is not None else 'Distance in pips: UNAVAILABLE')
        else:
            lines.append('TP evidence unavailable')
        if sl is not None:
            lines.append(f'SL: {sl}')
        lines.append(f'Relevant horizon: H{parsed.horizon or 3}')
        lines.append(f'Broker candle: {session.get("broker_candle_time") or "UNAVAILABLE"}')
        lines.append(f'Run ID: {identity.get("run_id") or "UNAVAILABLE"}')
        lines.append('Evidence sources: canonical decision, protected forecast bundle, AI evidence contract')
        return '\n'.join(lines)
    if parsed.intent == 'forecast_horizon':
        item = _horizon_item(contract, parsed.horizon)
        return f"H{parsed.horizon or 3} prediction: {item or 'UNAVAILABLE'}\nBroker candle: {session.get('broker_candle_time')}\nRun ID: {identity.get('run_id')}"
    if parsed.intent == 'green_path':
        green = contract.get('green_path') or []
        if not green:
            validation = validate_ai_evidence_contract(contract)
            missing = list(validation.get('missing_components') or [])
            suffix = f" Missing components: {missing}." if missing else ''
            return 'Green-path evidence unavailable for this run because the exact published central path, current price, or valid bounds are not all available.' + suffix
        row = green[0]
        return (
            f"The green line is lower than the main path because shrinkage pulls the session-adjusted central path back toward the current price. "
            f"Current price={row.get('Current Price')}; base central={row.get('Base Central Path')}; session-adjusted={row.get('Session-Adjusted Path')}; "
            f"green={row.get('Green Less-Risky Path')}; path trust={row.get('Path Trust')}; tier={row.get('Green Tier')}; reason codes={row.get('Reason Codes')}."
        )
    if parsed.intent == 'session':
        evidence = _m(contract.get('field2_settled_evidence'))
        stats = evidence.get('stats') if isinstance(evidence.get('stats'), pd.DataFrame) else pd.DataFrame()
        if stats.empty:
            return 'No settled session performance evidence is available yet, so no best session is claimed.'
        rows = []
        for _, r in stats.sort_values(['direction_accuracy', 'sample_count'], ascending=[False, False]).iterrows():
            rows.append(f"{r['session']}: n={int(r['sample_count'])}, direction_accuracy={float(r['direction_accuracy']):.3f}, coverage={float(r['interval_coverage']):.3f}")
        return 'Settled session comparison:\n' + '\n'.join(rows[:5])
    if parsed.intent == 'current_decision':
        return f"Current decision: {contract.get('current_decision')}\nLess-risky decision: {contract.get('less_risky_decision')}\nRun ID: {identity.get('run_id')}"
    if parsed.intent == 'regime':
        return f"Regime evidence: {contract.get('regime_standards')}"
    if parsed.intent == 'reliability_uncertainty':
        return f"Reliability: {contract.get('reliability')}\nUncertainty: {contract.get('uncertainty')}"
    if parsed.intent == 'history':
        return f"Field 1 history rows available: {len(contract.get('field1_history') or [])}\nMost recent sample: {(contract.get('field1_history') or ['UNAVAILABLE'])[0]}"
    if parsed.intent == 'reversal':
        return f"Minimum reversal conditions: {contract.get('reversal_conditions')}"
    if parsed.intent == 'model_comparison':
        return f"Field 7 evidence: {contract.get('field7_drift_cpa_evidence')}\nField 8 evidence: {contract.get('field8_calibration_spa_evidence')}"
    if parsed.intent == 'ranking_methodology':
        return (
            "The system keeps two ranks separate:\n"
            "1. Production Rank is the unchanged Field 10 authority.\n"
            "2. Research Rank is a shadow thesis rank ordered by trust gate and risk-normalized evidence.\n"
            "When Field 11 target probability, MFE and MAE are available, the research formula is:\n"
            "p(target)×MFE − (1−p(target))×|MAE| − transaction cost − event penalty − uncertainty penalty.\n"
            "If those inputs are incomplete, it falls back to the labeled published Field 10 Net Expected Value. "
            "Bias never overrides Trade Permission, and no-trade reasons remain visible."
        )
    if parsed.intent == 'news_nlp':
        symbol = _question_symbol(parsed, contract)
        rows = [dict(row) for row in (contract.get('field12_fundamental_news_ranking') or []) if isinstance(row, Mapping)]
        if symbol:
            row = _symbol_row(rows, symbol)
            if not row:
                return f'No Field 12 news/NLP row is published for {symbol}.'
            return (
                f"Field 12 NLP for {symbol}:\n"
                f"Fundamental bias: {_value(row, 'Fundamental Bias', 'News Sentiment')}\n"
                f"Permission: {_value(row, 'News Permission')}\n"
                f"Relevance: {_value(row, 'News Relevance Score')} | Freshness minutes: {_value(row, 'News Freshness Minutes')}\n"
                f"Absorption: {_value(row, 'News Absorption Score')} | Conflict: {_value(row, 'News Conflict Flag')}\n"
                f"Headline: {_value(row, 'Latest High-Impact Symbol News', 'Latest News Title')}\n"
                "News is supporting evidence only and cannot create a trade entry."
            )
        if not rows:
            return 'No Field 12 multi-symbol news/NLP evidence is published.'
        lines = ['Top saved Field 12 news rows:']
        for row in rows[:5]:
            lines.append(
                f"{_value(row, 'Symbol')}: rank={_value(row, 'Fundamental Rank', 'Rank')}, "
                f"bias={_value(row, 'Fundamental Bias')}, permission={_value(row, 'News Permission')}, "
                f"headline={_value(row, 'Latest High-Impact Symbol News', 'Latest News Title')}."
            )
        return '\n'.join(lines)
    if parsed.intent == 'data_quality':
        symbol = _question_symbol(parsed, contract)
        row = _rank_row(contract, symbol) if symbol else {}
        if row:
            return (
                f"Data quality for {_value(row, 'Symbol')}:\n"
                f"Grade: {_value(row, 'Data Quality', 'Data quality grade')}\n"
                f"Candle count: {_value(row, 'Candle count')} | Coverage: {_value(row, 'Coverage ratio')}\n"
                f"Provider: {_value(row, 'Provider used')} | Completed candle: {_value(row, 'Broker Candle Time')}\n"
                f"Evidence completeness: {_value(row, 'Evidence Completeness %')}%\n"
                f"Permission impact: {_value(row, 'Trade Permission', 'Entry permission')} — "
                f"{_value(row, 'No-Trade Reason', 'Missing reason', default='NONE')}."
            )
        audits = [dict(item) for item in (contract.get('data_load_audit') or []) if isinstance(item, Mapping)]
        if not audits:
            return 'No data-load audit is published for the current generation.'
        degraded = [
            item for item in audits
            if str(item.get('Loaded status') or '').upper() in {'BLOCKED', 'DATA DEGRADED'}
            or str(item.get('Failure reason') or '').strip()
        ]
        return f"Loaded-symbol data audit rows: {len(audits)}. Degraded/missing rows: {degraded or 'NONE'}."
    if parsed.intent == 'risk_portfolio':
        symbol = _question_symbol(parsed, contract)
        row = _rank_row(contract, symbol)
        if not row:
            return f'No saved risk row exists for {symbol or "the selected symbol"}.'
        return (
            f"Portfolio/risk evidence for {_value(row, 'Symbol')}:\n"
            f"CVaR / expected shortfall: {_value(row, 'CVaR', 'CVaR / drawdown-risk estimate')}\n"
            f"Transition risk 6H: {_value(row, 'Transition Risk', 'Transition Risk 6H')}\n"
            f"Correlation penalty: {_value(row, 'Correlation penalty using Ledoit-Wolf shrinkage and DCC')}\n"
            f"Duplicate exposure penalty: {_value(row, 'Duplicate exposure penalty')}\n"
            f"Spillover risk: {_value(row, 'Spillover risk using Diebold-Yilmaz logic')}\n"
            f"Transaction cost: {_value(row, 'Transaction Cost', 'Spread/slippage cost if available')}\n"
            f"Event risk: {_value(row, 'Event Risk')} | Uncertainty: {_value(row, 'Uncertainty', 'Conformal interval width')}\n"
            f"Trade Permission: {_value(row, 'Trade Permission', 'Entry permission')}."
        )
    if parsed.intent == 'research_method':
        methods = [dict(row) for row in (contract.get('research_method_registry') or []) if isinstance(row, Mapping)]
        # ParsedQuestion intentionally stores structure, not the full query, so
        # provide the complete concise registry when a specific token is absent.
        selected = methods
        if not selected:
            return 'The research method registry is unavailable for this run.'
        lines = ['Thesis/research method registry:']
        for row in selected[:20]:
            lines.append(
                f"{row.get('Method')}: {row.get('Purpose')} [{row.get('Status')}]."
            )
        lines.append(
            "Governance rule: a method name or one strong backtest is not promotion evidence; use chronological walk-forward, "
            "purge/embargo, calibration, costs, multiple-testing control and settled outcomes."
        )
        return '\n'.join(lines)
    if parsed.intent == 'loaded_universe':
        symbols = list(contract.get('loaded_symbols') or [])
        return (
            f"Loaded canonical universe ({len(symbols)} symbols): {', '.join(map(str, symbols)) or 'UNAVAILABLE'}.\n"
            f"Timeframe: {contract.get('timeframe') or 'UNKNOWN'}.\n"
            "Field 10 ranks this universe; the selected display symbol does not replace another symbol's identity."
        )
    if parsed.intent == 'field_explain':
        number = parsed.field_number
        mapping = [dict(row) for row in (contract.get('system_field_map') or []) if isinstance(row, Mapping)]
        for row in mapping:
            area = str(row.get('Original System Area') or '')
            if number is not None and re.search(rf'\b{number}\b', area):
                return (
                    f"{area} is unified into {row.get('Unified Destination')}.\n"
                    f"Responsibility: {row.get('Preserved Responsibility')}."
                )
        field_notes = {
            1: 'Current multi-symbol decision summary.',
            2: 'Calibrated multi-horizon projection and conformal bounds.',
            3: 'Lower, middle and higher regime, bias, age and transition evidence.',
            4: 'Supporting research evidence preserved in the original Fields 4–9 workspace.',
            5: 'Supporting research/AI evidence preserved without replacing Field 10.',
            6: 'Bayesian/fusion supporting evidence.',
            7: 'Drift, CPA and shadow model comparison.',
            8: 'Calibration, SPA and model-confidence evidence.',
            9: 'Counterfactual, reversal and doubly robust evidence.',
            10: 'Production multi-symbol ranking authority.',
            11: 'Similar-path MFE/MAE and drift evidence.',
            12: 'Fundamental news/NLP authority.',
            13: 'Legacy supporting surface preserved in Original Workspaces.',
        }
        return f"Field {number}: {field_notes.get(number, 'No documented field mapping is available.')}"
    if parsed.intent == 'system_health':
        validation = validate_ai_evidence_contract(contract)
        valid = bool(validation.get("ready"))
        missing = list(validation.get("missing_components") or [])
        return f"System health: {'READY' if valid else 'NOT READY'}\nMissing components: {missing or 'NONE'}\nIdentity: {identity}\nBroker candle: {session.get('broker_candle_time')}"
    symbols = list(contract.get('loaded_symbols') or [])
    return (
        "This is the unified Multi-Stock Ranking Research System. It uses one frozen Settings generation and keeps "
        "production ranking, research analysis, data mining, NLP and AI logically separated.\n"
        f"Current loaded universe: {', '.join(map(str, symbols)) or 'UNAVAILABLE'}.\n"
        "Field 10 is the production ranking authority; Field 3 supplies regime evidence; Field 11 supplies similar-path "
        "MFE/MAE; Field 12 supplies news/NLP; validation evidence supplies calibration, PBO/DSR/SPA/MCS and drift checks.\n"
        "You can ask for the best approved symbol, compare two symbols, explain a rank/no-trade reason, data quality, "
        "portfolio risk, news, any Field 1–13 role, loaded universe, model validation, thesis methodology or system health."
    )


def answer_canonical_question(question: str, state: MutableMapping[str, Any]) -> dict[str, Any]:
    contract = build_ai_evidence_contract(state)
    validation = validate_ai_evidence_contract(contract)
    valid = bool(validation.get("ready"))
    missing = list(validation.get("missing_components") or [])
    parsed = _parse(question)
    answer = _answer(parsed, contract)
    evidence = _evidence_rows(contract, parsed)
    evidence_hash = sha256(json.dumps({'contract': contract.get('identity'), 'intent': parsed.intent, 'question': question}, sort_keys=True, default=str).encode('utf-8')).hexdigest()
    return {
        'answer': answer,
        'status': 'ANSWER',
        'intent': parsed.intent,
        'run_id': _m(contract.get('identity')).get('run_id') or 'UNAVAILABLE',
        'normalized_query': _normalize(question),
        'evidence': contract,
        'evidence_used': evidence,
        'evidence_hash': evidence_hash,
        'full_recalculation_performed': False,
        'ready': valid,
        'missing_components': missing,
        'parsed': parsed.__dict__,
    }


# Backward-compatible helpers.
def normalize_query(question: str) -> str:
    return _normalize(question)


def detect_intent(question: str) -> str:
    return _parse(question).intent


def build_intent_evidence(question: str, state: Mapping[str, Any]) -> dict[str, Any]:
    parsed = _parse(question)
    return {'intent': parsed.intent, 'query': _normalize(question), 'evidence': build_ai_evidence_contract(state)}


__all__ = [
    'INTENTS', 'normalize_query', 'detect_intent', 'build_intent_evidence',
    'build_ai_evidence_contract', 'validate_ai_evidence_contract', 'answer_canonical_question'
]
