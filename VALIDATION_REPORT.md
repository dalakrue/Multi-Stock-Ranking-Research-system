# Validation Report

## Executed checks

- Per-file isolated pytest: **332 passed**, **0 failed**, **0 errors**, across **42 files**.
- Related Field 10/multi-symbol suite: **120 passed**.
- New 20260704 upgrade suite: **17 passed**.
- Python `compileall`: **PASS**.
- Import smoke for app/startup/Field 10/API/UI modules: **PASS**.
- Protected uploaded-file hash acceptance: **PASS**.
- Database migration twice: **PASS**; integrity `ok`; zero FK issues.
- Secret-shaped literal/schema/value scan: **PASS**.

## Causal and anti-leakage controls covered

- Transition risk matrix-power/survival formula.
- Cost-adjusted EV and distinct risk-adjusted EV.
- Positive EV target and exceedance probability, not exact equality.
- Last 12 completed H1 tick-volume sum.
- Same-symbol snapshot identity and no heavy calculation on display selection.
- Idempotent exact-candle startup and API deduplication.
- Migration does not invent EV/probability values.
- Existing Field 10 daily lock and protected test suite remain passing.

## Monolithic-run note

A single-process `pytest -q` run reached approximately 65% and then stalled because of legacy cross-test process/session interaction. To avoid treating global state contamination as a product failure, each of the 42 test files was rerun in a fresh Python process. All 332 collected tests passed. The monolithic timeout log is retained as evidence rather than hidden.

## Statistical validation status

The codebase retains existing walk-forward, conformal, calibration, SPA, regime, tail-risk, and research validation modules. No new model is promoted solely from in-sample results. Live out-of-sample trading performance was not available in this environment, so no accuracy/profit claim is made.
