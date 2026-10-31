"""
Aegis AI - Built-in Desktop Automation Tools.
Wraps Windows process, window, and clipboard managers as BaseTool implementations.
"""

from typing import Any
from aegis_core.automation.clipboard_manager import ClipboardManager
from aegis_core.automation.process_manager import ProcessManager
from aegis_core.automation.window_manager import WindowManager
from aegis_core.plugins.base import BaseTool, RiskLevel, ToolResult
from aegis_core.utils.system_info import get_system_telemetry


class LaunchAppTool(BaseTool):
    name = "launch_application"
    description = (
        "Launches a Windows desktop application or utility using fuzzy matching "
        "(e.g. 'chrome', 'google chrome', 'notepad', 'calculator', 'terminal', 'vs code')."
    )
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "The application name or command (e.g., 'chrome', 'notepad', 'calculator').",
            },
        },
        "required": ["app_name"],
    }

    async def execute(self, app_name: str, **kwargs: Any) -> ToolResult:
        res = ProcessManager.launch_app(app_name)
        if res.get("launched"):
            return ToolResult(
                success=True,
                data=res,
                message=f"Successfully launched {res.get('name', app_name)}",
            )
        return ToolResult(
            success=False,
            error=res.get("error", f"Failed to launch application '{app_name}'."),
            data=res,
        )


class CloseAppTool(BaseTool):
    name = "close_application"
    description = "Terminates a running Windows desktop application by executable name or process ID."
    risk_level = RiskLevel.RESTRICTED_CONFIRM
    parameters_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Process name to terminate (e.g. 'notepad.exe', 'calc.exe', 'chrome.exe').",
            },
            "pid": {
                "type": "integer",
                "description": "Optional specific process ID to terminate.",
            },
        },
    }

    async def execute(self, name: str = "", pid: int = 0, **kwargs: Any) -> ToolResult:
        p_name = name if name else None
        p_id = pid if pid > 0 else None
        res = ProcessManager.terminate_process(pid=p_id, name=p_name)
        if res.get("success"):
            return ToolResult(success=True, data=res)
        return ToolResult(success=False, error="Could not locate or terminate the requested process.", data=res)


class ListProcessesTool(BaseTool):
    name = "list_processes"
    description = "Lists active running desktop applications and system processes with RAM and CPU usage."
    risk_level = RiskLevel.READ_ONLY
    parameters_schema = {
        "type": "object",
        "properties": {
            "filter_name": {
                "type": "string",
                "description": "Optional search string to filter processes by name.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of processes to return (default: 20).",
            },
        },
    }

    async def execute(self, filter_name: str = "", limit: int = 20, **kwargs: Any) -> ToolResult:
        procs = ProcessManager.list_processes(filter_name=filter_name or None, limit=limit)
        return ToolResult(success=True, data=procs)


class GetClipboardTool(BaseTool):
    name = "get_clipboard"
    description = "Reads and returns the current text content copied to the Windows system clipboard."
    risk_level = RiskLevel.READ_ONLY
    parameters_schema = {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        text = ClipboardManager.get_text()
        return ToolResult(success=True, data={"text": text, "length": len(text)})


class SetClipboardTool(BaseTool):
    name = "set_clipboard"
    description = "Copies the provided text content onto the Windows system clipboard."
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text content to write to the clipboard.",
            },
        },
        "required": ["text"],
    }

    async def execute(self, text: str, **kwargs: Any) -> ToolResult:
        ok = ClipboardManager.set_text(text)
        if ok:
            return ToolResult(success=True, data={"copied": True, "length": len(text)})
        return ToolResult(success=False, error="Failed to set clipboard data.")


class ListWindowsTool(BaseTool):
    name = "list_windows"
    description = "Enumerates currently visible desktop windows and titles."
    risk_level = RiskLevel.READ_ONLY
    parameters_schema = {
        "type": "object",
        "properties": {
            "title_filter": {
                "type": "string",
                "description": "Optional keyword to filter window titles.",
            },
        },
    }

    async def execute(self, title_filter: str = "", **kwargs: Any) -> ToolResult:
        windows = WindowManager.list_windows(title_filter=title_filter or None)
        return ToolResult(success=True, data=windows)


class FocusWindowTool(BaseTool):
    name = "focus_window"
    description = "Brings a specific window to the foreground by its window handle (hwnd)."
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "hwnd": {
                "type": "integer",
                "description": "Window handle integer ID to focus.",
            },
        },
        "required": ["hwnd"],
    }

    async def execute(self, hwnd: int, **kwargs: Any) -> ToolResult:
        ok = WindowManager.focus_window(hwnd)
        if ok:
            return ToolResult(success=True, data={"focused": True, "hwnd": hwnd})
        return ToolResult(success=False, error=f"Failed to focus window handle {hwnd}.")


class FocusWindowByTitleTool(BaseTool):
    name = "focus_window_by_title"
    description = "Searches for an open window by application or title name and brings it to the foreground."
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "title_query": {
                "type": "string",
                "description": "The name or title of the window to focus (e.g. 'chrome', 'notepad').",
            },
        },
        "required": ["title_query"],
    }

    async def execute(self, title_query: str, **kwargs: Any) -> ToolResult:
        res = WindowManager.focus_window_by_title(title_query)
        if res.get("success"):
            return ToolResult(success=True, data=res, message=f"Focused window: {res.get('title')}")
        return ToolResult(success=False, error=res.get("error", "Window not found."))


class MinimizeAllWindowsTool(BaseTool):
    name = "minimize_all_windows"
    description = "Minimizes all desktop application windows to show the clean desktop (Win+D)."
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        ok = WindowManager.minimize_all()
        return ToolResult(success=ok, data={"minimized": ok})


class SnapWindowTool(BaseTool):
    name = "snap_window"
    description = (
        "Snaps or tiles the currently active window to 'left', 'right', 'maximize', "
        "'minimize', or 'restore' using monitor work area dimensions."
    )
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "side": {
                "type": "string",
                "description": "Position to snap: 'left', 'right', 'maximize', 'minimize', or 'restore'.",
                "enum": ["left", "right", "maximize", "minimize", "restore"],
            },
            "hwnd": {
                "type": "integer",
                "description": "Optional window handle (defaults to active foreground window).",
            },
        },
        "required": ["side"],
    }

    async def execute(self, side: str, hwnd: int = 0, **kwargs: Any) -> ToolResult:
        target_hwnd = hwnd if hwnd > 0 else None
        res = WindowManager.snap_window(side=side, hwnd=target_hwnd)
        if res.get("success"):
            return ToolResult(success=True, data=res)
        return ToolResult(success=False, error=res.get("error", "Window snapping failed."))


class GetSystemTelemetryTool(BaseTool):
    name = "get_system_telemetry"
    description = "Retrieves Windows system information including CPU usage, RAM utilization, and OS version."
    risk_level = RiskLevel.READ_ONLY
    parameters_schema = {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        info = get_system_telemetry()
        return ToolResult(success=True, data=info)
