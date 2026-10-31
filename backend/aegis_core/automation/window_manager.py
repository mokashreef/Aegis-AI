"""
Aegis AI - Windows Window Manager.
Provides window enumeration, focus switching, window state control,
multi-monitor snapping (left/right/maximize), and desktop minimize-all via Win32 user32.dll.
"""

import ctypes
from ctypes import wintypes
from difflib import SequenceMatcher
import os
from typing import Any, Dict, List, Optional
from aegis_core.utils.logger import logger

# Win32 Constants
SW_HIDE = 0
SW_MAXIMIZE = 3
SW_MINIMIZE = 6
SW_RESTORE = 9
SW_SHOW = 5

VK_LWIN = 0x5B
VK_D = 0x44
VK_M = 0x4D
KEYEVENTF_KEYUP = 0x0002

MONITOR_DEFAULTTONEAREST = 2


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


class WindowManager:
    """Controls top-level Windows application windows and display layouts."""

    @staticmethod
    def list_windows(title_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Enumerates active visible desktop application windows."""
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
                    # Filter out system background layers
                    if title and title not in ["Program Manager", "Windows Input Experience"]:
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
    def get_foreground_window() -> Optional[Dict[str, Any]]:
        """Returns the currently active foreground window handle and title."""
        if os.name != "nt":
            return None

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None

        length = user32.GetWindowTextLengthW(hwnd)
        title = ""
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.strip()

        return {"hwnd": hwnd, "title": title}

    @staticmethod
    def focus_window(hwnd: int) -> bool:
        """Brings the designated window handle to the foreground."""
        if os.name != "nt":
            return False

        user32 = ctypes.windll.user32
        user32.ShowWindowAsync(hwnd, SW_RESTORE)
        success = bool(user32.SetForegroundWindow(hwnd))
        return success

    @classmethod
    def focus_window_by_title(cls, title_query: str) -> Dict[str, Any]:
        """Finds and focuses the best matching open application window."""
        windows = cls.list_windows()
        if not windows:
            return {"success": False, "error": "No open application windows found."}

        clean_query = title_query.lower().strip()
        best_match: Optional[Dict[str, Any]] = None
        best_score = 0.0

        for win in windows:
            t = win["title"].lower()
            if clean_query in t:
                score = 90.0 + (len(clean_query) / len(t)) * 10.0
            else:
                score = SequenceMatcher(None, clean_query, t).ratio() * 80.0

            if score > best_score:
                best_score = score
                best_match = win

        if best_match and best_score >= 50.0:
            cls.focus_window(best_match["hwnd"])
            return {
                "success": True,
                "hwnd": best_match["hwnd"],
                "title": best_match["title"],
                "score": round(best_score, 1),
            }

        return {
            "success": False,
            "error": f"No active window matching '{title_query}' found.",
        }

    @staticmethod
    def minimize_all() -> bool:
        """Simulates native Windows Show Desktop / Minimize All (Win+D)."""
        if os.name != "nt":
            return False

        user32 = ctypes.windll.user32
        # Win+D toggle
        user32.keybd_event(VK_LWIN, 0, 0, 0)
        user32.keybd_event(VK_D, 0, 0, 0)
        user32.keybd_event(VK_D, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
        logger.info("Executed Win+D minimize all / show desktop.")
        return True

    @classmethod
    def snap_window(cls, side: str, hwnd: Optional[int] = None) -> Dict[str, Any]:
        """
        Snaps a window to left, right, maximize, or minimize.
        Uses active monitor work area bounds (excluding taskbar).
        """
        if os.name != "nt":
            return {"success": False, "error": "Snapping is only supported on Windows."}

        user32 = ctypes.windll.user32
        target_hwnd = hwnd
        if not target_hwnd:
            fg = cls.get_foreground_window()
            if fg and fg["hwnd"]:
                target_hwnd = fg["hwnd"]

        if not target_hwnd:
            return {"success": False, "error": "No active window found to snap."}

        clean_side = side.lower().strip()

        # Handle simple maximize/minimize actions
        if clean_side in ["maximize", "max"]:
            user32.ShowWindow(target_hwnd, SW_MAXIMIZE)
            return {"success": True, "action": "maximize", "hwnd": target_hwnd}
        elif clean_side in ["minimize", "min"]:
            user32.ShowWindow(target_hwnd, SW_MINIMIZE)
            return {"success": True, "action": "minimize", "hwnd": target_hwnd}
        elif clean_side in ["restore"]:
            user32.ShowWindow(target_hwnd, SW_RESTORE)
            return {"success": True, "action": "restore", "hwnd": target_hwnd}

        # Query active monitor geometry
        hmonitor = user32.MonitorFromWindow(target_hwnd, MONITOR_DEFAULTTONEAREST)
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if not user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
            return {"success": False, "error": "Failed to get monitor coordinates."}

        work = info.rcWork
        work_x = work.left
        work_y = work.top
        work_w = work.right - work.left
        work_h = work.bottom - work.top

        # Restore first if maximized
        user32.ShowWindow(target_hwnd, SW_RESTORE)

        if clean_side in ["left", "snap_left", "tile_left"]:
            x = work_x
            y = work_y
            w = work_w // 2
            h = work_h
            user32.MoveWindow(target_hwnd, x, y, w, h, True)
            return {
                "success": True,
                "action": "snap_left",
                "hwnd": target_hwnd,
                "bounds": {"x": x, "y": y, "w": w, "h": h},
            }

        elif clean_side in ["right", "snap_right", "tile_right"]:
            x = work_x + (work_w // 2)
            y = work_y
            w = work_w - (work_w // 2)
            h = work_h
            user32.MoveWindow(target_hwnd, x, y, w, h, True)
            return {
                "success": True,
                "action": "snap_right",
                "hwnd": target_hwnd,
                "bounds": {"x": x, "y": y, "w": w, "h": h},
            }

        return {"success": False, "error": f"Unknown snap direction '{side}'."}
