# Streamlit Cloud Deployment Instructions

## Main file

Use **`app.py`** as the Streamlit Cloud main file.

## Required repository settings

1. Upload the complete extracted project to a private GitHub repository.
2. In Streamlit Community Cloud, create a new app from that repository.
3. Set **Main file path** to `app.py`.
4. Keep `runtime.txt` in the repository root. It contains `python-3.12`.
5. Keep `requirements.txt` in the repository root.
6. Do not add the Windows-only `MetaTrader5` package to the Linux Cloud requirements. MT5 remains an optional external/bridge provider.

## Secrets

Open **App settings → Secrets** and enter only the connectors you use, following `.streamlit/secrets.example.toml`. Do not commit real API keys to GitHub.

Typical sections are the existing Twelve Data, Finnhub, OpenRouter/AI and optional MT5 bridge values already documented by the project example file.

## First deployment

1. Deploy the app.
2. Open the logs and confirm dependency installation finishes under Python 3.12.
3. Confirm the log starts `app.py` and does not route deployment through `adx_dashpoard.py`.
4. At startup, the timeframe-identity migration runs automatically and creates a one-time backup when needed.
5. Enter as Guest or authenticate using the existing app flow.
6. Settings should be the initial application route.
7. Verify saved connector states or enter credentials and use the existing save/validate/connect control.
8. Select the Top 10 Currency Pairs and H4.
9. Click `Super Quick Calculation + Open Lunch` once.
10. Do not close the browser while a live provider is actively supplying batches. The durable state machine saves each stage, and an interrupted rerun resumes incomplete/failed symbols rather than recomputing completed children.
11. In Lunch, verify Field 10 first, then use the explicit `Load Selected Symbol` button in Field 1 and Field 2.

## Database persistence note

Streamlit Community Cloud's local filesystem is not guaranteed to be permanent across redeployments. The package preserves the existing SQLite design, but production-grade durable retention should mount or synchronize the database to an external persistent store. Do not treat a redeployable local SQLite file as a guaranteed long-term backup.

## Health command for local verification

```bash
python -m pip install -r requirements.txt
streamlit run app.py --server.headless true
```

Then open the URL printed by Streamlit.
