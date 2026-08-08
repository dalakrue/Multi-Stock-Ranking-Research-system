# Deploy the repaired project

1. Delete the old repository contents or replace them with the complete contents of this repaired folder.
2. Commit every file, including `core/canonical_runtime_20260617_standalone.py` and all compatibility modules.
3. In Streamlit Community Cloud, set the main file to `app.py`.
4. Confirm the branch is `main` and Python resolves to 3.12.
5. Reboot the app from **Manage app**. A normal reboot is enough; no database deletion is required.

Do not upload a nested folder inside another repository folder. `app.py`, `requirements.txt`, `runtime.txt`, `core/`, `tabs/`, `ui/`, and `lunch/` must all be at the repository root.
