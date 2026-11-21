"""
Aegis AI - Unit Tests for Multi-Monitor Window Management & Virtual Desktop Automation.
Verifies EnumDisplayMonitors enumeration, DPI discovery, multi-monitor snapping,
virtual desktop switching, and bilingual intent routing (resolving Issue #4).
"""

from unittest.mock import patch
import pytest
from aegis_core.automation.intent_router import IntentRouter, UserIntent
from aegis_core.automation.system_tools import (
    ListMonitorsTool,
    ManageVirtualDesktopTool,
    MoveWindowMonitorTool,
    SnapWindowTool,
)
from aegis_core.automation.window_manager import WindowManager


def test_window_manager_get_monitors():
    monitors = WindowManager.get_monitors()
    assert isinstance(monitors, list)
    if monitors:
        m = monitors[0]
        assert "index" in m
        assert "is_primary" in m
        assert "bounds" in m
        assert "work_area" in m
        assert "dpi" in m
        assert "scale_percent" in m
        assert m["dpi"] >= 72
        assert m["work_area"]["w"] > 0
        assert m["work_area"]["h"] > 0


def test_move_window_to_monitor_mocked():
    mock_monitors = [
        {
            "index": 1,
            "handle": 1001,
            "is_primary": True,
            "name": "Monitor 1 (Primary)",
            "dpi": 96,
            "scale_percent": 100,
            "bounds": {"x": 0, "y": 0, "w": 1920, "h": 1080},
            "work_area": {"x": 0, "y": 0, "w": 1920, "h": 1040},
        },
        {
            "index": 2,
            "handle": 1002,
            "is_primary": False,
            "name": "Monitor 2 (Secondary)",
            "dpi": 96,
            "scale_percent": 100,
            "bounds": {"x": 1920, "y": 0, "w": 1920, "h": 1080},
            "work_area": {"x": 1920, "y": 0, "w": 1920, "h": 1080},
        },
    ]

    with patch.object(WindowManager, "get_monitors", return_value=mock_monitors):
        with patch.object(WindowManager, "get_foreground_window", return_value={"hwnd": 1234, "title": "Editor"}):
            with patch("ctypes.windll.user32.MoveWindow") as mock_move:
                with patch("ctypes.windll.user32.ShowWindow") as mock_show:
                    # 1. Snap to right half of monitor 2
                    res_right = WindowManager.move_window_to_monitor(monitor_index=2, side="right", hwnd=1234)
                    assert res_right["success"] is True
                    assert res_right["monitor"] == 2
                    assert res_right["action"] == "snap_right"
                    assert res_right["bounds"]["x"] == 1920 + 960
                    assert res_right["bounds"]["w"] == 960
                    mock_move.assert_called_with(1234, 1920 + 960, 0, 960, 1080, True)

                    # 2. Snap to left half of monitor 2
                    res_left = WindowManager.move_window_to_monitor(monitor_index=2, side="left", hwnd=1234)
                    assert res_left["success"] is True
                    assert res_left["action"] == "snap_left"
                    assert res_left["bounds"]["x"] == 1920

                    # 3. Maximize on monitor 2
                    res_max = WindowManager.move_window_to_monitor(monitor_index=2, side="maximize", hwnd=1234)
                    assert res_max["success"] is True
                    assert res_max["action"] == "maximize"
                    mock_show.assert_called()

                    # 4. Unknown monitor index
                    res_err = WindowManager.move_window_to_monitor(monitor_index=5, side="center", hwnd=1234)
                    assert res_err["success"] is False
                    assert "Monitor 5 not found" in res_err["error"]


def test_snap_window_with_monitor_parameter():
    with patch.object(WindowManager, "move_window_to_monitor", return_value={"success": True, "action": "snap_right"}):
        res = WindowManager.snap_window(side="right", hwnd=1234, monitor=2)
        assert res["success"] is True


def test_virtual_desktop_controls():
    with patch("ctypes.windll.user32.keybd_event") as mock_keybd:
        # 1. Next desktop
        res_next = WindowManager.switch_virtual_desktop("next")
        assert res_next["success"] is True
        assert res_next["action"] == "next_desktop"
        assert mock_keybd.call_count >= 6

        # 2. Prev desktop
        res_prev = WindowManager.switch_virtual_desktop("prev")
        assert res_prev["success"] is True
        assert res_prev["action"] == "prev_desktop"

        # 3. New desktop
        res_new = WindowManager.switch_virtual_desktop("new")
        assert res_new["success"] is True
        assert res_new["action"] == "created_new_desktop"

        # 4. Task view
        res_tv = WindowManager.switch_virtual_desktop("task_view")
        assert res_tv["success"] is True
        assert res_tv["action"] == "task_view"

        # 5. Jump to desktop 2
        res_desk2 = WindowManager.switch_virtual_desktop(2)
        assert res_desk2["success"] is True
        assert res_desk2["current_desktop"] == 2


@pytest.mark.asyncio
async def test_tools_execution():
    # 1. ListMonitorsTool
    list_tool = ListMonitorsTool()
    res_list = await list_tool.execute()
    assert res_list.success is True
    assert "monitors" in res_list.data

    # 2. MoveWindowMonitorTool
    move_tool = MoveWindowMonitorTool()
    with patch.object(
        WindowManager, "move_window_to_monitor", return_value={"success": True, "action": "snap_right"}
    ):
        res_move = await move_tool.execute(monitor=2, side="right")
        assert res_move.success is True
        assert "Monitor 2 (right)" in res_move.message

    # 3. ManageVirtualDesktopTool
    desk_tool = ManageVirtualDesktopTool()
    with patch.object(
        WindowManager, "switch_virtual_desktop", return_value={"success": True, "action": "next_desktop"}
    ):
        res_desk = await desk_tool.execute(action="next")
        assert res_desk.success is True
        assert res_desk.data["action"] == "next_desktop"

    # 4. SnapWindowTool with monitor
    snap_tool = SnapWindowTool()
    with patch.object(
        WindowManager, "snap_window", return_value={"success": True, "action": "snap_left"}
    ):
        res_snap = await snap_tool.execute(side="left", monitor=2)
        assert res_snap.success is True
        assert "monitor 2" in res_snap.message


def test_intent_router_multi_monitor_arabic():
    # "انقل النافذة للشاشة الثانية"
    r1 = IntentRouter.classify_and_route("انقل النافذة للشاشة الثانية")
    assert r1 is not None
    assert r1["intent"] == UserIntent.MULTI_MONITOR
    assert r1["name"] == "move_window_monitor"
    assert r1["arguments"]["monitor"] == 2
    assert r1["arguments"]["side"] == "center"

    # "انقل للشاشة 2"
    r2 = IntentRouter.classify_and_route("انقل للشاشة 2")
    assert r2 is not None
    assert r2["intent"] == UserIntent.MULTI_MONITOR
    assert r2["arguments"]["monitor"] == 2

    # "انقل النافذة ليمين الشاشة الثانية"
    r3 = IntentRouter.classify_and_route("انقل النافذة للشاشة الثانية على اليمين")
    assert r3 is not None
    assert r3["intent"] == UserIntent.MULTI_MONITOR
    assert r3["arguments"]["monitor"] == 2
    assert r3["arguments"]["side"] == "right"

    # "اعرض الشاشات"
    r4 = IntentRouter.classify_and_route("اعرض الشاشات")
    assert r4 is not None
    assert r4["name"] == "list_monitors"


def test_intent_router_multi_monitor_english():
    # "Snap active window to the right half of monitor 2"
    r1 = IntentRouter.classify_and_route("Snap active window to the right half of monitor 2")
    assert r1 is not None
    assert r1["intent"] == UserIntent.MULTI_MONITOR
    assert r1["name"] == "move_window_monitor"
    assert r1["arguments"]["monitor"] == 2
    assert r1["arguments"]["side"] == "right"

    # "Move window to monitor 2"
    r2 = IntentRouter.classify_and_route("Move window to monitor 2")
    assert r2 is not None
    assert r2["intent"] == UserIntent.MULTI_MONITOR
    assert r2["name"] == "move_window_monitor"
    assert r2["arguments"]["monitor"] == 2

    # "list monitors"
    r3 = IntentRouter.classify_and_route("list monitors")
    assert r3 is not None
    assert r3["name"] == "list_monitors"


def test_intent_router_virtual_desktop_bilingual():
    # "Switch to virtual desktop 2"
    r1 = IntentRouter.classify_and_route("Switch to virtual desktop 2")
    assert r1 is not None
    assert r1["intent"] == UserIntent.VIRTUAL_DESKTOP
    assert r1["name"] == "manage_virtual_desktop"
    assert r1["arguments"]["action"] == "switch"
    assert r1["arguments"]["desktop"] == 2

    # "Next virtual desktop"
    r2 = IntentRouter.classify_and_route("next virtual desktop")
    assert r2 is not None
    assert r2["arguments"]["action"] == "next"

    # "انتقل إلى سطح المكتب الثاني"
    r3 = IntentRouter.classify_and_route("انتقل إلى سطح المكتب الثاني")
    assert r3 is not None
    assert r3["intent"] == UserIntent.VIRTUAL_DESKTOP
    assert r3["arguments"]["action"] == "switch"
    assert r3["arguments"]["desktop"] == 2

    # "سطح مكتب جديد"
    r4 = IntentRouter.classify_and_route("سطح مكتب جديد")
    assert r4 is not None
    assert r4["arguments"]["action"] == "new"

    # "سطح المكتب 2"
    r5 = IntentRouter.classify_and_route("سطح المكتب 2")
    assert r5 is not None
    assert r5["arguments"]["action"] == "switch"
    assert r5["arguments"]["desktop"] == 2
