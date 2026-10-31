"""
Aegis AI - Native Desktop Overlay Window Manager.
Integrates Microsoft WebView2 through pywebview to provide a frameless,
AlwaysOnTop, multi-monitor centered glassmorphic desktop companion.
"""

import ctypes
from ctypes import wintypes
from typing import Dict, Optional
import webview
from aegis_core.config import settings
from aegis_core.utils.logger import logger

user32 = ctypes.windll.user32


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


def get_active_monitor_bounds(width: int = 760, height: int = 620) -> Dict[str, int]:
    """Computes window coordinates centered on the active display where user cursor is located."""
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    h_monitor = user32.MonitorFromPoint(pt, 2)  # MONITOR_DEFAULTTONEAREST

    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    user32.GetMonitorInfoW(h_monitor, ctypes.byref(mi))

    work_w = mi.rcWork.right - mi.rcWork.left
    work_h = mi.rcWork.bottom - mi.rcWork.top

    # Ensure overlay fits on small displays
    target_w = min(width, max(360, work_w - 40))
    target_h = min(height, max(400, work_h - 40))

    # Center horizontally, place at 1/4 from top for natural spotlight alignment
    x = mi.rcWork.left + (work_w - target_w) // 2
    y = mi.rcWork.top + (work_h - target_h) // 4

    return {"x": max(0, x), "y": max(0, y), "width": target_w, "height": target_h}


class AegisDesktopBridge:
    """JS-accessible bridge for client-side window control."""

    def __init__(self, overlay_manager: "DesktopOverlayManager"):
        self.overlay_manager = overlay_manager

    def hide(self) -> None:
        """Hides the overlay window."""
        self.overlay_manager.hide()

    def show(self) -> None:
        """Shows the overlay window."""
        self.overlay_manager.show()

    def toggle(self) -> None:
        """Toggles overlay visibility."""
        self.overlay_manager.toggle()

    def ping(self) -> str:
        """Sanity ping from HUD."""
        return "pong"


class DesktopOverlayManager:
    """Controls the native Windows WebView2 overlay window."""

    def __init__(self, url: Optional[str] = None):
        self.url = url or f"http://{settings.host}:{settings.port}/"
        self._window: Optional[webview.Window] = None
        self._is_visible = False
        self._bridge = AegisDesktopBridge(self)

    @property
    def is_visible(self) -> bool:
        return self._is_visible

    def create_window(self) -> webview.Window:
        """Instantiates the frameless always-on-top window."""
        bounds = get_active_monitor_bounds(width=760, height=620)

        self._window = webview.create_window(
            title="Aegis AI",
            url=self.url,
            width=bounds["width"],
            height=bounds["height"],
            x=bounds["x"],
            y=bounds["y"],
            frameless=True,
            on_top=True,
            transparent=True,
            js_api=self._bridge,
            easy_drag=False,
            shadow=True,
        )

        self._window.events.shown += self._on_shown
        self._window.events.hidden += self._on_hidden
        self._window.events.closed += self._on_closed
        return self._window

    def _on_shown(self):
        self._is_visible = True
        logger.debug("Overlay window shown.")

    def _on_hidden(self):
        self._is_visible = False
        logger.debug("Overlay window hidden.")

    def _on_closed(self):
        self._is_visible = False
        self._window = None
        logger.debug("Overlay window closed.")

    def show(self) -> None:
        """Brings the overlay into view and centers it on the current monitor."""
        if not self._window:
            return

        try:
            # Re-center on active monitor where cursor currently is
            bounds = get_active_monitor_bounds(width=self._window.width, height=self._window.height)
            self._window.move(bounds["x"], bounds["y"])
            self._window.show()
            self._is_visible = True
        except Exception as exc:
            logger.error("Error showing overlay window: %s", exc)

    def hide(self) -> None:
        """Dismisses the overlay window."""
        if not self._window:
            return

        try:
            self._window.hide()
            self._is_visible = False
        except Exception as exc:
            logger.error("Error hiding overlay window: %s", exc)

    def toggle(self) -> None:
        """Toggles between visible and hidden states."""
        if self._is_visible:
            self.hide()
        else:
            self.show()

    def start_gui_loop(self) -> None:
        """Starts the pywebview UI loop on the main thread."""
        logger.info("Starting native Windows desktop overlay GUI loop (WebView2)...")
        webview.start(debug=settings.debug)


# Global overlay singleton
overlay_manager = DesktopOverlayManager()
