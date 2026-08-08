#!/usr/bin/env bash
set -euo pipefail
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m compileall -q .
PYTHONPATH=. pytest -q tests/test_full_multi_symbol_repair_20260702.py
PYTHONPATH=. pytest -q tests/test_field10_daily_snapshot_contract_20260702.py tests/test_field11_similar_path_simulator_20260702.py tests/test_field10_multi_symbol_20260701.py
streamlit run app.py
