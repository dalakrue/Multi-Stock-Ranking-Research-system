# Canonical Symbol Selector Repair — 20260709

## Fixed misunderstanding

The previous upgrade added the institutional multi-symbol evidence, but some visible selectors still depended on the old “complete child publication” restore path. When that old child restore failed, the UI stayed on the previous active symbol such as AUDUSD and showed:

- “The selected symbol could not be restored from a complete child publication.”
- Field 2 H1/H4 stale Power BI identity mismatch.
- Field 1/2/11 selector changed visually but the displayed evidence did not follow the selected symbol.

This repair changes the selector architecture so every important field/tab can select a canonical symbol directly from the saved institutional run.

## New selector controller

Added:

- `core/canonical_symbol_selection_20260709.py`

It provides:

- `available_symbols(state)` — reads canonical symbols from `canonical_run_identity_20260708`, Field 10 ranking, Field 3, Field 1, Field 2, Field 11, and fallback selector state.
- `activate_symbol(state, symbol, surface=...)` — sets all display-compatible active-symbol keys for the chosen field/tab.
- `filter_frame_for_symbol(frame, symbol)` — filters Field 10/Field 3/Field 11/Research/NLP tables by the loaded symbol.
- `render_selector(...)` — one reusable Multi-Symbol Selector for every field/tab.

This selector no longer fails just because a legacy child publication is missing. It loads from the canonical institutional snapshot first.

## Field/tab behavior repaired

### Lunch Field 1

Field 1 now has a canonical multi-symbol selector. Loading a symbol filters the Field 1 summary and updates compatible display keys before old protected tables render.

### Lunch Field 2 / Power BI Projection

Field 2 now has a canonical multi-symbol selector and uses `field2_canonical_projection_20260708` first. The old H1-only Power BI integrity banner is hidden by default, so H4 canonical projection no longer gets blocked by stale H1 active-symbol OHLC.

### Field 10

Field 10 institutional ranking now has its own selector. It displays selected-symbol evidence and the full canonical ranking.

### Field 11

Field 11 now has a canonical symbol + horizon selector. It filters the saved similar-path snapshot by symbol and horizon before any legacy index simulation. The old shared child-publication selector is hidden.

### Dinner

Dinner is transformed into a master/PhD-style multi-symbol ranking and thesis-evidence tab. It shows:

- Best symbol now.
- Whether it is a clean TRADE CANDIDATE or only best watch symbol.
- Less-risky bias.
- Institutional utility.
- Selected-symbol thesis evidence.
- Why top 4 symbols are top 4.
- Field 3 regime summary.
- Field 11 similar-path summary.
- Research score summary.

Old single-symbol Dinner center is hidden by default, not deleted.

### Research

Research now has a canonical symbol selector and filters research, ranking, and AI/NLP evidence to the selected symbol.

### Finder

Finder now starts with the same canonical multi-symbol selector and selected-symbol ranking/similar-path evidence. Old single-symbol Finder is hidden by default.

### AI/NLP

AI/NLP now has a canonical symbol selector. The local AI answer engine was patched so questions like “what is the best symbol to trade now?” use Field 10 institutional ranking and Field 11 evidence first instead of old single-symbol identity rows.

## Hidden noisy sections by default

These old sections are hidden by default:

- Global “Choose the Lunch Field to Open” box, replaced with compact Field 1/2/3/10/11 buttons.
- Global “Lunch Symbol Connector — Fields 1–3 + Fields 10–11”.
- Startup provider banner at the top of Lunch.
- Shared FX Session Selector widget.
- Interface mode control.
- Legacy H1 Power BI integrity/error banner when canonical Field 2 projection exists.
- Legacy single-symbol Dinner center.
- Legacy single-symbol Finder.

They are hidden, not deleted, to avoid breaking existing imports and protected logic.

## Run buttons

Settings run buttons no longer stay disabled because of stale lock booleans after Super Quick completes. If no active instant job is running, stale lock flags are cleared and Super Quick / Quick / Full buttons remain usable as long as loaded symbols exist.

## Copy/export priority

Lunch copy now prioritizes the multi-symbol Field 10 ranking, Field 11 similar-path evidence, and research validation before legacy current-candle copy.

## Storage cleanup

`__pycache__` and `.pytest_cache` were removed before zipping to reduce package size without deleting production code.
