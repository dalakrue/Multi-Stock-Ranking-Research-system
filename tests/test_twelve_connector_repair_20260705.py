from __future__ import annotations

import sqlite3
import sys
import types
from pathlib import Path

import pandas as pd


if "streamlit" not in sys.modules:
    fake_streamlit = types.ModuleType("streamlit")
    fake_streamlit.session_state = {}
    sys.modules["streamlit"] = fake_streamlit


def test_twelve_secret_alias_and_explicit_override(monkeypatch):
    import core.secure_api_startup_20260619 as secure

    values = {("api_keys", "second_api"): "secret-key"}
    monkeypatch.setattr(secure, "_secret_path", lambda *parts: values.get(tuple(parts), ""))

    assert secure.resolve_api_key("twelve", {}) == "secret-key"
    assert secure.resolve_api_key(
        "twelve", {"twelve_api_key": "pasted-key", "twelve_api_key_source": "explicit"}
    ) == "pasted-key"
    assert secure.resolve_api_key(
        "twelve", {"twelve_api_key": "old-vault-key", "twelve_api_key_source": "vault"}
    ) == "secret-key"


def test_twelve_fetcher_loads_normalized_candles(monkeypatch):
    from core.connectors.data_parts import fetchers

    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {
                "status": "ok",
                "values": [
                    {"datetime": "2026-07-05 10:00:00", "open": "1.17", "high": "1.18", "low": "1.16", "close": "1.175"},
                    {"datetime": "2026-07-05 09:00:00", "open": "1.16", "high": "1.17", "low": "1.15", "close": "1.165"},
                ],
            }

    monkeypatch.setattr(fetchers.requests, "get", lambda *args, **kwargs: Response())
    frame, ok, message = fetchers.fetch_twelve("EURUSD", "valid-key", interval="1h", bars=600)

    assert ok is True
    assert isinstance(frame, pd.DataFrame)
    assert len(frame) == 2
    assert list(frame.columns) == ["time", "open", "high", "low", "close", "volume"]
    assert "connected" in message.lower()


def test_twelve_fetcher_reports_rejected_key(monkeypatch):
    from core.connectors.data_parts import fetchers

    class Response:
        status_code = 401
        headers = {}

        @staticmethod
        def json():
            return {"status": "error", "message": "invalid api key"}

    monkeypatch.setattr(fetchers.requests, "get", lambda *args, **kwargs: Response())
    frame, ok, message = fetchers.fetch_twelve("EURUSD", "bad-key", interval="1h", bars=5)

    assert frame is None
    assert ok is False
    assert "rejected" in message.lower()


def test_vault_save_and_connection_state_support_streamlit_secrets(tmp_path, monkeypatch):
    import core.connectors.credential_vault as vault

    vault_dir = tmp_path / "vault"
    monkeypatch.setattr(vault, "VAULT_DIR", vault_dir)
    monkeypatch.setattr(vault, "KEY_PATH", vault_dir / "vault.key")
    monkeypatch.setattr(vault, "DATA_PATH", vault_dir / "credentials.enc")
    db_path = tmp_path / "connector.sqlite3"

    saved = vault.save_credential("TWELVE_DATA", "dummy-key", db_path=db_path)
    assert saved["ok"] is True
    vault.mark_connection(
        "TWELVE_DATA", connected=True, configured=True, status="VALIDATED", db_path=db_path
    )

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT configured,connected,last_status,secret_fingerprint FROM api_connection_state WHERE provider='TWELVE_DATA'"
        ).fetchone()
    assert row[0:3] == (1, 1, "VALIDATED")
    assert row[3]


def test_sidebar_uses_real_state_machine_success_function():
    source = Path("ui/sidebar_fallback_panel.py").read_text(encoding="utf-8")
    assert "from core.connector_state_machine_20260621 import begin, fail, succeed" in source
    assert "import connect, fail" not in source


def test_market_connect_updates_connected_metric_state(monkeypatch):
    import core.app.refresh as refresh_module
    import ui.sidebar_fallback_panel as panel

    state = {
        "connector_mode": "twelve",
        "twelve_api_key": "valid-key",
        "twelve_api_key_source": "explicit",
        "multi_symbol_selected_20260701": ["EURUSD"],
        "multi_symbol_main_symbol_20260702": "EURUSD",
        "timeframe": "H1",
        "connector_bars": 600,
    }
    panel.st.session_state = state

    def fake_refresh(target, **kwargs):
        target["active_symbol_market_provenance_20260705"] = {
            "attempts": [{"provider": "TWELVE_DATA", "ok": True, "message": "validated"}]
        }
        target["connected"] = True
        target["source"] = "TWELVE_DATA"
        target["last_df"] = pd.DataFrame({"time": [pd.Timestamp("2026-07-05T10:00:00Z")], "open": [1.0], "high": [1.1], "low": [0.9], "close": [1.05], "volume": [0]})
        return {"ok": True, "status": "SUCCESS", "source": "TWELVE_DATA", "message": "candles loaded"}

    monkeypatch.setattr(refresh_module, "refresh_data", fake_refresh)
    monkeypatch.setattr("core.connectors.credential_vault.mark_connection", lambda *args, **kwargs: None)

    result = panel._central_market_connect(force=False)

    assert result["ok"] is True
    assert state["market_connector_20260621_state"] == "CONNECTED"
    assert state["twelve_data_connected"] is True
    assert state["market_connector_saved_profile_20260702"]["main_symbol"] == "EURUSD"
