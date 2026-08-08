# Multi-Stock Ranking Research System

Release: 2026-07-29  
Entry point: `app.py`  
Runtime target: Python 3.12

## Outcome

This release turns the many top-level application tabs into one primary
`Multi-Stock Ranking Research System` page. Nothing important was deleted:
the original Settings, Lunch, Morning, Dinner, Research, Data Visualization,
Other, and AI renderers remain in the project.

The unified page contains seven lazy inner workspaces:

1. Ranking Command Center
2. Multi-Stock Ranking Data Analysis
3. Multi-Stock Ranking Data Mining
4. Multi-Stock Ranking NLP
5. Multi-Stock Ranking AI Assistant
6. System Controls & Run
7. Preserved Original Workspaces

The AI Assistant and Research logic are not merged. They share one page and
one frozen publication identity, but continue to run through their original
modules and evidence contracts.

## First run

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Linux/macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Keep API keys in Streamlit Secrets or the existing server-side Settings
inputs. Do not store keys in source files.

## End-to-end workflow

1. Open `System Controls & Run`.
2. Choose the timeframe.
3. Select up to ten symbols in each of the three selectors.
4. Load the combined canonical universe, up to 30 unique symbols.
5. Run Super Quick, Quick, or Full Calculation.
6. Return to `Ranking Command Center`.
7. Review Production Rank, Research Rank, Trade Permission, trust status,
   data quality, uncertainty, event risk, and no-trade reason.
8. Use Data Analysis, Data Mining, NLP, and AI only against that frozen run.
9. Export the ranking CSV or the thesis evidence JSON when required.

The default 10/10/10 profile includes DXY in Selector 3. Provider aliases are
supported, but the system still reports an honest load failure when the
configured provider or account does not supply genuine DXY candles.

## Ranking governance

- `Production Rank` remains the original Field 10 authority.
- `Research Rank` is a separate, read-only thesis rank.
- Research outputs cannot overwrite Production Rank or Trade Permission.
- A BUY/SELL bias is not treated as permission to enter.
- If no symbol passes both production permission and the research trust gate,
  the system explicitly says that no symbol is currently approved.
- Missing, stale, conflicting, or low-quality evidence reduces trust and
  produces a visible no-trade reason.

When the required Field 11 inputs are available, the research layer calculates:

```text
Expected Net Value =
    p(target) × Expected MFE
  − (1 − p(target)) × |Expected MAE|
  − transaction cost
  − event penalty
  − uncertainty penalty
```

When those inputs are incomplete, it uses the already-published Field 10 Net
Expected Value and labels that source. It does not invent missing values.

## Research workspaces

### Multi-Stock Ranking Data Analysis

- descriptive statistics and dispersion
- grouping, filtering, and sorting
- missing-data completeness
- correlation matrix
- z-score standardization
- min-max normalization
- quartile discretization
- IQR outlier review
- exploratory permutation comparison

### Multi-Stock Ranking Data Mining

- standardized K-nearest-symbol peers
- KMeans cross-sectional clustering
- Isolation Forest or standardized anomaly fallback
- Random Forest permission-surrogate importance when sample support is adequate
- published model-validation evidence

The surrogate and anomaly models are research explanations, not new production
trade signals.

### Multi-Stock Ranking NLP

- symbol/entity matching
- sentiment and relevance
- freshness and absorption
- news/technical conflict
- topic classification
- token and bigram frequency
- an explicit evidence-reliability score

Opening this workspace does not make a new API request. It reads the saved
Field 12 publication.

### Multi-Stock Ranking AI Assistant

The Assistant can answer saved-evidence questions such as:

- What stock or symbol is best to enter now?
- Compare EURUSD and XAUUSD.
- Why is DXY ranked here?
- Why is this symbol blocked?
- What is the current data quality?
- Explain portfolio risk, CVaR, correlation, spread, or event risk.
- Explain Field 1 through Field 13.
- What symbols are loaded?
- Explain the ranking methodology, validation, NLP, or system health.

For multi-symbol entry questions, Field 10 is authoritative. The Assistant
returns an approved symbol only when saved Trade Permission supports it;
otherwise it gives the highest-ranked watch symbol and clearly says that no
entry is approved.

## Thesis and interview framing

The included method registry connects the implementation to:

- Hamilton/Markov regime switching
- ARCH/GARCH volatility evidence
- DCC and Ledoit-Wolf correlation shrinkage
- CVaR/Expected Shortfall
- conformal uncertainty
- BOCPD/drift controls
- similar-path MFE/MAE
- calibrated probabilities
- chronological walk-forward testing
- purge and embargo
- PBO/CSCV and Deflated Sharpe
- White Reality Check, SPA, Model Confidence Set, Diebold-Mariano, and
  Giacomini-White comparisons

Methods are marked as implemented, published evidence, optional, or requiring
per-run evidence. A method name alone is never presented as proof of superior
performance.

Suggested interview summary:

> This is a deterministic multi-symbol decision-support system. A Settings run
> freezes one canonical generation. Field 10 provides the production rank;
> Field 3 adds multi-scale regime evidence; Field 11 contributes similar-path
> MFE/MAE; Field 12 contributes symbol-specific NLP and event risk. A separate
> research layer audits the rank, uncertainty, data quality, and no-trade
> reasons without changing the production decision.

## Scientific limitations

- This is decision support, not a guarantee of profit or investment advice.
- Cross-sectional clustering and the permutation snapshot are exploratory.
- Causal or predictive claims require settled, chronological out-of-sample
  evidence.
- Provider coverage and execution costs differ by broker and account.
- Live entry decisions must be rechecked against candle freshness, spread,
  slippage, liquidity, and event risk.
- The final holdout must remain untouched when reporting thesis results.

## Verification

The release includes focused acceptance tests in:

- `tests/test_multi_stock_thesis_system_20260729.py`
- `tests/test_multisymbol_global_repair_20260722.py`
- `tests/test_provider_selector_capacity_20260708.py`

The ZIP integrity test should also be run after packaging.
