# Calibration Report

## Classification

- Algorithm implementation: **SHADOW_ONLY**
- Production calibration result: **INSUFFICIENT_HISTORY**

## Method

For each symbol and 1H/6H/12H/24H target, features use only prior completed candles. A chronological 60/20/20 split is applied with purge and embargo equal to the horizon. The base probability model is fitted only on training data. Platt and isotonic calibrators are fitted on validation predictions and selected using validation log loss. Brier score, Brier skill against training prevalence, log loss, ECE, MCE and Brier reliability/resolution are measured on untouched test predictions.

## Evidence

Synthetic causal unit tests pass and verify split separation and bounded metrics. The uploaded production database has zero institutional settled outcomes and cannot support a trustworthy production calibration claim. Published calibrated probabilities must remain NULL or `INSUFFICIENT_SAMPLE` until adequate OOS evidence accumulates.
