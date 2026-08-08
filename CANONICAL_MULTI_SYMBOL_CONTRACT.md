# Canonical Multi-Symbol Contract

## Required run identity

- parent run ID and calculation scope
- ordered requested, loaded, failed and excluded symbols
- exact timeframe and common completed-candle policy
- generation, canonical run ID and snapshot hash per child
- provider, provider symbol, source ID and source signature
- available/required candles, coverage and validation mode
- final publication status and component-gate diagnostics

## Selector rule

`ordered_unique(first_loaded + second_loaded + third_loaded)` using only current non-stale exact-symbol/exact-timeframe load records. A pure reorder is reconciled without refetch; membership or timeframe change invalidates that selector until Load Selected Data is pressed.

## Child rule

One child snapshot per loaded symbol. The saved child must contain genuine source data plus Field 1, Field 2 and all three Field 3 standards before Field 10 publication. No active-symbol substitution is allowed.

## Cross-tab rule

Field 1, Field 2, Field 10, Field 11, Dinner, Research, Morning and Finder may filter or visualize persisted evidence, but cannot create a competing production calculation or change rank identity on render.

## Completion rule

A run is complete only when every loaded symbol has a canonical result/publication row, database writes are committed, hashes are stored, and failed/degraded components are reported explicitly.
