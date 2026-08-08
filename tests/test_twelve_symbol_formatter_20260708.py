from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# The project runtime has Streamlit, but the smoke-test container used for this
# repair may not. Stub only the import-time object needed by connector utils.
sys.modules.setdefault("streamlit", types.SimpleNamespace(session_state={}, secrets={}))

from core.connectors.data_parts.utils import _twelve_symbol


def test_twelve_symbol_formats_selector_2_crosses_with_slash():
    assert _twelve_symbol("NZDUSD") == "NZD/USD"
    assert _twelve_symbol("EURCHF") == "EUR/CHF"
    assert _twelve_symbol("EURAUD") == "EUR/AUD"
    assert _twelve_symbol("EURCAD") == "EUR/CAD"
    assert _twelve_symbol("EURNZD") == "EUR/NZD"
    assert _twelve_symbol("GBPCHF") == "GBP/CHF"


def test_twelve_symbol_preserves_existing_special_aliases():
    assert _twelve_symbol("XAUUSD") == "XAU/USD"
    assert _twelve_symbol("BTCUSD") == "BTC/USD"
    assert _twelve_symbol("NAS100") == "NDX"
