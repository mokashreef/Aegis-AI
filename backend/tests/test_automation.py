"""
Unit tests for Windows desktop automation tools.
"""

import pytest
from aegis_core.automation.process_manager import ProcessManager
from aegis_core.automation.system_tools import (
    GetSystemTelemetryTool,
    SetClipboardTool,
    GetClipboardTool,
)


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
