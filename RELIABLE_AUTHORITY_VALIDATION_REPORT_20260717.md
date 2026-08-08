# Reliable Authority Validation Report — 2026-07-17

## Scope

The supplied project was audited and repaired around the canonical Field 10
authority, H4/4H identity, Field 12/13 display behavior, append-only storage,
settled outcome contracts, event gates and paper-trade identity.

## Checks performed

| Check | Result | Evidence |
|---|---|---|
| Python compilation | PASS | `python -m compileall -q` completed for the project |
| H4/4H and UTC timestamp identity | PASS | Contract smoke tests and H4 restore test |
| Same completed H4 restore | PASS | Changed source frame did not alter restored table/hash; ranked row order is accepted while parent symbol order remains frozen |
| Append-only authority write | PASS | Repeated publication remains one snapshot; conflicting row is rejected |
| Read-only Field 10/12/Dinner path | PASS | Display paths use `load_saved_field10_authority` |
| Settled target labels | PASS | Future completed rows only; unresolved rows remain unsettled |
| CPI/PPI-style event uncertainty | PASS | Pre-event/released-unconfirmed states block permission |
| Promotion gate | PASS | Insufficient settled sample returns `SHADOW_ONLY` |
| Paper-trade identity | PASS | Selector mutation is rejected; close adds an event without changing entry identity |
| Full pytest suite | NOT RUN | `pytest` is not installed in the supplied runtime (`No module named pytest`) |

## Data evidence limitation

The supplied project database contains research and model-registry rows, but no
settled Field 10 outcome rows or promotion decisions in the inspected current
database. The pasted project report also states that only two parent broker
days and zero settled institutional outcomes were available. Therefore no
accuracy, profitability, calibration, PBO, SPA, Deflated Sharpe or production
promotion claim is made.

## Unavailable dependency

- `pytest` — unavailable in the packaging/runtime environment.

The dependency-independent targeted checks executed in the supplied runtime
covered eight zero-fixture contract tests plus exact restore/conflict,
migration-idempotency and paper-trade identity integration checks.

The project’s declared UI and analytics dependencies were not treated as proof
of successful installation. A deployment environment must install the declared
requirements and run the complete test suite before release.

## Known limitations

1. A local SQLite file cannot guarantee phone/laptop parity. The authority now
   exposes `CROSS_DEVICE_PARITY_UNVERIFIED` until a genuinely shared authority
   URI is configured.
2. The new research contract does not create synthetic order-book data, macro
   consensus, or settled outcomes. Those inputs must be supplied point-in-time.
3. Existing research modules remain available as shadow/background modules; they
   are not automatically promoted by this repair.
4. No live trading is enabled, and no profitability guarantee is made.
