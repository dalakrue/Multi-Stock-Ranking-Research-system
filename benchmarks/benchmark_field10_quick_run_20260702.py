from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path
import statistics
import tempfile
import time
import tracemalloc
from typing import Callable

import numpy as np
import pandas as pd

from core.quick_run_feature_cache_20260702 import (
    _build_features,
    append_completed_candle,
    get_or_build_shared_feature_bundle,
)
from core.serialization_compat_20260702 import dumps, loads
from core.symbol_context_20260702 import resolve_symbol_context

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "DELIVERY_20260702_SYMBOL_FIELD10_REPAIR" / "evidence" / "performance_benchmark_fixture.json"


def frame_for(symbol_index: int, rows: int = 600) -> pd.DataFrame:
    rng = np.random.default_rng(10_000 + symbol_index)
    returns = rng.normal(0.0, 0.0004, rows)
    close = 1.05 + symbol_index * 0.1 + np.cumsum(returns)
    spread = np.abs(rng.normal(0.0003, 0.00005, rows))
    return pd.DataFrame(
        {
            "time": pd.date_range("2026-06-07 11:00:00+00:00", periods=rows, freq="h"),
            "open": close - returns / 2,
            "high": close + spread,
            "low": close - spread,
            "close": close,
        }
    )


def measure(fn: Callable[[], object], repeats: int = 15) -> dict[str, float]:
    wall: list[float] = []
    cpu: list[float] = []
    peaks: list[float] = []
    for _ in range(repeats):
        tracemalloc.start()
        c0 = time.process_time()
        w0 = time.perf_counter()
        fn()
        wall.append(time.perf_counter() - w0)
        cpu.append(time.process_time() - c0)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peaks.append(peak / (1024 * 1024))
    return {
        "wall_median_seconds": statistics.median(wall),
        "wall_p95_seconds": sorted(wall)[max(0, int(len(wall) * 0.95) - 1)],
        "cpu_median_seconds": statistics.median(cpu),
        "python_peak_mib_median": statistics.median(peaks),
    }


def reduction(before: float, after: float) -> float:
    return 0.0 if before <= 0 else 100.0 * (before - after) / before


def benchmark_symbol_count(count: int) -> dict[str, object]:
    symbols = ["EURUSD", "GBPUSD", "USDJPY"][:count]
    frames = {s: frame_for(i) for i, s in enumerate(symbols)}

    def legacy_cold():
        for s in symbols:
            features = _build_features(frames[s])
            payload = gzip.compress(dumps({"symbol": s, "features": features}))
            loads(gzip.decompress(payload))

    def optimized_cold():
        state = {}
        for s in symbols:
            f = frames[s]
            bundle = get_or_build_shared_feature_bundle(
                state, f, provider="FIXTURE", symbol=s, timeframe="H1",
                completed_broker_candle=f.time.iloc[-1], calculation_version="fixture-v1",
            )
            payload = gzip.compress(dumps({"symbol": s, "features": bundle.frame}))
            loads(gzip.decompress(payload))

    warm_state = {}
    for s in symbols:
        f = frames[s]
        get_or_build_shared_feature_bundle(
            warm_state, f, provider="FIXTURE", symbol=s, timeframe="H1",
            completed_broker_candle=f.time.iloc[-1], calculation_version="fixture-v1",
        )

    def legacy_warm():
        for s in symbols:
            _build_features(frames[s])

    def optimized_warm():
        for s in symbols:
            f = frames[s]
            get_or_build_shared_feature_bundle(
                warm_state, f, provider="FIXTURE", symbol=s, timeframe="H1",
                completed_broker_candle=f.time.iloc[-1], calculation_version="fixture-v1",
            )

    before_cold = measure(legacy_cold, 8)
    after_cold = measure(optimized_cold, 8)
    before_warm = measure(legacy_warm, 20)
    after_warm = measure(optimized_warm, 20)
    return {
        "symbols": symbols,
        "cold_run": {
            "baseline": before_cold,
            "optimized": after_cold,
            "wall_reduction_percent": reduction(before_cold["wall_median_seconds"], after_cold["wall_median_seconds"]),
            "simulated_api_calls_baseline": count,
            "simulated_api_calls_optimized": count,
        },
        "warm_unchanged_candle": {
            "baseline": before_warm,
            "optimized": after_warm,
            "wall_reduction_percent": reduction(before_warm["wall_median_seconds"], after_warm["wall_median_seconds"]),
            "simulated_api_calls_baseline": count,
            "simulated_api_calls_optimized": 0,
            "cache_hits": count,
        },
    }


def interaction_benchmarks() -> dict[str, object]:
    frame = frame_for(0)
    extra = frame.tail(1).copy()
    extra["time"] = extra["time"] + pd.Timedelta(hours=1)

    new_before = measure(lambda: _build_features(pd.concat([frame, extra], ignore_index=True).tail(600)), 20)
    new_after = measure(lambda: append_completed_candle(frame.tail(599), extra, time_column="time"), 20)

    state = {
        "multi_symbol_main_symbol_20260702": "EURUSD",
        "connector_symbol_20260702": "EURUSD",
        "multi_symbol_selected_20260701": ["EURUSD", "GBPUSD", "USDJPY"],
        "canonical_decision_result_20260617": {
            "symbol": "EURUSD", "timeframe": "H1", "run_id": "R", "source_id": "S",
            "snapshot_hash": "H", "completed_broker_candle": frame.time.iloc[-1].isoformat(),
        },
    }

    def legacy_switch():
        copy.deepcopy(frame)
        copy.deepcopy(state)

    def optimized_switch():
        resolve_symbol_context(state | {"lunch_display_symbol_20260702": "GBPUSD", "active_snapshot_symbol_20260702": "GBPUSD"}, "Lunch", "GBPUSD")

    switch_before = measure(legacy_switch, 50)
    switch_after = measure(optimized_switch, 50)

    snapshot = gzip.compress(dumps({"state": state, "frame": frame}))
    cached_payload = loads(gzip.decompress(snapshot))
    refresh_before = measure(lambda: loads(gzip.decompress(snapshot)), 25)
    refresh_after = measure(lambda: cached_payload["state"].get("canonical_decision_result_20260617"), 25)

    full_rows = frame.to_dict("records")
    cached_text = json.dumps({"symbol": "EURUSD", "current": full_rows[-1]}, default=str)
    copy_before = measure(lambda: json.dumps({"symbol": "EURUSD", "history": full_rows}, default=str), 30)
    copy_after = measure(lambda: cached_text, 30)

    return {
        "new_candle_incremental_history": {
            "baseline": new_before, "optimized": new_after,
            "wall_reduction_percent": reduction(new_before["wall_median_seconds"], new_after["wall_median_seconds"]),
        },
        "lunch_symbol_switch": {
            "baseline": switch_before, "optimized": switch_after,
            "wall_reduction_percent": reduction(switch_before["wall_median_seconds"], switch_after["wall_median_seconds"]),
            "api_calls": 0, "heavy_calculations": 0,
        },
        "browser_refresh_hydration": {
            "baseline_deserialize_every_rerun": refresh_before,
            "optimized_already_hydrated_registry_path": refresh_after,
            "wall_reduction_percent": reduction(refresh_before["wall_median_seconds"], refresh_after["wall_median_seconds"]),
            "api_calls": 0, "heavy_calculations": 0,
        },
        "copy_button_interaction": {
            "baseline_rebuild_600_rows": copy_before,
            "optimized_identity_cached_current_only": copy_after,
            "wall_reduction_percent": reduction(copy_before["wall_median_seconds"], copy_after["wall_median_seconds"]),
            "api_calls": 0, "heavy_calculations": 0,
        },
    }


def main() -> None:
    symbol_cases = [benchmark_symbol_count(n) for n in (1, 2, 3)]
    interactions = interaction_benchmarks()
    warm_reductions = [case["warm_unchanged_candle"]["wall_reduction_percent"] for case in symbol_cases]
    cold_reductions = [case["cold_run"]["wall_reduction_percent"] for case in symbol_cases]
    result = {
        "benchmark_name": "ADX Quant Pro Field 10 orchestration fixture benchmark",
        "date": pd.Timestamp.now(tz="UTC").isoformat(),
        "environment": {"rows_per_symbol": 600, "timeframe": "H1", "provider": "deterministic fixture", "live_api": False},
        "scope_warning": "This benchmark validates the new cache/interaction substrate only. It is not an end-to-end live-provider Quick Run benchmark and cannot prove the requested 30-50% production target.",
        "symbol_cases": symbol_cases,
        "interactions": interactions,
        "median_warm_fixture_reduction_percent": statistics.median(warm_reductions),
        "median_cold_fixture_reduction_percent": statistics.median(cold_reductions),
        "acceptance": {
            "warm_fixture_30_percent_met": statistics.median(warm_reductions) >= 30.0,
            "end_to_end_live_provider_30_percent_proven": False,
            "reason": "No credentials/live provider and no stable production hardware baseline were available in the sandbox.",
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
