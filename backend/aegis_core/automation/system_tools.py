"""
Aegis AI - Built-in Desktop Automation Tools.
Wraps Windows process, window, volume, brightness, screen capture, and quick notes
as BaseTool implementations.
"""

from typing import Any
from aegis_core.automation.brightness_manager import brightness_manager
from aegis_core.automation.clipboard_manager import ClipboardManager
from aegis_core.automation.notes_manager import notes_manager
from aegis_core.automation.process_manager import ProcessManager
from aegis_core.automation.screen_capture import screen_capture
from aegis_core.automation.volume_manager import volume_manager
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


class VolumeControlTool(BaseTool):
    name = "control_volume"
    description = (
        "Controls Windows master audio volume: 'set' (0-100), 'mute', 'unmute', "
        "'increase', 'decrease', or 'get'."
    )
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "The volume action: 'set', 'mute', 'unmute', 'increase', 'decrease', or 'get'.",
                "enum": ["set", "mute", "unmute", "increase", "decrease", "get"],
            },
            "level": {
                "type": "integer",
                "description": "Target volume percentage (0 to 100) for 'set', or delta for adjust.",
            },
        },
        "required": ["action"],
    }

    async def execute(self, action: str, level: int = 0, **kwargs: Any) -> ToolResult:
        act = action.lower().strip()
        if act == "get":
            res = volume_manager.get_status()
            return ToolResult(success=res.get("success", True), data=res)
        elif act == "set":
            res = volume_manager.set_volume(level)
            return ToolResult(success=res.get("success", False), data=res, message=res.get("message"))
        elif act == "mute":
            res = volume_manager.set_mute(True)
            return ToolResult(success=res.get("success", False), data=res, message=res.get("message"))
        elif act == "unmute":
            res = volume_manager.set_mute(False)
            return ToolResult(success=res.get("success", False), data=res, message=res.get("message"))
        elif act in ["increase", "up"]:
            delta = level if level > 0 else 10
            res = volume_manager.adjust_volume(delta)
            return ToolResult(success=res.get("success", False), data=res, message=res.get("message"))
        elif act in ["decrease", "down"]:
            delta = level if level > 0 else 10
            res = volume_manager.adjust_volume(-delta)
            return ToolResult(success=res.get("success", False), data=res, message=res.get("message"))
        return ToolResult(success=False, error=f"Unknown volume action '{action}'.")


class BrightnessControlTool(BaseTool):
    name = "control_brightness"
    description = (
        "Controls Windows display brightness: 'set' (0-100), 'increase', 'decrease', or 'get'."
    )
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Brightness action: 'set', 'increase', 'decrease', or 'get'.",
                "enum": ["set", "increase", "decrease", "get"],
            },
            "level": {
                "type": "integer",
                "description": "Target brightness percentage (0-100) or delta.",
            },
        },
        "required": ["action"],
    }

    async def execute(self, action: str, level: int = 0, **kwargs: Any) -> ToolResult:
        act = action.lower().strip()
        if act == "get":
            res = brightness_manager.get_brightness()
            return ToolResult(success=res.get("success", True), data=res)
        elif act == "set":
            res = brightness_manager.set_brightness(level)
            return ToolResult(success=res.get("success", False), data=res, message=res.get("message"))
        elif act in ["increase", "up"]:
            delta = level if level > 0 else 10
            res = brightness_manager.adjust_brightness(delta)
            return ToolResult(success=res.get("success", False), data=res, message=res.get("message"))
        elif act in ["decrease", "down"]:
            delta = level if level > 0 else 10
            res = brightness_manager.adjust_brightness(-delta)
            return ToolResult(success=res.get("success", False), data=res, message=res.get("message"))
        return ToolResult(success=False, error=f"Unknown brightness action '{action}'.")


class ScreenCaptureTool(BaseTool):
    name = "capture_screen"
    description = (
        "Captures a screenshot of the Windows desktop and prepares it for multimodal analysis."
    )
    risk_level = RiskLevel.READ_ONLY
    parameters_schema = {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "description": "Capture target: 'full' (desktop) or 'active_window'.",
                "default": "full",
            },
        },
    }

    async def execute(self, target: str = "full", **kwargs: Any) -> ToolResult:
        res = screen_capture.capture(target=target)
        if res.get("success"):
            return ToolResult(success=True, data=res, message=res.get("message"))
        return ToolResult(success=False, error=res.get("error", "Screen capture failed."))


class QuickNotesTool(BaseTool):
    name = "manage_notes"
    description = (
        "Manages local markdown daily notes: 'append' to today's note, 'search' notes, or 'read_today'."
    )
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Notes action: 'append', 'search', or 'read_today'.",
                "enum": ["append", "search", "read_today"],
            },
            "text": {
                "type": "string",
                "description": "Note content to append (required for 'append').",
            },
            "query": {
                "type": "string",
                "description": "Search keyword (required for 'search').",
            },
        },
        "required": ["action"],
    }

    async def execute(self, action: str, text: str = "", query: str = "", **kwargs: Any) -> ToolResult:
        act = action.lower().strip()
        if act == "append":
            res = notes_manager.append_daily_note(text)
            return ToolResult(success=res.get("success", False), data=res, message=res.get("message"))
        elif act in ["read_today", "read"]:
            res = notes_manager.get_today_notes()
            return ToolResult(success=res.get("success", True), data=res, message=res.get("message"))
        elif act == "search":
            res = notes_manager.search_notes(query or text)
            return ToolResult(success=res.get("success", False), data=res, message=res.get("message"))
        return ToolResult(success=False, error=f"Unknown notes action '{action}'.")


class GetSystemTelemetryTool(BaseTool):
    name = "get_system_telemetry"
    description = "Retrieves Windows system information including CPU usage, RAM utilization, and OS version."
    risk_level = RiskLevel.READ_ONLY
    parameters_schema = {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        info = get_system_telemetry()
        return ToolResult(success=True, data=info)
