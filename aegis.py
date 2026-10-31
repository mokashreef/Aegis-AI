#!/usr/bin/env python3
"""
Aegis AI - Desktop Application Entrypoint.
Launches the local daemon, registers the native Windows Alt+Space global hotkey,
and opens the frameless, always-on-top WebView2 desktop companion overlay.
"""

import sys
import threading
import time
from pathlib import Path

# Add backend directory to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

import uvicorn
from aegis_core.config import settings
from aegis_core.desktop.hotkey import GlobalHotkeyManager
from aegis_core.desktop.window import overlay_manager
from aegis_core.main import app
from aegis_core.utils.logger import logger


def run_daemon_thread():
    """Runs FastAPI daemon in a background thread."""
    config = uvicorn.Config(
        app=app,
        host=settings.host,
        port=settings.port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.run()


def main():
    print("=" * 60)
    print("🛡️  Aegis AI - Native Windows Companion")
    print("=" * 60)
    print("  • Hotkey:     Alt + Space (Summon / Dismiss)")
    print("  • Overlay:    Always-On-Top Frameless WebView2")
    print("  • Backend:    http://127.0.0.1:8420")
    print("  • Mode:       Zero API Keys / Local-First")
    print("=" * 60)

    # 1. Start backend daemon
    logger.info("Starting Aegis Core daemon thread on %s:%d...", settings.host, settings.port)
    daemon_thread = threading.Thread(target=run_daemon_thread, name="AegisDaemonThread", daemon=True)
    daemon_thread.start()

    # Wait for daemon to bind
    time.sleep(0.5)

    # 2. Setup native Windows Alt+Space global hotkey
    def on_hotkey():
        overlay_manager.toggle()

    hotkey_mgr = GlobalHotkeyManager(on_hotkey_pressed=on_hotkey)
    hotkey_mgr.start()

    # 3. Create native overlay window and start GUI loop
    try:
        overlay_manager.create_window()
        overlay_manager.start_gui_loop()
    finally:
        logger.info("Aegis AI shutting down...")
        hotkey_mgr.stop()


if __name__ == "__main__":
    main()
