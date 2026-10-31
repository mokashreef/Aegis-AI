"""
Unit tests for native Windows desktop integration (Hotkeys and Overlay Window).
"""

from aegis_core.desktop.hotkey import GlobalHotkeyManager
from aegis_core.desktop.window import (
    DesktopOverlayManager,
    AegisDesktopBridge,
    get_active_monitor_bounds,
)


def test_active_monitor_bounds():
    """Verify that monitor bounds calculation returns valid screen coordinates."""
    bounds = get_active_monitor_bounds(width=760, height=620)
    assert isinstance(bounds, dict)
    assert "x" in bounds
    assert "y" in bounds
    assert "width" in bounds
    assert "height" in bounds
    assert bounds["width"] > 0
    assert bounds["height"] > 0
    assert bounds["x"] >= 0
    assert bounds["y"] >= 0


def test_desktop_bridge():
    """Verify desktop bridge calls through to overlay manager."""
    mgr = DesktopOverlayManager()
    bridge = AegisDesktopBridge(mgr)

    assert bridge.ping() == "pong"
    # Testing toggle/hide without window shouldn't throw
    bridge.hide()
    bridge.show()
    bridge.toggle()


def test_hotkey_manager_lifecycle():
    """Verify GlobalHotkeyManager can start and stop cleanly."""
    called = []

    def on_press():
        called.append(True)

    mgr = GlobalHotkeyManager(on_hotkey_pressed=on_press)
    mgr.start()
    assert mgr.is_running is True
    mgr.stop()
    assert mgr.is_running is False
