#!/usr/bin/env python3
"""
Aegis AI - Desktop Application Entrypoint.
Launches the local daemon, registers the native Windows Alt+Space global hotkey,
starts the System Tray notification icon, and opens the frameless, always-on-top
WebView2 desktop companion overlay.
"""

import sys
import threading
import time
from pathlib import Path

# Add backend directory to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

import uvicorn  # noqa: E402
from aegis_core.config import settings  # noqa: E402
from aegis_core.desktop.hotkey import GlobalHotkeyManager  # noqa: E402
from aegis_core.desktop.tray import TrayIconManager  # noqa: E402
from aegis_core.desktop.window import overlay_manager  # noqa: E402
from aegis_core.main import app  # noqa: E402
from aegis_core.utils.logger import logger  # noqa: E402


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
    print("  • Hotkey:      Alt + Space (Summon / Dismiss)")
    print("  • System Tray: Background daemon icon & context menu active")
    print("  • Overlay:     Always-On-Top Frameless WebView2")
    print("  • Backend:     http://127.0.0.1:8420")
    print("  • Mode:        Zero API Keys / Local-First")
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

    # 3. Initialize System Tray companion icon
    def on_tray_quit():
        logger.info("Shutdown dispatched from system tray.")
        hotkey_mgr.stop()
        overlay_manager.quit()

    tray_mgr = TrayIconManager(overlay_manager=overlay_manager, on_quit=on_tray_quit)
    tray_mgr.start()

    # 4. Create native overlay window and start GUI loop
    try:
        overlay_manager.create_window()
        overlay_manager.start_gui_loop()
    finally:
        logger.info("Aegis AI shutting down...")
        tray_mgr.stop()
        hotkey_mgr.stop()


if __name__ == "__main__":
    main()
