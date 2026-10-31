"""
Unit and integration tests for Aegis AI Phase 5 Daily Value Features:
Audio Volume Control, Display Brightness, Screen Capture, Quick Notes, and Natural Language Routing.
"""

from unittest.mock import patch
import pytest
from aegis_core.automation.brightness_manager import BrightnessManager, brightness_manager
from aegis_core.automation.intent_router import IntentRouter, UserIntent
from aegis_core.automation.notes_manager import notes_manager
from aegis_core.automation.screen_capture import screen_capture
from aegis_core.automation.system_tools import (
    BrightnessControlTool,
    QuickNotesTool,
    ScreenCaptureTool,
    VolumeControlTool,
)
from aegis_core.automation.volume_manager import VolumeManager, volume_manager


def test_volume_manager_status_and_control():
    """Verify VolumeManager queries and controls master volume."""
    st = volume_manager.get_status()
    assert isinstance(st, dict)
    assert "level" in st
    assert "is_muted" in st

    with patch.object(
        VolumeManager,
        "set_volume",
        return_value={"success": True, "level": 50, "message": "Volume set to 50%."},
    ):
        res = volume_manager.set_volume(50)
        assert res["success"] is True
        assert res["level"] == 50

    with patch.object(
        VolumeManager,
        "set_mute",
        return_value={"success": True, "is_muted": True, "message": "Audio muted."},
    ):
        mute_res = volume_manager.set_mute(True)
        assert mute_res["success"] is True
        assert mute_res["is_muted"] is True


def test_brightness_manager_status_and_control():
    """Verify BrightnessManager queries and controls display brightness."""
    b = brightness_manager.get_brightness()
    assert b["success"] is True
    assert 0 <= b["brightness"] <= 100

    set_res = brightness_manager.set_brightness(75)
    assert set_res["success"] is True
    assert set_res["brightness"] == 75

    with patch.object(BrightnessManager, "get_brightness", return_value={"success": True, "brightness": 75}):
        adj_res = brightness_manager.adjust_brightness(-10)
        assert adj_res["success"] is True
        assert adj_res["brightness"] == 65


def test_screen_capture_engine():
    """Verify ScreenCaptureEngine captures image and formats base64 payload."""
    cap = screen_capture.capture(target="full")
    assert cap["success"] is True
    assert "base64" in cap
    assert cap["base64"].startswith("data:image/png;base64,")
    assert "path" in cap
    assert cap["size_bytes"] > 0


def test_notes_manager_lifecycle():
    """Verify NotesManager appends daily notes, reads today, and searches."""
    # 1. Append
    test_note = "Aegis AI Automated Test Verification Note"
    app_res = notes_manager.append_daily_note(test_note)
    assert app_res["success"] is True
    assert app_res["text"] == test_note

    # 2. Read Today
    today_res = notes_manager.get_today_notes()
    assert today_res["success"] is True
    assert today_res["entries_count"] >= 1
    assert test_note in today_res["content"]

    # 3. Search
    search_res = notes_manager.search_notes("Verification Note")
    assert search_res["success"] is True
    assert search_res["matches_count"] >= 1
    assert any(test_note in m["snippet"] for m in search_res["matches"])


@pytest.mark.asyncio
async def test_daily_value_tools():
    """Verify execution of VolumeControlTool, BrightnessControlTool, ScreenCaptureTool, and QuickNotesTool."""
    # 1. Volume Tool
    vol_tool = VolumeControlTool()
    with patch.object(volume_manager, "set_volume", return_value={"success": True, "level": 80}):
        vol_res = await vol_tool.execute(action="set", level=80)
        assert vol_res.success is True

    # 2. Brightness Tool
    br_tool = BrightnessControlTool()
    with patch.object(brightness_manager, "set_brightness", return_value={"success": True, "brightness": 90}):
        br_res = await br_tool.execute(action="set", level=90)
        assert br_res.success is True

    # 3. Screen Capture Tool
    scr_tool = ScreenCaptureTool()
    with patch.object(
        screen_capture,
        "capture",
        return_value={"success": True, "base64": "data:image/png;base64,abc", "message": "Captured"},
    ):
        scr_res = await scr_tool.execute(target="full")
        assert scr_res.success is True

    # 4. Quick Notes Tool
    note_tool = QuickNotesTool()
    with patch.object(notes_manager, "append_daily_note", return_value={"success": True, "message": "Saved"}):
        note_res = await note_tool.execute(action="append", text="Finish Phase 5")
        assert note_res.success is True


def test_intent_router_daily_value_patterns():
    """Verify that IntentRouter classifies all Phase 5 daily value commands."""
    # Volume
    r_vol = IntentRouter.classify_and_route("set volume to 65%")
    assert r_vol is not None
    assert r_vol["intent"] == UserIntent.VOLUME
    assert r_vol["name"] == "control_volume"
    assert r_vol["arguments"] == {"action": "set", "level": 65}

    r_mute = IntentRouter.classify_and_route("mute sound please")
    assert r_mute is not None
    assert r_mute["arguments"]["action"] == "mute"

    r_unmute = IntentRouter.classify_and_route("unmute")
    assert r_unmute is not None
    assert r_unmute["arguments"]["action"] == "unmute"

    # Brightness
    r_br = IntentRouter.classify_and_route("brightness 70")
    assert r_br is not None
    assert r_br["intent"] == UserIntent.BRIGHTNESS
    assert r_br["arguments"] == {"action": "set", "level": 70}

    r_dim = IntentRouter.classify_and_route("dim screen")
    assert r_dim is not None
    assert r_dim["arguments"]["action"] == "decrease"

    # Screen Capture
    r_scr = IntentRouter.classify_and_route("take a screenshot please")
    assert r_scr is not None
    assert r_scr["intent"] == UserIntent.SCREEN_CAPTURE
    assert r_scr["name"] == "capture_screen"

    # Quick Notes
    r_note = IntentRouter.classify_and_route("note down: review pull request at 4pm")
    assert r_note is not None
    assert r_note["intent"] == UserIntent.NOTES
    assert r_note["name"] == "manage_notes"
    assert "review pull request" in r_note["arguments"]["text"]

    r_read_note = IntentRouter.classify_and_route("show today's notes")
    assert r_read_note is not None
    assert r_read_note["arguments"]["action"] == "read_today"

    r_search_note = IntentRouter.classify_and_route("search notes for deployment")
    assert r_search_note is not None
    assert r_search_note["arguments"]["action"] == "search"
    assert r_search_note["arguments"]["query"] == "deployment"
