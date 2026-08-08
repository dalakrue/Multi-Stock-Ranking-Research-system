# Field 10 Formula Dictionary

## Directional cost-adjusted return

For horizon `H` and raw future return `r_H`:

- BUY: `d_H = r_H - estimated_cost`
- SELL: `d_H = -r_H - estimated_cost`
- WAIT/unknown direction: no directional EV is asserted.

Costs are expressed in percentage-return units and are deducted before EV/probability calculations.

## Transition Risk 6H

Preferred empirical duration form:

`TransitionRisk_6H = 1 - P(regime survives next 6 completed H1 periods | current state, current age)`

Fallback Markov form:

`TransitionRisk_6H = 1 - (P^6)[s,s]`

The transition matrix is estimated from causal state labels with smoothing. Linear multiplication of 1H risk and scaling of 24H risk are prohibited.

## Expected Value 6H

`EV_6H = sum_i w_i * d_6H_i / sum_i w_i`

The implementation uses same-symbol, regime-conditioned historical analogues available strictly before the cutoff. Weights decrease with feature distance.

## CVaR and risk-adjusted EV

`CVaR95_6H = mean(losses in the worst 5% tail)`

`RiskAdjustedEV_6H = EV_6H - lambda_tail * CVaR95_6H`

Raw EV and risk-adjusted EV are stored separately.

## Probability of Profit

`P_Profit_H = P(d_H > 0 | completed-candle evidence)` for `H in {1,6,12}`.

## EV target

`EV_Target_H = max(abs(E[d_H]), minimum_economically_meaningful_move)`

## Probability of Reaching EV Target

`P_Reach_EV_H = P(d_H >= EV_Target_H)`

This is a threshold-exceedance probability, not the probability of exact equality to a continuous expected value.

## Observed 12H tick volume

`Observed_Tick_Volume_12H = sum(tick_volume over last 12 completed H1 candles)`

Source is explicitly stored as `BROKER_TICK_VOLUME` when available.

## Robust 12H volume z-score

`Volume_12H_Z = 0.67448975 * (V_12H - median(reference)) / MAD(reference)`

Comparable historical 12H rolling sums form the reference. A standard-deviation fallback is used only when MAD is zero.

## Unexpected-situation severity

Available shock signals produce a maximum normalized severity. Thresholds:

- `<40`: NORMAL
- `40–<70`: CAUTION
- `70–<90`: PROTECT
- `>=90`: BLOCK

BLOCK denies validation permission but preserves diagnostic publication.

## Missing evidence

When fewer than 100 normalized completed H1 rows exist, the module returns `INSUFFICIENT_VALID_EVIDENCE`. It does not fabricate a confident value.
