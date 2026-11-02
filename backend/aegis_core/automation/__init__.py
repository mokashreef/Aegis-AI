"""
Aegis AI - Windows Automation Package.
"""

from aegis_core.automation.app_finder import AppFinder, app_finder
from aegis_core.automation.brightness_manager import BrightnessManager, brightness_manager
from aegis_core.automation.clipboard_manager import ClipboardManager
from aegis_core.automation.intent_router import IntentRouter, UserIntent
from aegis_core.automation.notes_manager import NotesManager, notes_manager
from aegis_core.automation.reminder_manager import ReminderManager, reminder_manager
from aegis_core.automation.process_manager import ProcessManager
from aegis_core.automation.screen_capture import ScreenCaptureEngine, screen_capture
from aegis_core.automation.system_tools import (
    BrightnessControlTool,
    CloseAppTool,
    FocusWindowByTitleTool,
    FocusWindowTool,
    GetClipboardTool,
    GetSystemTelemetryTool,
    LaunchAppTool,
    ListProcessesTool,
    ListWindowsTool,
    MinimizeAllWindowsTool,
    QuickNotesTool,
    ScreenCaptureTool,
    AnalyzeScreenTool,
    QueryDocumentTool,
    SetTimerTool,
    SetReminderTool,
    ListRemindersTool,
    CancelReminderTool,
    SetClipboardTool,
    SnapWindowTool,
    VolumeControlTool,
)
from aegis_core.automation.volume_manager import VolumeManager, volume_manager
from aegis_core.automation.window_manager import WindowManager

__all__ = [
    "AppFinder",
    "app_finder",
    "BrightnessManager",
    "brightness_manager",
    "ClipboardManager",
    "IntentRouter",
    "UserIntent",
    "NotesManager",
    "notes_manager",
    "ProcessManager",
    "ScreenCaptureEngine",
    "screen_capture",
    "VolumeManager",
    "volume_manager",
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
    "VolumeControlTool",
    "BrightnessControlTool",
    "ScreenCaptureTool",
    "AnalyzeScreenTool",
    "QueryDocumentTool",
    "SetTimerTool",
    "SetReminderTool",
    "ListRemindersTool",
    "CancelReminderTool",
    "ReminderManager",
    "reminder_manager",
    "QuickNotesTool",
    "GetSystemTelemetryTool",
]
