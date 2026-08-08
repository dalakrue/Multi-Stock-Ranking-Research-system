# Field 10 Formula and Threshold Registry

## Authority and versions

- Production authority: `field10_daily_snapshot`, `field10_daily_snapshot_symbol`
- Candidate model: `field10-institutional-shadow-20260704-v1`
- Feature version: `field10-institutional-features-20260704-v1`
- Formula version: `field10-hierarchical-utility-20260704-v1`
- Threshold version: `field10-promotion-gates-20260704-v1`
- Calibration version: `purged-walk-forward-calibration-20260704-v1`
- Conformal version: `adaptive-marginal-conformal-20260704-v1`

## Eligibility

Candidate utility is NULL unless exact symbol identity, verified source identity/hash, exact completed H1 cutoff and 600 completed H1 rows pass. Blocked symbols remain displayed.

## Candidate utility

```text
WeightedNetEV = 0.15*NetEV_1H + 0.35*NetEV_6H + 0.30*NetEV_12H + 0.20*NetEV_24H

Utility = WeightedNetEV
          - 0.50*max_abs_CVaR
          - 0.15*transition_risk_6H
          - 0.10*mean_conformal_interval_width
          - 0.10*structural_break_strength
          - 0.10*duplicate_exposure_penalty
          - 0.10*data_quality_penalty
```

Net EV is NULL when provider spread/slippage evidence is unavailable.

## Reliability

Weighted geometric mean of available components; missing values are not imputed:

| Component | Weight |
|---|---:|
| Calibration reliability | 0.16 |
| Conformal coverage reliability | 0.13 |
| Sample adequacy | 0.12 |
| Data completeness | 0.11 |
| Source identity reliability | 0.14 |
| Regime stability | 0.10 |
| Structural stability | 0.09 |
| Rank stability | 0.05 |
| Feature availability | 0.06 |
| Outcome settlement completeness | 0.04 |

## Research thresholds

- Production window: latest 600 completed H1 candles.
- Minimum model rows: 120 labelled rows.
- Minimum calibration residuals: 60.
- Minimum conformal residuals: 60.
- Minimum aligned covariance rows: 80.
- Conformal target coverage: 90% marginal coverage.
- Structural entry block candidate: break strength ≥ 0.75 and post-break H1 count < 96.
- Purge and embargo: equal to prediction horizon.

These are registered research thresholds, not proof of production validity. Promotion remains blocked until immutable OOS evidence supports all gates.
