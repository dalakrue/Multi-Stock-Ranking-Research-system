# Release Validation — Multi-Stock Ranking Research System

Date: 2026-07-29

## Passed checks

- full Python syntax compilation for `core`, `ui`, `tabs`, `pages`, `tests`,
  and the three application entry points
- master ranking preserves Production Rank
- thesis expected-net-value calculation and source label
- multi-symbol Data Analysis and NLP outputs
- AI best-entry answer uses Field 10 authority
- AI comparison and rank explanation
- equity ticker parsing (`AAPL` versus `MSFT`)
- FX slash parsing (`EUR/USD` versus `DXY`)
- all legacy top-level routes normalize to one unified page
- Research/NLP legacy state migrates into the correct inner workspace
- three selector limits are 10/10/10
- canonical and Field 10 research limits are 30
- default universe contains 30 unique symbols
- DXY is included and resolves through the provider-symbol boundary
- Load All executes Selector 1, Selector 2, and Selector 3 workers
- original global multi-symbol repair acceptance checks remain green
- unified page imports through the application registry

## Deployment-dependent checks

Live market-provider calls, broker-specific DXY coverage, and visual browser
rendering require the deployment credentials and the packages in
`requirements.txt`. The runtime must keep reporting missing or invalid live
data rather than generating synthetic ranking evidence.

## Reproducible commands

```bash
python -m compileall -q core ui tabs pages tests app.py main.py adx_dashpoard.py
streamlit run app.py
```

After packaging:

```bash
unzip -t Multi_Stock_Ranking_Research_System_Thesis_Ready_20260729.zip
```
