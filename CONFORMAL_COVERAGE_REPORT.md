# Conformal Coverage Report

## Classification

- Algorithm implementation: **SHADOW_ONLY**
- Production coverage validation: **INSUFFICIENT_HISTORY**

A ridge return model is fitted on chronological training rows. Absolute residuals from the purged validation block define a finite-sample marginal conformal quantile. Coverage, lower-tail misses and upper-tail misses are evaluated only on the untouched chronological test block. Adaptive alpha is stored as monitoring evidence.

The implementation explicitly describes the interval as **marginal** OOS coverage and does not claim conditional coverage by symbol/regime/session. Separate subgroup calibration remains unavailable until each subgroup has enough immutable observations.
