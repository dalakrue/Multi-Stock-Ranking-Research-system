# Upgrade Manifest — 2026-07-29

## Primary additions

- `tabs/multi_stock_ranking_research_system.py`
- `core/multi_stock_thesis_research_20260729.py`
- `tests/test_multi_stock_thesis_system_20260729.py`
- `README_MULTI_STOCK_RANKING_RESEARCH_SYSTEM_20260729.md`
- `RELEASE_VALIDATION_20260729.md`

## Navigation consolidation

The app registry, navigation state, menu renderers, and default state now route
all legacy top-level destinations to one unified page. The former destinations
remain reachable as lazy inner workspaces.

## Preserved logic

- original AI Assistant renderer
- original Research renderer and calculations
- original Settings calculation/run path
- original Lunch, Dinner, Morning, Data Visualization, and Other renderers
- original Field 10 Production Rank and Trade Permission

## Research upgrades

- master ranking evidence adapter
- separate Research Rank
- expected-net-value source labeling
- trust gate and no-trade reason
- data-analysis tables
- data-mining tables
- saved-evidence NLP lab
- multi-symbol/system AI intents
- thesis method registry
- system migration map
- CSV and JSON evidence exports

## Universe upgrade

- three selectors with ten symbols each
- canonical maximum of 30 unique symbols
- Field 10 research maximum aligned to 30
- DXY included in the third default group
- provider aliases added for DXY

## Safety contract

The new layer is read-only with respect to published production decisions.
Research, mining, NLP, and AI views cannot start a full calculation merely by
opening a workspace and cannot replace Production Rank or Trade Permission.
