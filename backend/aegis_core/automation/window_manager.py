"""
Aegis AI - Windows Window Manager.
Provides window enumeration, focus switching, and window state control using user32.dll.
"""

import ctypes
import os
from typing import Any, Dict, List, Optional

SW_RESTORE = 9
SW_MINIMIZE = 6
SW_MAXIMIZE = 3


class WindowManager:
    """Controls top-level Windows application windows."""

    @staticmethod
    def list_windows(title_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Enumerates active visible desktop windows."""
        if os.name != "nt":
            return []

        user32 = ctypes.windll.user32
        windows = []

        def enum_windows_proc(hwnd, lparam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.strip()
                    if title:
                        if not title_filter or title_filter.lower() in title.lower():
                            windows.append({
                                "hwnd": hwnd,
                                "title": title,
                            })
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        cb = WNDENUMPROC(enum_windows_proc)
        user32.EnumWindows(cb, 0)
        return windows

    @staticmethod
    def focus_window(hwnd: int) -> bool:
        """Brings the designated window handle to the foreground."""
        if os.name != "nt":
            return False

        user32 = ctypes.windll.user32
        user32.ShowWindowAsync(hwnd, SW_RESTORE)
        success = bool(user32.SetForegroundWindow(hwnd))
        return success
