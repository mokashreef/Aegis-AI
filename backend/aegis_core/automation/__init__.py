"""
Aegis AI - Windows Automation Package.
"""

from aegis_core.automation.process_manager import ProcessManager
from aegis_core.automation.clipboard_manager import ClipboardManager
from aegis_core.automation.window_manager import WindowManager
from aegis_core.automation.system_tools import (
    LaunchAppTool,
    CloseAppTool,
    ListProcessesTool,
    GetClipboardTool,
    SetClipboardTool,
    ListWindowsTool,
    FocusWindowTool,
    GetSystemTelemetryTool,
)

__all__ = [
    "ProcessManager",
    "ClipboardManager",
    "WindowManager",
    "LaunchAppTool",
    "CloseAppTool",
    "ListProcessesTool",
    "GetClipboardTool",
    "SetClipboardTool",
    "ListWindowsTool",
    "FocusWindowTool",
    "GetSystemTelemetryTool",
]

