"""
Unit tests for native Windows desktop integration (Hotkeys and Overlay Window).
"""

from fastapi.testclient import TestClient
from aegis_core.desktop.hotkey import (
    GlobalHotkeyManager,
    hotkey_manager,
    parse_hotkey_string,
    PRESET_HOTKEYS,
)
from aegis_core.desktop.window import (
    DesktopOverlayManager,
    AegisDesktopBridge,
    get_active_monitor_bounds,
)
from aegis_core.main import app


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


def test_hotkey_string_parsing():
    """Verify parse_hotkey_string parses key and modifier combinations accurately."""
    # Alt+Space
    vk, alt, ctrl, shift, win = parse_hotkey_string("Alt+Space")
    assert vk == 0x20
    assert alt is True
    assert ctrl is False
    assert shift is False

    # Ctrl+Shift+A
    vk, alt, ctrl, shift, win = parse_hotkey_string("Ctrl+Shift+A")
    assert vk == ord("A")
    assert alt is False
    assert ctrl is True
    assert shift is True

    # Ctrl+Alt+Space
    vk, alt, ctrl, shift, win = parse_hotkey_string("Ctrl+Alt+Space")
    assert vk == 0x20
    assert alt is True
    assert ctrl is True
    assert shift is False

    # F4 single key
    vk, alt, ctrl, shift, win = parse_hotkey_string("F4")
    assert vk == 0x73  # VK_F4
    assert alt is False
    assert ctrl is False

    # Empty fallback
    vk, alt, ctrl, shift, win = parse_hotkey_string("")
    assert vk == 0x20
    assert alt is True


def test_hotkey_dynamic_reconfiguration():
    """Verify hotkey_manager dynamically updates target shortcut at runtime."""
    mgr = GlobalHotkeyManager(hotkey="Alt+Space")
    assert mgr.current_hotkey == "Alt+Space"

    ok = mgr.set_hotkey("Ctrl+Shift+A")
    assert ok is True
    assert mgr.current_hotkey == "Ctrl+Shift+A"
    assert mgr._target_vk == ord("A")
    assert mgr._req_ctrl is True
    assert mgr._req_shift is True
    assert mgr._req_alt is False

    # Revert to default
    mgr.set_hotkey("Alt+Space")
    assert mgr.current_hotkey == "Alt+Space"


def test_desktop_hotkey_api_endpoints():
    """Verify GET and POST /api/desktop/hotkey REST endpoints."""
    client = TestClient(app)

    # 1. GET /api/desktop/hotkey
    res_get = client.get("/api/desktop/hotkey")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert "current_hotkey" in data_get
    assert "presets" in data_get
    assert len(data_get["presets"]) == len(PRESET_HOTKEYS)

    # 2. POST /api/desktop/hotkey (valid)
    res_post = client.post("/api/desktop/hotkey", json={"hotkey": "Ctrl+Shift+A"})
    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["success"] is True
    assert data_post["hotkey"] == "Ctrl+Shift+A"
    assert hotkey_manager.current_hotkey == "Ctrl+Shift+A"

    # 3. POST /api/desktop/hotkey (missing parameter)
    res_err = client.post("/api/desktop/hotkey", json={})
    assert res_err.status_code == 400

    # Reset back to default
    client.post("/api/desktop/hotkey", json={"hotkey": "Alt+Space"})
    assert hotkey_manager.current_hotkey == "Alt+Space"
