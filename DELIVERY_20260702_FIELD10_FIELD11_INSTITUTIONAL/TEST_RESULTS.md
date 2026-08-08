# Test Results

## Deterministic segmented run

All **295 collected tests passed** in four isolated process segments:

| Segment | Scope | Result |
|---|---|---|
| A | First 11 top-level modules | 108 passed |
| B | Field 10 daily through Field 3 lifecycle modules | 102 passed, 6 existing sklearn warnings |
| C | Navigation/time-sync/routing/remaining legacy modules | 78 passed, 3 existing sklearn warnings |
| D | `research_quant/tests` | 7 passed |
| **Total** | **All collected tests** | **295 passed** |

## Other verification

- `compileall`: PASS for `app.py`, `adx_dashpoard.py`, `main.py`, `core`, `ui`, `tabs`, `lunch`, `services`, `tests`.
- Python imports: `app` and `adx_dashpoard` PASS.
- Streamlit startup: PASS.
- `/_stcore/health`: `ok`.

## Monolithic-run disclosure

The one-process `pytest -q` run reached 70% with no assertion failure, then stalled while constructing the existing module-scoped Field 3 regime fixture after extensive prior state accumulation. The same Field 3 module passes in segment B. Therefore the delivery reports the reproducible segmented result, not a false monolithic PASS.

Test interpreter: Python 3.13.5. Deployment target in `runtime.txt`: Python 3.12. Exact Python 3.12 execution was not available in this container.
