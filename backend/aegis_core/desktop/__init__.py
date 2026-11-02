"""
Aegis AI - Desktop Overlay & Native Windows Integration Package.
"""

from aegis_core.desktop.hotkey import (
    GlobalHotkeyManager,
    PRESET_HOTKEYS,
    hotkey_manager,
    parse_hotkey_string,
)
from aegis_core.desktop.window import DesktopOverlayManager, overlay_manager

__all__ = [
    "GlobalHotkeyManager",
    "hotkey_manager",
    "PRESET_HOTKEYS",
    "parse_hotkey_string",
    "DesktopOverlayManager",
    "overlay_manager",
]
