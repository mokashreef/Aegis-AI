"""
Comprehensive unit and integration tests for Aegis AI Windows Desktop Automation.
Tests fuzzy app matcher, natural language intent routing, window management, and tools.
"""

from unittest.mock import patch
import pytest
from aegis_core.agent.planner import AgentPlanner
from aegis_core.automation.app_finder import AppFinder, app_finder
from aegis_core.automation.intent_router import IntentRouter, UserIntent
from aegis_core.automation.process_manager import ProcessManager
from aegis_core.automation.system_tools import (
    FocusWindowByTitleTool,
    GetClipboardTool,
    GetSystemTelemetryTool,
    LaunchAppTool,
    MinimizeAllWindowsTool,
    SetClipboardTool,
    SnapWindowTool,
)
from aegis_core.automation.window_manager import WindowManager


@pytest.mark.asyncio
async def test_launch_app_tool():
    """Verify LaunchAppTool invokes app launcher and returns success."""
    tool = LaunchAppTool()
    with patch(
        "aegis_core.automation.process_manager.ProcessManager.launch_app",
        return_value={"launched": True, "name": "notepad"},
    ):
        res = await tool.execute(app_name="notepad")
        assert res.success is True


def test_process_manager_list():
    """Verify that process listing returns valid system tasks."""
    procs = ProcessManager.list_processes(limit=10)
    assert isinstance(procs, list)
    assert len(procs) > 0
    assert "pid" in procs[0]
    assert "name" in procs[0]
    assert "memory_mb" in procs[0]


@pytest.mark.asyncio
async def test_system_telemetry_tool():
    """Ensure system telemetry returns complete hardware specifications."""
    tool = GetSystemTelemetryTool()
    res = await tool.execute()
    assert res.success is True
    assert "os" in res.data
    assert "cpu" in res.data
    assert "memory" in res.data


@pytest.mark.asyncio
async def test_clipboard_cycle():
    """Tests writing and reading from clipboard."""
    set_tool = SetClipboardTool()
    get_tool = GetClipboardTool()

    test_content = "Aegis AI System Test 2026"
    set_res = await set_tool.execute(text=test_content)
    if set_res.success:
        get_res = await get_tool.execute()
        assert get_res.success is True
        assert get_res.data["text"] == test_content


def test_fuzzy_app_finder_resolution():
    """Test that AppFinder resolves natural phrasing to executable targets."""
    # 1. Built-in system apps
    m_calc = app_finder.find_app("can you start calculator please")
    assert m_calc is not None
    assert "calc" in m_calc["target"].lower()

    m_notepad = app_finder.find_app("open notepad")
    assert m_notepad is not None
    assert "notepad" in m_notepad["target"].lower()

    m_terminal = app_finder.find_app("launch terminal")
    assert m_terminal is not None
    assert "wt.exe" in m_terminal["target"].lower()

    # 2. Custom AppFinder instance indexing verification
    finder = AppFinder(cache_ttl_seconds=60)
    finder.refresh_index(force=True)
    assert len(finder._index) > 0


def test_intent_router_classification():
    """Test that IntentRouter correctly classifies natural variations into tools."""
    # 1. App Launching
    r1 = IntentRouter.classify_and_route("can you please open google chrome")
    assert r1 is not None
    assert r1["intent"] == UserIntent.APP_LAUNCH
    assert r1["name"] == "launch_application"
    assert "chrome" in r1["arguments"]["app_name"].lower()

    r2 = IntentRouter.classify_and_route("launch notepad please")
    assert r2 is not None
    assert r2["name"] == "launch_application"
    assert r2["arguments"]["app_name"] == "notepad"

    # 2. App Closing
    r3 = IntentRouter.classify_and_route("kill notepad")
    assert r3 is not None
    assert r3["intent"] == UserIntent.APP_CLOSE
    assert r3["name"] == "close_application"

    # 3. Window Actions
    r4 = IntentRouter.classify_and_route("minimize all windows")
    assert r4 is not None
    assert r4["name"] == "minimize_all_windows"

    r5 = IntentRouter.classify_and_route("snap window left")
    assert r5 is not None
    assert r5["name"] == "snap_window"
    assert r5["arguments"]["side"] == "left"

    r6 = IntentRouter.classify_and_route("bring chrome to front")
    assert r6 is not None
    assert r6["name"] == "focus_window_by_title"
    assert "chrome" in r6["arguments"]["title_query"]

    # 4. System & Clipboard
    r7 = IntentRouter.classify_and_route("what is on my clipboard")
    assert r7 is not None
    assert r7["name"] == "get_clipboard"

    r8 = IntentRouter.classify_and_route("cpu usage")
    assert r8 is not None
    assert r8["name"] == "get_system_telemetry"

    # 5. Conversation Fallback
    r9 = IntentRouter.classify_and_route("what is the capital of France?")
    assert r9 is None


@pytest.mark.asyncio
async def test_window_manager_and_tools():
    """Test WindowManager functions and corresponding tool executions."""
    # 1. List windows
    windows = WindowManager.list_windows()
    assert isinstance(windows, list)

    # 2. Minimize all tool
    min_tool = MinimizeAllWindowsTool()
    with patch("aegis_core.automation.window_manager.WindowManager.minimize_all", return_value=True):
        res = await min_tool.execute()
        assert res.success is True

    # 3. Snap window tool
    snap_tool = SnapWindowTool()
    with patch(
        "aegis_core.automation.window_manager.WindowManager.snap_window",
        return_value={"success": True, "action": "snap_left"},
    ):
        snap_res = await snap_tool.execute(side="left")
        assert snap_res.success is True

    # 4. Focus window by title tool
    focus_tool = FocusWindowByTitleTool()
    with patch(
        "aegis_core.automation.window_manager.WindowManager.focus_window_by_title",
        return_value={"success": True, "title": "Google Chrome"},
    ):
        foc_res = await focus_tool.execute(title_query="chrome")
        assert foc_res.success is True


@pytest.mark.asyncio
async def test_planner_natural_language_routing():
    """Verify that AgentPlanner extracts natural intents and synthesizes output."""
    planner = AgentPlanner()
    call = planner._extract_tool_call("can you start notepad please")
    assert call is not None
    assert call["name"] == "launch_application"
    assert call["arguments"]["app_name"] == "notepad"

    min_call = planner._extract_tool_call("show desktop")
    assert min_call is not None
    assert min_call["name"] == "minimize_all_windows"
