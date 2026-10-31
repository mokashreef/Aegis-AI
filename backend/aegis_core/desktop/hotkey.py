"""
Aegis AI - Native Windows Global Hotkey Manager.
Uses Win32 WH_KEYBOARD_LL low-level hooks to reliably capture Alt+Space across the entire OS,
bypassing ERROR_HOTKEY_ALREADY_REGISTERED and operating regardless of focused window.
"""

import ctypes
from ctypes import wintypes
import threading
from typing import Callable, Optional
from aegis_core.utils.logger import logger

# Win32 Constants
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_KEYUP = 0x0101
WM_SYSKEYUP = 0x0105
VK_SPACE = 0x20
VK_MENU = 0x12       # Alt key
VK_LMENU = 0xA4      # Left Alt
VK_RMENU = 0xA5      # Right Alt
LLKHF_ALTDOWN = 0x20

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK

user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL

user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_long

user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, ctypes.c_uint, ctypes.c_uint]
user32.GetMessageW.restype = wintypes.BOOL

user32.PostThreadMessageW.argtypes = [wintypes.DWORD, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM]
user32.PostThreadMessageW.restype = wintypes.BOOL


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]


class GlobalHotkeyManager:
    """Manages global Windows keyboard hooks for instant companion summoning."""

    def __init__(self, on_hotkey_pressed: Optional[Callable[[], None]] = None):
        self.on_hotkey_pressed = on_hotkey_pressed
        self._hook: Optional[wintypes.HHOOK] = None
        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._c_callback = None
        self._ready_event = threading.Event()
        self._stop_event = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._ready_event.is_set() and not self._stop_event.is_set()

    def _hook_proc(self, nCode: int, wParam: int, lParam: int) -> int:
        """Low-level hook callback executed on every system keystroke."""
        if nCode >= 0 and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            kbd = KBDLLHOOKSTRUCT.from_address(lParam)
            is_space = kbd.vkCode == VK_SPACE
            is_alt = bool(kbd.flags & LLKHF_ALTDOWN)

            if is_space and is_alt:
                logger.info("Global Alt+Space intercepted. Summoning Aegis AI overlay.")
                if self.on_hotkey_pressed:
                    try:
                        self.on_hotkey_pressed()
                    except Exception as exc:
                        logger.error("Error executing hotkey callback: %s", exc)
                # Consume keypress so Windows System Menu does not activate
                return 1

        return user32.CallNextHookEx(None, nCode, wParam, lParam)

    def _run_message_loop(self):
        """Dedicated background message pump for the Win32 hook."""
        self._thread_id = kernel32.GetCurrentThreadId()
        self._c_callback = HOOKPROC(self._hook_proc)

        self._hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._c_callback,
            None,
            0,
        )

        if not self._hook:
            logger.error("Failed to install WH_KEYBOARD_LL hook. Error code: %d", kernel32.GetLastError())
            self._ready_event.set()
            return

        logger.info("Global Alt+Space hotkey hook installed successfully.")
        self._ready_event.set()

        msg = wintypes.MSG()
        while not self._stop_event.is_set() and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None
            logger.info("Global Alt+Space hook uninstalled.")

    def start(self) -> None:
        """Starts the global hotkey listener in a daemon thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Hotkey listener is already running.")
            return

        self._ready_event.clear()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_message_loop, name="AegisHotkeyThread", daemon=True)
        self._thread.start()
        # Wait for hook to be installed before returning
        self._ready_event.wait(timeout=2.0)

    def stop(self) -> None:
        """Uninstalls the hook and stops the message loop."""
        self._stop_event.set()
        if self._thread_id:
            WM_QUIT = 0x0012
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        self._ready_event.clear()
