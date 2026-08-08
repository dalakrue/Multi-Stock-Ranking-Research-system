import pandas as pd


def test_full_snapshot_zip_contains_expected_files():
    from core.field10_unified_authority_20260709 import build_unified_field10_authority, full_snapshot_zip_bytes
    import zipfile, io
    state = {"canonical_selected_symbols":["EURUSD"], "selected_timeframe":"H4"}
    build_unified_field10_authority(state, source_frame=pd.DataFrame([{"Symbol":"EURUSD","Rows":600,"Less-Risky Bias":"BUY"}]), persist=False)
    data = full_snapshot_zip_bytes(state)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
    assert "field10_unified_rank.csv" in names
    assert "dinner_research_evidence.csv" in names
    assert "snapshot_identity.json" in names
