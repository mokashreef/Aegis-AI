"""
Aegis AI - Unit Tests for Native System Tray Companion Icon & Background Daemon Mode.
"""

from unittest.mock import MagicMock, patch
from PIL import Image
from aegis_core.desktop.tray import (
    TrayIconManager,
    generate_shield_icon,
    get_tray_icon_image,
)
from aegis_core.desktop.window import DesktopOverlayManager


def test_generate_shield_icon():
    """Verify shield icon generation creates a valid RGBA image with non-empty content."""
    img = generate_shield_icon(size=64)
    assert isinstance(img, Image.Image)
    assert img.size == (64, 64)
    assert img.mode == "RGBA"

    # Verify that image is not completely transparent
    extrema = img.getextrema()
    # Alpha channel extrema should have max > 0
    assert extrema[3][1] > 0


def test_get_tray_icon_image():
    """Verify tray icon retrieval loads or generates icon successfully."""
    img = get_tray_icon_image()
    assert isinstance(img, Image.Image)
    assert img.size[0] > 0 and img.size[1] > 0


def test_tray_manager_initialization_and_menu():
    """Verify tray manager initializes with correct properties and menu items."""
    mock_overlay = MagicMock()
    mock_quit = MagicMock()
    tray = TrayIconManager(overlay_manager=mock_overlay, on_quit=mock_quit)

    assert tray.is_running is False
    assert tray.overlay_manager is mock_overlay
    assert tray.on_quit is mock_quit

    menu = tray.build_menu()
    assert menu is not None

    menu_texts = [getattr(item, "text", "") for item in menu.items]
    assert any("Show Aegis AI" in t for t in menu_texts)
    assert any("Wake Word" in t for t in menu_texts)
    assert any("Open Companion Web HUD" in t for t in menu_texts)
    assert any("Exit Aegis AI" in t for t in menu_texts)


def test_tray_manager_actions():
    """Verify tray action callbacks execute corresponding subsystem handlers."""
    mock_overlay = MagicMock()
    mock_quit = MagicMock()
    tray = TrayIconManager(overlay_manager=mock_overlay, on_quit=mock_quit)

    # 1. Show action
    tray._on_show()
    mock_overlay.show.assert_called_once()

    # 2. Toggle wake word action
    with patch("aegis_core.voice.wake_word.wake_word_listener") as mock_ww:
        mock_ww.is_running = False
        tray._on_toggle_wake_word()
        mock_ww.start.assert_called_once()

        mock_ww.is_running = True
        tray._on_toggle_wake_word()
        mock_ww.stop.assert_called_once()

    # 3. Open web action
    with patch("webbrowser.open") as mock_open:
        tray._on_open_web()
        mock_open.assert_called_once()
        assert "http://" in mock_open.call_args[0][0]

    # 4. Exit action
    with patch.object(tray, "stop") as mock_stop:
        tray._on_exit()
        mock_stop.assert_called_once()
        mock_quit.assert_called_once()


def test_overlay_manager_close_interception():
    """Verify window close event is intercepted and hidden to tray rather than killed."""
    overlay = DesktopOverlayManager()
    assert overlay._quitting is False

    with patch.object(overlay, "hide") as mock_hide:
        # Closing when not quitting should hide to tray and return False to cancel destruction
        cancel_result = overlay._on_closing()
        assert cancel_result is False
        mock_hide.assert_called_once()

    # Calling quit should set quitting flag to True
    overlay.quit()
    assert overlay._quitting is True

    # Closing when quitting should allow destruction by returning True
    assert overlay._on_closing() is True
