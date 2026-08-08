from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.instant_run_engine_20260705 import (
    ENGINE_RUNNING_KEY,
    JOB_KEY,
    current_job,
    enqueue_run,
    execute_queued_job,
    progress_rows,
    recover_stale_job,
)


def test_enqueue_acknowledges_immediately_and_blocks_duplicate_active_click(tmp_path: Path):
    journal = tmp_path / "job.json"
    state = {}
    first = enqueue_run(
        state, scope="LUNCH_CORE", symbols=["EUR/USD", "USDJPY"], timeframe="H1",
        start_delay_seconds=0, journal_path=journal,
    )
    second = enqueue_run(
        state, scope="FULL", symbols=["GBPUSD"], timeframe="H1",
        start_delay_seconds=0, journal_path=journal,
    )
    assert first["status"] == "QUEUED"
    assert first["symbols"] == ["EURUSD", "USDJPY"]
    assert first["scope"] == "LUNCH_CORE"
    assert second["job_id"] == first["job_id"]
    assert second["duplicate_click_ignored"] is True
    assert journal.is_file()


def test_execute_streams_symbol_progress_and_completes(tmp_path: Path):
    journal = tmp_path / "job.json"
    state = {}
    enqueue_run(
        state, scope="QUICK", symbols=["EURUSD", "USDJPY"], timeframe="H1",
        start_delay_seconds=0, journal_path=journal,
    )

    def runner(job, publish):
        publish({
            "overall_percent": 50,
            "current_symbol": "EURUSD",
            "current_stage": "Calculated",
            "symbols": {
                "EURUSD": {"status": "COMPLETED", "percent": 100, "stage": "Done"},
                "USDJPY": {"status": "RUNNING", "percent": 20, "stage": "Calculating"},
            },
        })
        return {
            "status": "COMPLETED",
            "result_payload": {
                "ok": True,
                "status": "COMPLETED",
                "parent_run_id": "MS-1",
                "completed_symbols": 2,
                "failed_symbols": 0,
            },
        }

    final = execute_queued_job(state, runner, journal_path=journal)
    assert final and final["status"] == "COMPLETED"
    assert final["progress_percent"] == 100
    assert final["result_summary"]["result_run_id"] == "MS-1"
    assert ENGINE_RUNNING_KEY not in state
    rows = progress_rows(final)
    assert [row["Symbol"] for row in rows] == ["EURUSD", "USDJPY"]
    assert rows[0]["Status"] == "COMPLETED"


def test_failed_symbol_batch_is_partial_not_blank(tmp_path: Path):
    state = {}
    enqueue_run(state, scope="QUICK", symbols=["EURUSD", "USDJPY"], start_delay_seconds=0, journal_path=tmp_path / "job.json")

    def runner(job, publish):
        publish({
            "overall_percent": 100,
            "current_symbol": "USDJPY",
            "current_stage": "Saved with validation warnings",
            "symbols": {
                "EURUSD": {"status": "COMPLETED", "percent": 100, "stage": "Done"},
                "USDJPY": {"status": "FAILED", "percent": 100, "stage": "Failed", "error": "provider empty"},
            },
        })
        return {
            "status": "COMPLETED",
            "result_payload": {
                "ok": True,
                "status": "PARTIAL",
                "completed_symbols": 1,
                "failed_symbols": 1,
            },
        }

    final = execute_queued_job(state, runner, journal_path=tmp_path / "job.json")
    assert final and final["status"] == "PARTIAL"
    rows = progress_rows(final)
    assert len(rows) == 2
    assert rows[1]["Error"] == "provider empty"


def test_stale_running_job_recovers_after_restart(tmp_path: Path):
    journal = tmp_path / "job.json"
    state = {}
    job = enqueue_run(state, scope="QUICK", symbols=["EURUSD"], start_delay_seconds=0, journal_path=journal)
    job["status"] = "RUNNING"
    job["updated_at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    state[JOB_KEY] = job
    # Persist through a normal queue call is intentionally not used here; the
    # session state itself is enough to exercise stale recovery.
    recovered = recover_stale_job(state, stale_after_seconds=30, journal_path=journal)
    assert recovered and recovered["status"] == "QUEUED"
    assert recovered["recovery_count"] == 1
    assert current_job(state, journal_path=journal)["job_id"] == job["job_id"]


def test_super_quick_service_uses_lunch_core_scope():
    source = Path("core/super_quick_service_20260704.py").read_text(encoding="utf-8")
    assert 'state["settings_calculation_scope_20260625"] = "LUNCH_CORE"' in source
    assert 'scope="LUNCH_CORE"' in source


def test_progress_is_monotonic_across_provider_and_symbol_phases(tmp_path: Path):
    from core.instant_run_engine_20260705 import publish_progress

    journal = tmp_path / "job.json"
    state = {}
    enqueue_run(state, scope="QUICK", symbols=["EURUSD"], start_delay_seconds=0, journal_path=journal)
    publish_progress(state, {"overall_percent": 18, "current_stage": "Market data ready"}, journal_path=journal)
    job = publish_progress(state, {"overall_percent": 0, "current_stage": "Starting symbol calculation"}, journal_path=journal)
    assert job and job["progress_percent"] == 18


def test_guest_journals_are_isolated_but_account_journal_is_stable():
    from core.instant_run_engine_20260705 import journal_path_for_state

    guest_a: dict[str, object] = {"new7_auth_email": "Guest"}
    guest_b: dict[str, object] = {"new7_auth_email": "Guest"}
    account_a = {"new7_auth_email": "trader@example.com"}
    account_b = {"new7_auth_email": "trader@example.com"}
    assert journal_path_for_state(guest_a) != journal_path_for_state(guest_b)
    assert journal_path_for_state(account_a) == journal_path_for_state(account_b)


def test_terminal_run_releases_all_locks_and_next_mode_can_start(tmp_path: Path):
    from core.instant_run_engine_20260705 import RUN_LOCK_KEYS

    journal = tmp_path / "job.json"
    state = {
        "settings_one_click_running_20260624": True,
        "multi_symbol_run_in_progress_20260701": True,
    }
    enqueue_run(state, scope="LUNCH_CORE", symbols=["EURUSD"], start_delay_seconds=0, journal_path=journal)

    def runner(job, publish):
        return {"status": "COMPLETED", "result_payload": {"ok": True, "status": "COMPLETED"}}

    final = execute_queued_job(state, runner, journal_path=journal)
    assert final and final["status"] == "COMPLETED"
    assert all(key not in state for key in RUN_LOCK_KEYS)
    next_job = enqueue_run(state, scope="FULL", symbols=["USDJPY"], start_delay_seconds=0, journal_path=journal)
    assert next_job["scope"] == "FULL"
    assert next_job["status"] == "QUEUED"
    assert not next_job.get("duplicate_click_ignored")
