# Read This First

This delivery implements the requested resource-controlled multi-symbol routing.

Start with:

1. `IMPLEMENTATION_REPORT.md`
2. `TEST_REPORT.md`
3. `TEN_ADVANCED_QUANT_RESEARCH_PAPERS.md`
4. `DETAILED_COMMAND.md`

Main behavior:

- Main symbol: Fields 1–9 + AI in Quick; Fields 1–9 + thesis + AI in Full.
- Secondary symbols: Fields 1–3 + Field 10 only.
- Top Lunch selector: switches cached Fields 1–3 + Field 10 data without an API call.
- Non-Lunch pages: restore the main-symbol canonical generation.
- Connect Once: reuses identical saved settings; Refresh Main Feed forces a new request.

No raw API key, bridge token, runtime SQLite database, pickle cache, `__pycache__` or `.pytest_cache` is intended to be included in the packaged ZIP.
