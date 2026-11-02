"""
Aegis AI - Native Windows Media Playback Control Manager.
Dispatches hardware multimedia keyboard events (Play, Pause, Next, Previous, Stop)
to globally control Spotify, YouTube, VLC, Apple Music, and Windows media players without focus.
"""

import platform
import time
from typing import Any, Dict

from aegis_core.utils.logger import logger

# Windows Virtual-Key Codes for Multimedia keys
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002


class MediaManager:
    """Dispatches global Windows hardware multimedia key events."""

    @classmethod
    def _send_media_key(cls, vk_code: int) -> bool:
        """Sends a hardware key-down and key-up event using Windows user32.dll."""
        if platform.system() != "Windows":
            logger.debug("Media keys simulated on non-Windows platform (VK: 0x%X).", vk_code)
            return True

        try:
            import ctypes

            user32 = ctypes.windll.user32
            # Key Down
            user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
            time.sleep(0.05)
            # Key Up
            user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
            return True
        except Exception as exc:
            logger.error("Failed to send media key 0x%X: %s", vk_code, exc)
            return False

    @classmethod
    def play_pause(cls) -> Dict[str, Any]:
        """Toggles play/pause state for active global media."""
        ok = cls._send_media_key(VK_MEDIA_PLAY_PAUSE)
        logger.info("Media action: Play/Pause toggle (success=%s)", ok)
        return {
            "success": ok,
            "action": "play_pause",
            "message": "تم تشغيل / إيقاف الوسائط مؤقتاً (Play/Pause).",
        }

    @classmethod
    def next_track(cls) -> Dict[str, Any]:
        """Skips to the next track."""
        ok = cls._send_media_key(VK_MEDIA_NEXT_TRACK)
        logger.info("Media action: Next Track (success=%s)", ok)
        return {
            "success": ok,
            "action": "next",
            "message": "تم الانتقال إلى المقطع التالي ⏭️.",
        }

    @classmethod
    def previous_track(cls) -> Dict[str, Any]:
        """Skips to the previous track."""
        ok = cls._send_media_key(VK_MEDIA_PREV_TRACK)
        logger.info("Media action: Previous Track (success=%s)", ok)
        return {
            "success": ok,
            "action": "previous",
            "message": "تم الرجوع إلى المقطع السابق ⏮️.",
        }

    @classmethod
    def stop(cls) -> Dict[str, Any]:
        """Stops media playback."""
        ok = cls._send_media_key(VK_MEDIA_STOP)
        logger.info("Media action: Stop (success=%s)", ok)
        return {
            "success": ok,
            "action": "stop",
            "message": "تم إيقاف تشغيل الوسائط ⏹️.",
        }

    @classmethod
    def execute_action(cls, action: str) -> Dict[str, Any]:
        """Executes a named media playback action."""
        act = action.lower().strip()
        if act in ["play", "pause", "play_pause", "toggle"]:
            return cls.play_pause()
        elif act in ["next", "skip", "forward"]:
            return cls.next_track()
        elif act in ["prev", "previous", "back"]:
            return cls.previous_track()
        elif act in ["stop"]:
            return cls.stop()
        else:
            return {
                "success": False,
                "error": f"Unknown media action '{action}'. Supported: play_pause, next, previous, stop.",
            }


media_manager = MediaManager()
