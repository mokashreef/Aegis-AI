"""
Aegis AI - Windows Automation Package.
"""

from aegis_core.automation.app_finder import AppFinder, app_finder
from aegis_core.automation.clipboard_manager import ClipboardManager
from aegis_core.automation.intent_router import IntentRouter, UserIntent
from aegis_core.automation.process_manager import ProcessManager
from aegis_core.automation.system_tools import (
    CloseAppTool,
    FocusWindowByTitleTool,
    FocusWindowTool,
    GetClipboardTool,
    GetSystemTelemetryTool,
    LaunchAppTool,
    ListProcessesTool,
    ListWindowsTool,
    MinimizeAllWindowsTool,
    SetClipboardTool,
    SnapWindowTool,
)
from aegis_core.automation.window_manager import WindowManager

__all__ = [
    "AppFinder",
    "app_finder",
    "ClipboardManager",
    "IntentRouter",
    "UserIntent",
    "ProcessManager",
    "WindowManager",
    "LaunchAppTool",
    "CloseAppTool",
    "ListProcessesTool",
    "GetClipboardTool",
    "SetClipboardTool",
    "ListWindowsTool",
    "FocusWindowTool",
    "FocusWindowByTitleTool",
    "MinimizeAllWindowsTool",
    "SnapWindowTool",
    "GetSystemTelemetryTool",
]
