# Ranking Formula Registry

## Production authority

Existing protected Field 10 ranking formulas and immutable daily/hourly snapshots remain the production baseline. This repair does not alter their weights or decisions.

## Existing shadow research

The repository contains versioned shadow modules for regime probabilities, calibration, conformal intervals, drift/change detection, covariance/dependence, tail risk, candidate utility and promotion governance. Shadow outputs cannot publish a production decision.

## Repair-specific controls

- provider selection is operational routing, not a rank feature;
- partial-history coverage is a transparent quality/reliability input;
- staleness and provider fallback remain visible provenance;
- publication completeness is not a rank score;
- missing evidence may degrade a row but cannot be imputed from another symbol.

Any future rank-utility version must declare component names, transformations, weights, clipping, missing-value policy, benchmark, validation cutoff and promotion state before use.
