"""
Aegis AI - Windows Window Manager.
Provides window enumeration, focus switching, window state control,
multi-monitor snapping (left/right/maximize), and desktop minimize-all via Win32 user32.dll.
"""

import ctypes
from ctypes import wintypes
from difflib import SequenceMatcher
import os
from typing import Any, Dict, List, Optional, Union
from aegis_core.utils.logger import logger

# Win32 Constants
SW_HIDE = 0
SW_MAXIMIZE = 3
SW_MINIMIZE = 6
SW_RESTORE = 9
SW_SHOW = 5

VK_LWIN = 0x5B
VK_CONTROL = 0x11
VK_D = 0x44
VK_M = 0x4D
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_F4 = 0x73
VK_TAB = 0x09
KEYEVENTF_KEYUP = 0x0002

MONITOR_DEFAULTTONEAREST = 2
MONITORINFOF_PRIMARY = 0x00000001


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

    _current_virtual_desktop: int = 1

    @classmethod
    def get_monitors(cls) -> List[Dict[str, Any]]:
        """
        Enumerates all active display monitors connected to the system via EnumDisplayMonitors.
        Queries geometry bounds, usable work area (excluding taskbar), and per-monitor DPI.
        """
        if os.name != "nt":
            return []

        user32 = ctypes.windll.user32
        monitors_raw: List[int] = []

        def monitor_enum_proc(hmonitor, hdc, lprect, lparam):
            monitors_raw.append(hmonitor)
            return True

        MONITORENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM
        )
        cb = MONITORENUMPROC(monitor_enum_proc)
        user32.EnumDisplayMonitors(0, 0, cb, 0)

        result = []
        for idx, hmon in enumerate(monitors_raw, 1):
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            if user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
                is_primary = bool(info.dwFlags & MONITORINFOF_PRIMARY)
                dpi = 96
                try:
                    shcore = getattr(ctypes.windll, "shcore", None)
                    if shcore and hasattr(shcore, "GetDpiForMonitor"):
                        dpi_x = ctypes.c_uint()
                        dpi_y = ctypes.c_uint()
                        hr = shcore.GetDpiForMonitor(hmon, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
                        if hr == 0 and dpi_x.value > 0:
                            dpi = dpi_x.value
                except Exception as dpi_err:
                    logger.debug("DPI query fallback for monitor %d: %s", idx, dpi_err)

                rc_mon = info.rcMonitor
                rc_work = info.rcWork

                result.append({
                    "index": idx,
                    "handle": int(hmon),
                    "is_primary": is_primary,
                    "name": f"Monitor {idx} ({'Primary' if is_primary else 'Secondary'})",
                    "dpi": dpi,
                    "scale_percent": int(round((dpi / 96.0) * 100)),
                    "bounds": {
                        "x": rc_mon.left,
                        "y": rc_mon.top,
                        "w": rc_mon.right - rc_mon.left,
                        "h": rc_mon.bottom - rc_mon.top,
                    },
                    "work_area": {
                        "x": rc_work.left,
                        "y": rc_work.top,
                        "w": rc_work.right - rc_work.left,
                        "h": rc_work.bottom - rc_work.top,
                    },
                })
        return result

    @classmethod
    def move_window_to_monitor(
        cls,
        monitor_index: int,
        side: Optional[str] = None,
        hwnd: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Moves the target (or foreground) window to the specified monitor (1-based index)
        with optional side snapping ('left', 'right', 'top', 'bottom', 'maximize', 'center').
        """
        if os.name != "nt":
            return {"success": False, "error": "Multi-monitor management is only supported on Windows."}

        monitors = cls.get_monitors()
        if not monitors:
            return {"success": False, "error": "No display monitors detected."}

        target_mon = None
        for m in monitors:
            if m["index"] == monitor_index:
                target_mon = m
                break

        if not target_mon:
            return {
                "success": False,
                "error": f"Monitor {monitor_index} not found. Available monitors: {len(monitors)}.",
                "available_monitors": [m["name"] for m in monitors],
            }

        target_hwnd = hwnd
        if not target_hwnd:
            fg = cls.get_foreground_window()
            if fg and fg["hwnd"]:
                target_hwnd = fg["hwnd"]

        if not target_hwnd:
            return {"success": False, "error": "No active window found to move."}

        user32 = ctypes.windll.user32
        work = target_mon["work_area"]
        wx = work["x"]
        wy = work["y"]
        ww = work["w"]
        wh = work["h"]

        # Restore window if maximized first
        user32.ShowWindow(target_hwnd, SW_RESTORE)

        clean_side = (side or "center").lower().strip()

        if clean_side in ["maximize", "max"]:
            user32.MoveWindow(target_hwnd, wx + 50, wy + 50, ww - 100, wh - 100, True)
            user32.ShowWindow(target_hwnd, SW_MAXIMIZE)
            action = "maximize"
            x, y, w, h = wx, wy, ww, wh
        elif clean_side in ["left", "snap_left", "tile_left", "left_half"]:
            x = wx
            y = wy
            w = ww // 2
            h = wh
            user32.MoveWindow(target_hwnd, x, y, w, h, True)
            action = "snap_left"
        elif clean_side in ["right", "snap_right", "tile_right", "right_half"]:
            x = wx + (ww // 2)
            y = wy
            w = ww - (ww // 2)
            h = wh
            user32.MoveWindow(target_hwnd, x, y, w, h, True)
            action = "snap_right"
        elif clean_side in ["top", "top_half"]:
            x = wx
            y = wy
            w = ww
            h = wh // 2
            user32.MoveWindow(target_hwnd, x, y, w, h, True)
            action = "snap_top"
        elif clean_side in ["bottom", "bottom_half"]:
            x = wx
            y = wy + (wh // 2)
            w = ww
            h = wh - (wh // 2)
            user32.MoveWindow(target_hwnd, x, y, w, h, True)
            action = "snap_bottom"
        else:
            w = int(ww * 0.75)
            h = int(wh * 0.75)
            x = wx + (ww - w) // 2
            y = wy + (wh - h) // 2
            user32.MoveWindow(target_hwnd, x, y, w, h, True)
            action = "move_center"

        logger.info(
            "Moved window hwnd=%s to Monitor %d (%s) at (%d, %d, %d, %d)",
            target_hwnd, monitor_index, action, x, y, w, h
        )

        return {
            "success": True,
            "monitor": monitor_index,
            "monitor_name": target_mon["name"],
            "action": action,
            "hwnd": target_hwnd,
            "bounds": {"x": x, "y": y, "w": w, "h": h},
        }

    @classmethod
    def snap_window(
        cls,
        side: str,
        hwnd: Optional[int] = None,
        monitor: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Snaps a window to left, right, maximize, or minimize.
        Uses active monitor work area bounds (excluding taskbar),
        or target monitor if specified.
        """
        if monitor is not None and monitor > 0:
            return cls.move_window_to_monitor(monitor_index=monitor, side=side, hwnd=hwnd)

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

    @classmethod
    def switch_virtual_desktop(cls, target: Union[str, int]) -> Dict[str, Any]:
        """
        Switches or controls Windows 10/11 virtual desktops via simulated shortcut keystrokes.
        Supports: 'next', 'prev', 'new', 'close', 'task_view', or integer desktop index.
        """
        if os.name != "nt":
            return {"success": False, "error": "Virtual desktops are only supported on Windows."}

        user32 = ctypes.windll.user32
        action_str = str(target).lower().strip()

        if action_str in ["next", "forward"]:
            # Win + Ctrl + Right
            user32.keybd_event(VK_LWIN, 0, 0, 0)
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_RIGHT, 0, 0, 0)
            user32.keybd_event(VK_RIGHT, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
            cls._current_virtual_desktop += 1
            return {"success": True, "action": "next_desktop", "current_desktop": cls._current_virtual_desktop}

        elif action_str in ["prev", "previous", "back"]:
            # Win + Ctrl + Left
            user32.keybd_event(VK_LWIN, 0, 0, 0)
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_LEFT, 0, 0, 0)
            user32.keybd_event(VK_LEFT, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
            cls._current_virtual_desktop = max(1, cls._current_virtual_desktop - 1)
            return {"success": True, "action": "prev_desktop", "current_desktop": cls._current_virtual_desktop}

        elif action_str in ["new", "create"]:
            # Win + Ctrl + D
            user32.keybd_event(VK_LWIN, 0, 0, 0)
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_D, 0, 0, 0)
            user32.keybd_event(VK_D, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
            cls._current_virtual_desktop += 1
            return {"success": True, "action": "created_new_desktop", "current_desktop": cls._current_virtual_desktop}

        elif action_str in ["close", "delete"]:
            # Win + Ctrl + F4
            user32.keybd_event(VK_LWIN, 0, 0, 0)
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_F4, 0, 0, 0)
            user32.keybd_event(VK_F4, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
            cls._current_virtual_desktop = max(1, cls._current_virtual_desktop - 1)
            return {"success": True, "action": "closed_desktop", "current_desktop": cls._current_virtual_desktop}

        elif action_str in ["task_view", "overview"]:
            # Win + Tab
            user32.keybd_event(VK_LWIN, 0, 0, 0)
            user32.keybd_event(VK_TAB, 0, 0, 0)
            user32.keybd_event(VK_TAB, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
            return {"success": True, "action": "task_view"}

        try:
            target_num = int(action_str)
            if target_num < 1:
                target_num = 1
            diff = target_num - cls._current_virtual_desktop
            if diff > 0:
                key = VK_RIGHT
                count = diff
            else:
                key = VK_LEFT
                count = abs(diff)

            for _ in range(count):
                user32.keybd_event(VK_LWIN, 0, 0, 0)
                user32.keybd_event(VK_CONTROL, 0, 0, 0)
                user32.keybd_event(key, 0, 0, 0)
                user32.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)
                user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
                user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)

            cls._current_virtual_desktop = target_num
            return {
                "success": True,
                "action": f"switched_to_desktop_{target_num}",
                "current_desktop": target_num,
            }
        except ValueError:
            return {"success": False, "error": f"Invalid virtual desktop target: '{target}'"}
