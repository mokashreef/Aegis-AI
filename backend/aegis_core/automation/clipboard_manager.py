"""
Aegis AI - Windows Clipboard Controller.
Provides direct, thread-safe access to the Windows system clipboard using ctypes Win32 API.
"""

import ctypes
import os
from aegis_core.utils.logger import logger

# Win32 Constants
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


class ClipboardManager:
    """Interacts with the Windows clipboard via native user32 and kernel32 ctypes."""

    @staticmethod
    def get_text() -> str:
        """Reads plain unicode text currently stored in the clipboard."""
        if os.name != "nt":
            return ""

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        user32.OpenClipboard.argtypes = [ctypes.c_void_p]
        user32.OpenClipboard.restype = ctypes.c_bool
        user32.CloseClipboard.argtypes = []
        user32.CloseClipboard.restype = ctypes.c_bool
        user32.GetClipboardData.argtypes = [ctypes.c_uint]
        user32.GetClipboardData.restype = ctypes.c_void_p
        user32.IsClipboardFormatAvailable.argtypes = [ctypes.c_uint]
        user32.IsClipboardFormatAvailable.restype = ctypes.c_bool

        kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalUnlock.restype = ctypes.c_bool

        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return ""

        if not user32.OpenClipboard(None):
            logger.warning("Could not open Windows clipboard for reading.")
            return ""

        text = ""
        try:
            h_clip_mem = user32.GetClipboardData(CF_UNICODETEXT)
            if h_clip_mem:
                p_clip_mem = kernel32.GlobalLock(h_clip_mem)
                if p_clip_mem:
                    try:
                        text = ctypes.c_wchar_p(p_clip_mem).value or ""
                    finally:
                        kernel32.GlobalUnlock(h_clip_mem)
        except Exception as exc:
            logger.error("Error reading clipboard: %s", exc)
        finally:
            user32.CloseClipboard()

        return text

    @staticmethod
    def set_text(text: str) -> bool:
        """Writes unicode text to the Windows system clipboard."""
        if os.name != "nt":
            return False

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        user32.OpenClipboard.argtypes = [ctypes.c_void_p]
        user32.OpenClipboard.restype = ctypes.c_bool
        user32.EmptyClipboard.argtypes = []
        user32.EmptyClipboard.restype = ctypes.c_bool
        user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
        user32.SetClipboardData.restype = ctypes.c_void_p
        user32.CloseClipboard.argtypes = []
        user32.CloseClipboard.restype = ctypes.c_bool

        kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = ctypes.c_void_p
        kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalUnlock.restype = ctypes.c_bool

        if not user32.OpenClipboard(None):
            logger.warning("Could not open Windows clipboard for writing.")
            return False

        success = False
        try:
            user32.EmptyClipboard()
            # Unicode wchar characters + null terminator
            buffer_size = (len(text) + 1) * ctypes.sizeof(ctypes.c_wchar)
            h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, buffer_size)
            if h_mem:
                p_mem = kernel32.GlobalLock(h_mem)
                if p_mem:
                    try:
                        ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(p_mem), text)
                        user32.SetClipboardData(CF_UNICODETEXT, h_mem)
                        success = True
                    finally:
                        kernel32.GlobalUnlock(h_mem)
        except Exception as exc:
            logger.error("Error writing to clipboard: %s", exc)
        finally:
            user32.CloseClipboard()

        return success
