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


def ensure_port_available(port: int = 8420):
    """Safely terminates any orphaned background process occupying the backend port."""
    import os
    try:
        import psutil
        current_pid = os.getpid()
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr and conn.laddr.port == port and conn.pid and conn.pid != current_pid:
                try:
                    p = psutil.Process(conn.pid)
                    logger.warning("Terminating orphan process PID %d holding port %d...", conn.pid, port)
                    p.terminate()
                    p.wait(timeout=2)
                except Exception as ex:
                    logger.debug("Could not terminate orphan PID %d: %s", conn.pid, ex)
    except Exception as e:
        logger.debug("Port cleanup check: %s", e)


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
    if "--install-startup" in sys.argv:
        from aegis_core.desktop.startup import WindowsStartupManager

        ok = WindowsStartupManager.enable()
        print("Aegis AI registered for Windows startup." if ok else "Failed registering startup.")
        sys.exit(0 if ok else 1)

    if "--remove-startup" in sys.argv:
        from aegis_core.desktop.startup import WindowsStartupManager

        ok = WindowsStartupManager.disable()
        print("Aegis AI removed from Windows startup." if ok else "Failed removing startup.")
        sys.exit(0 if ok else 1)

    is_background = "--background" in sys.argv

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
    ensure_port_available(settings.port)
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
        overlay_manager.create_window(hidden=is_background)
        overlay_manager.start_gui_loop()
    finally:
        logger.info("Aegis AI shutting down...")
        tray_mgr.stop()
        hotkey_mgr.stop()


if __name__ == "__main__":
    main()
