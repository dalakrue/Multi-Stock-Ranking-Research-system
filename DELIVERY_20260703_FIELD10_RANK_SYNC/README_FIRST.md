# Deploy and verify

1. Deploy the complete project folder.
2. Keep `app.py` as the Streamlit entry point.
3. Open Settings and choose the ordered multi-symbol universe.
4. Press **Run Calculation + Open Lunch**.
5. In Lunch, use **Lunch Symbol Connector — Fields 1–3 + Fields 10–11** to load a completed symbol.
6. Open Field 10 and confirm the Today First rank table contains:
   - Transition Risk 24H
   - Expected Return 12H (%)
7. Open `Legacy / Diagnostics — Previous Field 10 Surfaces` only for non-ranking audit details.
8. Confirm the connector caption reports `Database migration/sync: PASS`.
