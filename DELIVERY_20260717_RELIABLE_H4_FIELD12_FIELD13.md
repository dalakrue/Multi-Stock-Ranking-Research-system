# ADX Quant Pro — Reliable H4 authority and Lunch Fields 12/13

## What changed

- Field 10 authority now restores from the durable SQLite snapshot store before
  building a new rank. The restore identity requires the selected timeframe, the
  completed selected-timeframe candle, and the selected symbol universe.
- H4 timestamps are normalized to one UTC boundary identity, so `4H`, `H4`, `Z`
  and `+00:00` reconnect representations cannot trigger a false refresh.
- The durable snapshot ID now includes the completed candle. Two H4 snapshots
  on the same broker day no longer overwrite each other.
- Warm-start restore no longer stops merely because an older canonical object is
  already present. Missing/incomplete `field10_*` authority keys are hydrated.
- Settings/current-result timeframe selection is normalized to `H4`/`H1` before
  signatures and publication, preventing alias drift after reconnect.
- Lunch now exposes two additional relabelled surfaces:
  - **Field 12 — Motion Symbol Higher-Regime Rank**: companion Field 10 logic,
    using the governed 100-pip/4H, Higher-Standard regime and 6H transition
    priorities.
  - **Field 13 — Regime Lifecycle and Three-Standards Evidence**: companion
    Field 3 lifecycle, lower/middle/higher regime, posterior, duration and
    switch-risk evidence.

Both new fields are read-only display adapters. They reuse the first project's
canonical backend and do not start a second connector or ranking engine.

## Reconnect contract

For a selected H4 run, opening Lunch again within the same completed H4 candle
must show the same `daily_snapshot_id`, snapshot hash, rank order and bias. A
refresh is allowed only when the H4 completed-candle identity or selected symbol
universe changes.

## Verification performed

- Python compilation passed for the complete `core`, `ui`, `lunch`, `tabs`,
  `pages` and app source trees.
- Manual smoke test passed for durable exact-H4 restore after changing the
  reconnect source frame.
- Manual smoke test passed for warm-cache repair when a canonical object exists
  but Field 10 authority keys are absent.
- Manual smoke test passed for `4H`/`H4` selection normalization and
  same-universe order-insensitive restore.

The environment used for packaging did not include `pytest`; the existing test
files remain in the project for the deployment environment.
