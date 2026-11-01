"""
Unit and integration tests for Aegis AI Arabic Voice Commands, OpenUrlTool, and Desktop Usability.
Covers Issue #13:
- Arabic spoken command classification and direct intent routing.
- Web browser launching (Chrome, Comet, Edge, Brave, etc.) with OpenUrlTool.
- Desktop Pin / Always-On-Top toggle endpoint and JS bridge.
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from aegis_core.automation.intent_router import IntentRouter, UserIntent
from aegis_core.automation.system_tools import OpenUrlTool
from aegis_core.desktop.window import DesktopOverlayManager
from aegis_core.main import app


def test_arabic_url_routing():
    """Verify that Arabic spoken requests to open websites are mapped directly to open_url."""
    # 1. YouTube in Chrome
    r1 = IntentRouter.classify_and_route("افتح لي موقع يوتيوب بمتصفح كروم")
    assert r1 is not None
    assert r1["intent"] == UserIntent.OPEN_URL
    assert r1["name"] == "open_url"
    assert "youtube.com" in r1["arguments"]["url"]
    assert r1["arguments"]["browser"] == "chrome"

    # 2. Google in Comet
    r2 = IntentRouter.classify_and_route("افتح جوجل بمتصفح كومت")
    assert r2 is not None
    assert r2["intent"] == UserIntent.OPEN_URL
    assert r2["name"] == "open_url"
    assert "google.com" in r2["arguments"]["url"]
    assert r2["arguments"]["browser"] == "comet"

    # 3. Direct URL with protocol
    r3 = IntentRouter.classify_and_route("افتح https://news.ycombinator.com")
    assert r3 is not None
    assert r3["intent"] == UserIntent.OPEN_URL
    assert r3["arguments"]["url"] == "https://news.ycombinator.com"

    # 4. GitHub with Brave
    r4 = IntentRouter.classify_and_route("افتح موقع github بمتصفح بريف")
    assert r4 is not None
    assert r4["intent"] == UserIntent.OPEN_URL
    assert "github.com" in r4["arguments"]["url"]
    assert r4["arguments"]["browser"] == "brave"

    # 5. English open URL command
    r5 = IntentRouter.classify_and_route("open youtube in chrome")
    assert r5 is not None
    assert r5["intent"] == UserIntent.OPEN_URL
    assert "youtube.com" in r5["arguments"]["url"]
    assert r5["arguments"]["browser"] == "chrome"


def test_arabic_app_launch_routing():
    """Verify Arabic spoken commands for launching applications."""
    # Notepad
    r_notepad = IntentRouter.classify_and_route("افتح المفكرة")
    assert r_notepad is not None
    assert r_notepad["intent"] == UserIntent.APP_LAUNCH
    assert r_notepad["arguments"]["app_name"] == "notepad"

    # Paint
    r_paint = IntentRouter.classify_and_route("شغل الرسام")
    assert r_paint is not None
    assert r_paint["intent"] == UserIntent.APP_LAUNCH
    assert r_paint["arguments"]["app_name"] == "mspaint"

    # Chrome
    r_chrome = IntentRouter.classify_and_route("افتح كروم")
    assert r_chrome is not None
    assert r_chrome["intent"] == UserIntent.APP_LAUNCH
    assert r_chrome["arguments"]["app_name"] == "chrome"

    # Comet
    r_comet = IntentRouter.classify_and_route("افتح متصفح كومت")
    assert r_comet is not None
    assert r_comet["intent"] == UserIntent.APP_LAUNCH
    assert r_comet["arguments"]["app_name"] == "comet"


def test_arabic_system_controls_routing():
    """Verify Arabic spoken commands for media, brightness, windows, and screenshots."""
    # Volume mute/unmute
    r_mute = IntentRouter.classify_and_route("كتم الصوت")
    assert r_mute is not None
    assert r_mute["intent"] == UserIntent.VOLUME
    assert r_mute["arguments"]["action"] == "mute"

    r_unmute = IntentRouter.classify_and_route("إلغاء كتم الصوت")
    assert r_unmute is not None
    assert r_unmute["arguments"]["action"] == "unmute"

    r_vol_up = IntentRouter.classify_and_route("علي الصوت")
    assert r_vol_up is not None
    assert r_vol_up["arguments"]["action"] == "increase"

    # Screenshot
    r_snap = IntentRouter.classify_and_route("صور الشاشة")
    assert r_snap is not None
    assert r_snap["intent"] == UserIntent.SCREEN_CAPTURE
    assert r_snap["name"] == "capture_screen"

    # Minimize / Show Desktop
    r_min = IntentRouter.classify_and_route("صغر كل النوافذ")
    assert r_min is not None
    assert r_min["intent"] == UserIntent.WINDOW_ACTION
    assert r_min["name"] == "minimize_all_windows"

    r_min2 = IntentRouter.classify_and_route("صغر النوافذ")
    assert r_min2 is not None
    assert r_min2["intent"] == UserIntent.WINDOW_ACTION
    assert r_min2["name"] == "minimize_all_windows"

    # Notes
    r_note = IntentRouter.classify_and_route("اكتب ملاحظة اجتماع مهم اليوم")
    assert r_note is not None
    assert r_note["intent"] == UserIntent.NOTES
    assert "اجتماع مهم اليوم" in r_note["arguments"]["text"]


@pytest.mark.asyncio
async def test_open_url_tool_execution():
    """Verify OpenUrlTool handles normalization and browser launching."""
    tool = OpenUrlTool()

    # 1. Normalization of shorthand names
    with patch("webbrowser.open", return_value=True) as mock_wb:
        res = await tool.execute(url="youtube")
        assert res.success is True
        assert res.data["url"] == "https://www.youtube.com"
        mock_wb.assert_called_once_with("https://www.youtube.com")

    # 2. Arabic name normalization
    with patch("webbrowser.open", return_value=True):
        res_ar = await tool.execute(url="يوتيوب")
        assert res_ar.success is True
        assert res_ar.data["url"] == "https://www.youtube.com"

    # 3. Targeted browser launch via subprocess
    with patch("shutil.which", return_value="C:\\Program Files\\Google\\Chrome\\chrome.exe"), \
         patch("subprocess.Popen") as mock_popen:
        res_chrome = await tool.execute(url="https://google.com", browser="chrome")
        assert res_chrome.success is True
        assert res_chrome.data["browser"] == "chrome"
        assert res_chrome.data["method"] == "browser_chrome"
        mock_popen.assert_called_once()


def test_desktop_pin_endpoints():
    """Verify GET and POST /api/desktop/pin endpoints."""
    client = TestClient(app)

    # 1. GET pin state
    resp_get = client.get("/api/desktop/pin")
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert "is_on_top" in data_get
    initial_state = data_get["is_on_top"]

    # 2. POST toggle pin state
    resp_post = client.post("/api/desktop/pin")
    assert resp_post.status_code == 200
    data_post = resp_post.json()
    assert data_post["is_on_top"] == (not initial_state)

    # 3. POST toggle back
    resp_post2 = client.post("/api/desktop/pin")
    assert resp_post2.status_code == 200
    assert resp_post2.json()["is_on_top"] == initial_state


def test_overlay_manager_toggle_on_top():
    """Verify DesktopOverlayManager toggle_on_top method with mock window."""
    mgr = DesktopOverlayManager()
    mock_window = MagicMock()
    mgr.window = mock_window

    mgr._is_on_top = True
    new_state = mgr.toggle_on_top()
    assert new_state is False
    assert mgr.is_on_top is False
    mock_window.on_top = False

    new_state2 = mgr.toggle_on_top()
    assert new_state2 is True
    assert mgr.is_on_top is True
    mock_window.on_top = True


def test_arabic_spoken_phonetic_domains_and_compound_phrases():
    """Verify Issue #14: spoken domains (دوت نت -> .net) and compound browser phrases."""
    # 1. "كروم و افتح موقع كود التطور دوت نت"
    r1 = IntentRouter.classify_and_route("كروم و افتح موقع كود التطور دوت نت")
    assert r1 is not None
    assert r1["intent"] == UserIntent.OPEN_URL
    assert r1["name"] == "open_url"
    assert r1["arguments"]["browser"] == "chrome"
    assert "كود التطور.net" in r1["arguments"]["url"]

    # 2. "افتح كروم و افتح موقع كود التطور دوت نت"
    r2 = IntentRouter.classify_and_route("افتح كروم و افتح موقع كود التطور دوت نت")
    assert r2 is not None
    assert r2["arguments"]["browser"] == "chrome"
    assert "كود التطور.net" in r2["arguments"]["url"]

    # 3. "كومت وافتح موقع جوجل دوت كوم"
    r3 = IntentRouter.classify_and_route("كومت وافتح موقع جوجل دوت كوم")
    assert r3 is not None
    assert r3["arguments"]["browser"] == "comet"
    assert "جوجل.com" in r3["arguments"]["url"]

    # 4. "افتح موقع كود التطور دوت نت"
    r4 = IntentRouter.classify_and_route("افتح موقع كود التطور دوت نت")
    assert r4 is not None
    assert "كود التطور.net" in r4["arguments"]["url"]

    # 5. "كروم و افتح موقع كود التطور" (without domain extension)
    r5 = IntentRouter.classify_and_route("كروم و افتح موقع كود التطور")
    assert r5 is not None
    assert r5["intent"] == UserIntent.OPEN_URL
    assert r5["arguments"]["browser"] == "chrome"
    assert r5["arguments"]["url"] == "كود التطور"

    # 6. "افتح موقع كود التطور بكروم"
    r6 = IntentRouter.classify_and_route("افتح موقع كود التطور بكروم")
    assert r6 is not None
    assert r6["arguments"]["browser"] == "chrome"
    assert r6["arguments"]["url"] == "كود التطور"

    # 7. "كود التطور دوت نت" (standalone spoken domain)
    r7 = IntentRouter.classify_and_route("كود التطور دوت نت")
    assert r7 is not None
    assert r7["intent"] == UserIntent.OPEN_URL
    assert "كود التطور.net" in r7["arguments"]["url"]

    # 8. "افتح المتصفح و افتح كود التطور"
    r8 = IntentRouter.classify_and_route("افتح المتصفح و افتح كود التطور")
    assert r8 is not None
    assert r8["intent"] == UserIntent.OPEN_URL
    assert r8["arguments"]["url"] == "كود التطور"
    assert r8["arguments"]["browser"] == "chrome"


@pytest.mark.asyncio
async def test_launch_app_tool_website_fallback():
    """Verify LaunchAppTool intercepts website commands and redirects to OpenUrlTool."""
    from aegis_core.automation.system_tools import LaunchAppTool

    import urllib.parse
    tool = LaunchAppTool()
    with patch("webbrowser.open", return_value=True):
        res = await tool.execute(app_name="كروم و افتح موقع كود التطور دوت نت")
        assert res.success is True
        assert "كود التطور.net" in urllib.parse.unquote_plus(res.data["url"])


def test_windows_startup_manager():
    """Verify WindowsStartupManager registration, enable, disable, and toggle."""
    from aegis_core.desktop.startup import WindowsStartupManager

    with patch("winreg.OpenKey"), patch("winreg.QueryValueEx", return_value=("cmd", 1)):
        assert WindowsStartupManager.is_enabled() is True

    with patch("winreg.OpenKey"), patch("winreg.SetValueEx"):
        assert WindowsStartupManager.enable() is True

    with patch("winreg.OpenKey"), patch("winreg.DeleteValue"):
        assert WindowsStartupManager.disable() is True


def test_desktop_startup_api_endpoints():
    """Verify GET and POST /api/desktop/startup endpoints."""
    from aegis_core.desktop.startup import WindowsStartupManager

    client = TestClient(app)

    with patch.object(WindowsStartupManager, "is_enabled", return_value=True):
        resp_get = client.get("/api/desktop/startup")
        assert resp_get.status_code == 200
        assert resp_get.json() == {"enabled": True}

    with patch.object(WindowsStartupManager, "toggle", return_value=False):
        resp_toggle = client.post("/api/desktop/startup/toggle")
        assert resp_toggle.status_code == 200
        assert resp_toggle.json() == {"enabled": False}
