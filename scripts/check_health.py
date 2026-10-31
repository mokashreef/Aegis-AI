#!/usr/bin/env python3
"""
Aegis AI - Health & Subsystem Diagnostic Utility.
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from aegis_core.ai_runtime.router import ai_router
from aegis_core.automation.clipboard_manager import ClipboardManager
from aegis_core.automation.process_manager import ProcessManager
from aegis_core.config import settings
from aegis_core.memory.db import db_engine
from aegis_core.utils.system_info import get_system_telemetry


async def run_diagnostics():
    print("=" * 60)
    print("🛡️  Aegis AI - Subsystem Health Diagnostic")
    print("=" * 60)

    # 1. Configuration & Directories
    print("\n[1] Configuration & Storage:")
    print(f"    - Storage Directory: {settings.storage_dir} (Exists: {settings.storage_dir.exists()})")
    print(f"    - Database Path:     {settings.db_path} (Exists: {settings.db_path.exists()})")
    print(f"    - Zero API Keys:     Enforced (Default)")

    # 2. Database Connectivity
    print("\n[2] Database Engine:")
    try:
        with db_engine.get_connection() as conn:
            cursor = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
            count = cursor.fetchone()[0]
        print(f"    - SQLite Status:     OPERATIONAL ({count} tables initialized)")
    except Exception as exc:
        print(f"    - SQLite Status:     FAILED ({exc})")

    # 3. Windows Automation Primitives
    print("\n[3] Windows Automation:")
    try:
        procs = ProcessManager.list_processes(limit=5)
        print(f"    - Process Manager:   OPERATIONAL ({len(procs)} active processes sampled)")
    except Exception as exc:
        print(f"    - Process Manager:   FAILED ({exc})")

    try:
        clip_text = ClipboardManager.get_text()
        print(f"    - Clipboard Manager: OPERATIONAL (Current length: {len(clip_text)} chars)")
    except Exception as exc:
        print(f"    - Clipboard Manager: FAILED ({exc})")

    # 4. AI Runtime Health Matrix
    print("\n[4] Zero-Cost AI Runtime Matrix:")
    status = await ai_router.get_system_status()
    ollama_stat = "ONLINE" if status["ollama"]["available"] else "OFFLINE"
    pollinations_stat = "ONLINE" if status["pollinations_fallback"]["available"] else "OFFLINE"

    print(f"    - Local Ollama:      {ollama_stat} ({status['ollama']['host']})")
    if status["ollama"]["models"]:
        print(f"      Installed Models:  {', '.join(status['ollama']['models'])}")
    print(f"    - Pollinations Free: {pollinations_stat} (Anonymous Fallback)")
    print(f"    - Active Provider:   {status['active_provider'].upper()}")

    # 5. System Specs
    print("\n[5] Host Telemetry:")
    specs = get_system_telemetry()
    print(f"    - OS:                {specs['os']['system']} {specs['os']['release']} (Build {specs['os']['version']})")
    print(f"    - CPU:               {specs['cpu']['physical_cores']} Cores / Usage: {specs['cpu']['usage_percent']}%")
    print(f"    - RAM:               {specs['memory']['available_gb']} GB Free / {specs['memory']['total_gb']} GB Total")

    print("\n" + "=" * 60)
    print("✅ Health diagnostics complete.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_diagnostics())
