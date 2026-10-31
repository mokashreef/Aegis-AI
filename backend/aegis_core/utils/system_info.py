"""
Aegis AI - Windows System Telemetry & Environment Inspector.
"""

import platform
import sys
from typing import Any, Dict
import psutil


def get_system_telemetry() -> Dict[str, Any]:
    """Collects comprehensive local Windows hardware and environment metrics."""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    telemetry = {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.architecture()[0],
            "machine": platform.machine(),
            "node": platform.node(),
        },
        "python": {
            "version": sys.version.split()[0],
            "executable": sys.executable,
        },
        "cpu": {
            "physical_cores": psutil.cpu_count(logical=False) or 1,
            "logical_cores": psutil.cpu_count(logical=True) or 1,
            "usage_percent": psutil.cpu_percent(interval=0.1),
        },
        "memory": {
            "total_bytes": mem.total,
            "available_bytes": mem.available,
            "used_bytes": mem.used,
            "percent_used": mem.percent,
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent_used": disk.percent,
        },
    }
    return telemetry

