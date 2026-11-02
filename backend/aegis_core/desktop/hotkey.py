"""
Aegis AI - Native Windows Global Hotkey Manager.
Uses Win32 WH_KEYBOARD_LL low-level hooks to reliably capture customizable shortcuts across the entire OS,
bypassing ERROR_HOTKEY_ALREADY_REGISTERED and operating regardless of focused window.
Supports dynamic runtime reconfiguration, multiple modifiers (Alt, Ctrl, Shift, Win), and key combos.
"""

import ctypes
from ctypes import wintypes
import threading
from typing import Callable, Dict, List, Optional, Set, Tuple
from aegis_core.utils.logger import logger

# Win32 Constants
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_KEYUP = 0x0101
WM_SYSKEYUP = 0x0105
VK_SPACE = 0x20
VK_MENU = 0x12       # Alt key
VK_CONTROL = 0x11    # Ctrl key
VK_SHIFT = 0x10      # Shift key
VK_LWIN = 0x5B       # Left Windows key
VK_RWIN = 0x5C       # Right Windows key
LLKHF_ALTDOWN = 0x20

# Safe cross-platform resolution
user32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None
kernel32 = ctypes.windll.kernel32 if hasattr(ctypes, "windll") else None

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

if user32:
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


# Mapping of common key names to Win32 Virtual Key codes
VK_MAP: Dict[str, int] = {
    "space": 0x20,
    "tab": 0x09,
    "enter": 0x0D,
    "return": 0x0D,
    "esc": 0x1B,
    "escape": 0x1B,
    "backquote": 0xC0,
    "`": 0xC0,
    "~": 0xC0,
    "tilde": 0xC0,
    "slash": 0xBF,
    "/": 0xBF,
    "backslash": 0xDC,
    "\\": 0xDC,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
}
# Function keys F1 to F12
for i in range(1, 13):
    VK_MAP[f"f{i}"] = 0x70 + (i - 1)
# Letters A-Z
for c in range(ord("a"), ord("z") + 1):
    VK_MAP[chr(c)] = c - 32
# Digits 0-9
for n in range(ord("0"), ord("9") + 1):
    VK_MAP[chr(n)] = n

# Standard user-friendly preset hotkeys
PRESET_HOTKEYS: List[Dict[str, str]] = [
    {"id": "Alt+Space", "label": "Alt + Space", "desc_ar": "النمط الافتراضي الشبيه بـ Spotlight"},
    {"id": "Ctrl+Space", "label": "Ctrl + Space", "desc_ar": "اختصار مألوف للمطورين"},
    {"id": "Ctrl+Shift+A", "label": "Ctrl + Shift + A", "desc_ar": "سريع بدون تعارض (Aegis)"},
    {"id": "Alt+Shift+A", "label": "Alt + Shift + A", "desc_ar": "سهل الوصول باليد اليسرى"},
    {"id": "Ctrl+Alt+Space", "label": "Ctrl + Alt + Space", "desc_ar": "ثلاثي فريد لمنع الضغط غير المقصود"},
    {"id": "F4", "label": "F4", "desc_ar": "زر مفرد وظيفي مباشر"},
    {"id": "F9", "label": "F9", "desc_ar": "زر علوي سريع"},
]


def parse_hotkey_string(hotkey_str: str) -> Tuple[int, bool, bool, bool, bool]:
    """
    Parses a hotkey string like 'Alt+Space', 'Ctrl+Shift+A', 'F4'.
    Returns: (target_vk, require_alt, require_ctrl, require_shift, require_win)
    """
    cleaned = hotkey_str.replace(" ", "").strip()
    if not cleaned:
        return VK_SPACE, True, False, False, False

    tokens = [t.lower() for t in cleaned.split("+") if t]
    modifiers: Set[str] = set()
    key_token = ""

    for tok in tokens:
        if tok in ("alt", "menu"):
            modifiers.add("alt")
        elif tok in ("ctrl", "control"):
            modifiers.add("ctrl")
        elif tok in ("shift",):
            modifiers.add("shift")
        elif tok in ("win", "super", "meta", "windows"):
            modifiers.add("win")
        else:
            key_token = tok

    req_alt = "alt" in modifiers
    req_ctrl = "ctrl" in modifiers
    req_shift = "shift" in modifiers
    req_win = "win" in modifiers

    target_vk = VK_MAP.get(key_token.lower(), VK_SPACE)
    return target_vk, req_alt, req_ctrl, req_shift, req_win


class GlobalHotkeyManager:
    """Manages global Windows keyboard hooks for instant companion summoning with customizable shortcuts."""

    def __init__(self, on_hotkey_pressed: Optional[Callable[[], None]] = None, hotkey: str = "Alt+Space"):
        self.on_hotkey_pressed = on_hotkey_pressed
        self.current_hotkey = hotkey or "Alt+Space"
        self._target_vk, self._req_alt, self._req_ctrl, self._req_shift, self._req_win = parse_hotkey_string(
            self.current_hotkey
        )
        self._lock = threading.Lock()

        self._hook: Optional[wintypes.HHOOK] = None
        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._c_callback = None
        self._ready_event = threading.Event()
        self._stop_event = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._ready_event.is_set() and not self._stop_event.is_set()

    def set_hotkey(self, hotkey_str: str) -> bool:
        """Dynamically reconfigures the monitored hotkey combination at runtime."""
        try:
            vk, alt, ctrl, shift, win = parse_hotkey_string(hotkey_str)
            with self._lock:
                self.current_hotkey = hotkey_str
                self._target_vk = vk
                self._req_alt = alt
                self._req_ctrl = ctrl
                self._req_shift = shift
                self._req_win = win
            logger.info("Global hotkey dynamically updated to: %s (VK=%s)", hotkey_str, hex(vk))
            return True
        except Exception as exc:
            logger.error("Failed to reconfigure hotkey '%s': %s", hotkey_str, exc)
            return False

    def _hook_proc(self, nCode: int, wParam: int, lParam: int) -> int:
        """Low-level hook callback executed on every system keystroke."""
        if not user32:
            return 0

        if nCode >= 0 and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            kbd = KBDLLHOOKSTRUCT.from_address(lParam)

            with self._lock:
                target_vk = self._target_vk
                req_alt = self._req_alt
                req_ctrl = self._req_ctrl
                req_shift = self._req_shift
                req_win = self._req_win
                active_str = self.current_hotkey

            if kbd.vkCode == target_vk:
                is_alt = bool(kbd.flags & LLKHF_ALTDOWN) or bool(user32.GetAsyncKeyState(VK_MENU) & 0x8000)
                is_ctrl = bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)
                is_shift = bool(user32.GetAsyncKeyState(VK_SHIFT) & 0x8000)
                is_win = bool(user32.GetAsyncKeyState(VK_LWIN) & 0x8000) or bool(
                    user32.GetAsyncKeyState(VK_RWIN) & 0x8000
                )

                matched = False
                if req_alt == is_alt and req_ctrl == is_ctrl and req_shift == is_shift and req_win == is_win:
                    matched = True
                # Backward-compatibility convenience: If default Alt+Space is set, Ctrl+Space also summons
                elif target_vk == VK_SPACE and active_str == "Alt+Space" and is_ctrl and not is_shift and not is_win:
                    matched = True

                if matched:
                    logger.info("Global shortcut (%s) intercepted. Summoning Aegis AI overlay.", active_str)
                    if self.on_hotkey_pressed:
                        try:
                            self.on_hotkey_pressed()
                        except Exception as exc:
                            logger.error("Error executing hotkey callback: %s", exc)
                    # Consume keypress so Windows default action does not activate
                    return 1

        return user32.CallNextHookEx(None, nCode, wParam, lParam)

    def _run_message_loop(self):
        """Dedicated background message pump for the Win32 hook."""
        if not user32 or not kernel32:
            logger.debug("Win32 API not available; hotkey hook skipped.")
            self._ready_event.set()
            return

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

        logger.info("Global hotkey hook (%s) installed successfully.", self.current_hotkey)
        self._ready_event.set()

        msg = wintypes.MSG()
        while not self._stop_event.is_set() and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self._hook:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None
            logger.info("Global hotkey hook uninstalled.")

    def start(self) -> None:
        """Starts the global hotkey listener in a daemon thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Hotkey listener is already running.")
            return

        self._ready_event.clear()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_message_loop, name="AegisHotkeyThread", daemon=True)
        self._thread.start()
        self._ready_event.wait(timeout=2.0)

    def stop(self) -> None:
        """Uninstalls the hook and stops the message loop."""
        self._stop_event.set()
        if self._thread_id and user32:
            WM_QUIT = 0x0012
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        self._ready_event.clear()


# Module-level singleton instance for application-wide hotkey coordination
hotkey_manager = GlobalHotkeyManager()
