"""
Aegis AI - Production Validation Benchmark: Desktop Experience.
Empirically measures RAM, CPU, launch latency, hook latency, and multi-monitor resolution.
"""

import json
import os
from pathlib import Path
import time
import psutil
from aegis_core.desktop.hotkey import GlobalHotkeyManager
from aegis_core.desktop.window import get_active_monitor_bounds

EVIDENCE_DIR = Path(".github/validation_evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def benchmark_desktop():
    results = {}
    proc = psutil.Process(os.getpid())

    # 1. Multi-monitor resolution latency
    t0 = time.perf_counter()
    iterations = 100
    for _ in range(iterations):
        bounds = get_active_monitor_bounds()
    t_bounds = (time.perf_counter() - t0) / iterations * 1000.0
    results["monitor_bounds"] = {
        "latency_ms": round(t_bounds, 3),
        "detected_bounds": bounds,
        "success": bool(bounds.get("width", 0) > 0 and bounds.get("height", 0) > 0),
    }

    # 2. Global Hotkey Manager start/stop lifecycle
    hotkey_mgr = GlobalHotkeyManager()
    t0 = time.perf_counter()
    started = hotkey_mgr.start()
    t_start = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    stopped = hotkey_mgr.stop()
    t_stop = (time.perf_counter() - t0) * 1000.0

    results["hotkey_lifecycle"] = {
        "hook_type": "WH_KEYBOARD_LL (Native Win32)",
        "start_latency_ms": round(t_start, 2),
        "stop_latency_ms": round(t_stop, 2),
        "started_cleanly": started,
        "stopped_cleanly": stopped,
    }

    # 3. Memory & CPU footprint
    mem_info = proc.memory_info()
    cpu_percent = proc.cpu_percent(interval=0.1)

    results["resource_footprint"] = {
        "rss_memory_mb": round(mem_info.rss / (1024 * 1024), 2),
        "vms_memory_mb": round(mem_info.vms / (1024 * 1024), 2),
        "cpu_percent": cpu_percent,
        "pid": proc.pid,
    }

    # 4. Save evidence
    evidence_file = EVIDENCE_DIR / "section1_desktop_experience.json"
    evidence_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    benchmark_desktop()
