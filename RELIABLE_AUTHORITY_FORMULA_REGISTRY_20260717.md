# Reliable Authority Formula Registry — 2026-07-17

## Identity

```text
authority_key = SHA256(
  canonical_symbol,
  provider_symbol,
  normalized_timeframe,
  broker_timezone_policy,
  completed_candle_close_utc,
  ordered_selected_symbols,
  universe_set_hash,
  provider,
  source_id,
  source_snapshot_hash,
  data_revision,
  feature_schema_hash,
  model_version,
  formula_version
)
```

`H4` and `4H` are one identity. `Z`, `+00:00`, and an explicitly UTC-naive
provider timestamp resolve to one UTC timestamp. The authority does not use
the phone or laptop wall clock as a candle key.

## Settled target label

For a direction `d`, entry price `p`, target distance `k`, and future completed
candles after the entry candle:

```text
target_price = p + k       for BUY
target_price = p - k       for SELL

target_reached = 1 if a future completed high/low reaches target_price
                 0 otherwise
```

An unresolved future horizon is not a zero. A same-candle target/adverse-path
collision is `AMBIGUOUS_SAME_CANDLE_PATH` and is excluded from calibration.

## Legacy overlay

```text
Probability 100 Pip Move 4H
  = existing heuristic overlay using base probability,
    projected movement and 6H transition safety
```

This value remains for compatibility, but is explicitly disclosed as a legacy
heuristic. It cannot populate `Probability Target Reached`.

## Production utility

```text
expected_net_value =
    p_target * expected_MFE
  - (1 - p_target) * expected_MAE
  - spread_cost
  - slippage_cost
  - event_penalty
  - uncertainty_penalty
  - cvar_penalty
  - dependency_penalty
  - data_quality_penalty
  - stale_data_penalty
  - transition_penalty
```

Rows without a finite utility are kept visible but rank after usable rows and
cannot receive a production trade permission.

## Event gate

Event states are `PRE_EVENT`, `RELEASED_UNCONFIRMED`, `POST_EVENT_SHOCK`,
`ABSORBING`, `NORMAL`, and `DATA_UNAVAILABLE`. Missing actual/consensus data is
not converted to zero surprise or a safe state.

## Promotion gate

A model is promoted only if all are true:

```text
settled_sample_size >= minimum_settled_sample
out_of_sample = true
calibrated = true
no_lookahead = true
multiple_testing_registered = true
```

Otherwise the model status is `SHADOW_ONLY`.
