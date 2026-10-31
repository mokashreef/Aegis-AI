"""
Aegis AI - Native Windows System Tray Companion Icon.
Manages the notification area icon, right-click context menu,
quick overlay summon, wake word toggling, and clean background daemon lifecycle.
"""

from typing import Callable, Optional
import webbrowser
from PIL import Image, ImageDraw
import pystray
from aegis_core.config import settings
from aegis_core.utils.logger import logger


def generate_shield_icon(size: int = 64) -> Image.Image:
    """
    Generates a crisp, high-definition Aegis AI shield icon with
    dark slate background, electric cyan border, and glowing central chevron.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    w, h = size, size
    shield = [
        (w * 0.5, h * 0.08),
        (w * 0.88, h * 0.22),
        (w * 0.82, h * 0.68),
        (w * 0.5, h * 0.94),
        (w * 0.18, h * 0.68),
        (w * 0.12, h * 0.22),
    ]

    # Fill shield with slate background
    draw.polygon(shield, fill=(15, 23, 42, 255))
    # Draw cyan border
    border_w = max(2, int(size * 0.05))
    draw.polygon(shield, outline=(6, 182, 212, 255), width=border_w)

    # Stylized central chevron 'A'
    chevron = [
        (w * 0.5, h * 0.28),
        (w * 0.70, h * 0.65),
        (w * 0.58, h * 0.65),
        (w * 0.5, h * 0.46),
        (w * 0.42, h * 0.65),
        (w * 0.30, h * 0.65),
    ]
    draw.polygon(chevron, fill=(56, 189, 248, 255))
    return img


def get_tray_icon_image() -> Image.Image:
    """Loads existing icon asset or generates dynamically and caches to assets directory."""
    assets_dir = settings.storage_dir.parent / "assets"
    png_path = assets_dir / "icon.png"

    if png_path.exists():
        try:
            return Image.open(png_path)
        except Exception as exc:
            logger.debug("Failed to read icon asset from %s: %s", png_path, exc)

    img = generate_shield_icon(64)
    try:
        assets_dir.mkdir(parents=True, exist_ok=True)
        img.save(png_path, "PNG")
        ico_path = assets_dir / "icon.ico"
        img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    except Exception as exc:
        logger.debug("Notice: Unable to persist icon asset to disk: %s", exc)

    return img


class TrayIconManager:
    """Manages the Windows notification area tray icon and menu dispatch."""

    def __init__(
        self,
        overlay_manager=None,
        on_quit: Optional[Callable[[], None]] = None,
    ):
        self.overlay_manager = overlay_manager
        self.on_quit = on_quit
        self._icon: Optional[pystray.Icon] = None
        self._is_running: bool = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def _is_wake_word_active(self) -> bool:
        try:
            from aegis_core.voice.wake_word import wake_word_listener

            return wake_word_listener.is_running
        except Exception:
            return False

    def _on_show(self, icon=None, item=None) -> None:
        logger.info("Tray menu: Showing Aegis AI overlay.")
        if self.overlay_manager:
            self.overlay_manager.show()

    def _on_toggle_wake_word(self, icon=None, item=None) -> None:
        try:
            from aegis_core.voice.wake_word import wake_word_listener

            if wake_word_listener.is_running:
                wake_word_listener.stop()
                logger.info("Tray menu: Wake word listener disabled.")
            else:
                wake_word_listener.start()
                logger.info("Tray menu: Wake word listener enabled.")

            if self._icon:
                self._icon.update_menu()
        except Exception as exc:
            logger.error("Error toggling wake word from tray: %s", exc)

    def _on_open_web(self, icon=None, item=None) -> None:
        web_url = f"http://{settings.host}:{settings.port}/"
        logger.info("Tray menu: Opening companion web HUD at %s", web_url)
        try:
            webbrowser.open(web_url)
        except Exception as exc:
            logger.error("Failed to open default browser: %s", exc)

    def _on_exit(self, icon=None, item=None) -> None:
        logger.info("Tray menu: Exit requested. Commencing clean application shutdown.")
        self.stop()
        if self.on_quit:
            try:
                self.on_quit()
            except Exception as exc:
                logger.error("Error in on_quit callback: %s", exc)
        elif self.overlay_manager:
            self.overlay_manager.quit()

    def build_menu(self) -> pystray.Menu:
        """Constructs the native right-click tray context menu."""
        return pystray.Menu(
            pystray.MenuItem("Show Aegis AI (Alt+Space)", self._on_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Wake Word: Hey Aegis",
                self._on_toggle_wake_word,
                checked=lambda item: self._is_wake_word_active(),
            ),
            pystray.MenuItem("Open Companion Web HUD", self._on_open_web),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit Aegis AI", self._on_exit),
        )

    def start(self) -> bool:
        """Starts the system tray icon detached on its own background thread."""
        if self._is_running:
            return True

        try:
            img = get_tray_icon_image()
            self._icon = pystray.Icon(
                name="AegisAI",
                icon=img,
                title="Aegis AI - Desktop Companion",
                menu=self.build_menu(),
            )
            self._icon.run_detached()
            self._is_running = True
            logger.info("System tray icon started successfully in background thread.")
            return True
        except Exception as exc:
            logger.error("Failed to start system tray icon: %s", exc)
            self._is_running = False
            return False

    def stop(self) -> None:
        """Stops and cleans up the notification area icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception as exc:
                logger.debug("Error stopping system tray icon: %s", exc)
            self._icon = None
        self._is_running = False
        logger.info("System tray icon stopped.")


# Global tray manager instance
tray_manager = TrayIconManager()
