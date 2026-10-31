"""
Aegis AI - Windows Audio Volume Manager.
Controls master system volume and mute state via Windows CoreAudio API (pycaw).
"""

from typing import Any, Dict
from aegis_core.utils.logger import logger


class VolumeManager:
    """Manages Windows system audio endpoint volume and mute states."""

    @classmethod
    def _get_endpoint(cls):
        """Retrieves default speaker audio endpoint volume interface."""
        try:
            from pycaw.pycaw import AudioUtilities
            speakers = AudioUtilities.GetSpeakers()
            if hasattr(speakers, "EndpointVolume") and speakers.EndpointVolume:
                return speakers.EndpointVolume
            # Fallback for older pycaw versions
            interface = speakers.Activate(AudioUtilities.IAudioEndpointVolume._iid_, 0, None)
            return interface.QueryInterface(AudioUtilities.IAudioEndpointVolume)
        except Exception as exc:
            logger.warning("Could not access pycaw audio endpoint: %s", exc)
            return None

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Returns current master volume percentage and mute status."""
        endpoint = cls._get_endpoint()
        if not endpoint:
            return {"success": False, "error": "Audio endpoint not accessible", "level": 0, "is_muted": False}

        try:
            scalar = endpoint.GetMasterVolumeLevelScalar()
            level = round(scalar * 100)
            is_muted = bool(endpoint.GetMute())
            return {
                "success": True,
                "level": level,
                "is_muted": is_muted,
            }
        except Exception as exc:
            logger.error("Error reading volume: %s", exc)
            return {"success": False, "error": str(exc), "level": 0, "is_muted": False}

    @classmethod
    def set_volume(cls, level_percent: int) -> Dict[str, Any]:
        """Sets master volume to a percentage between 0 and 100."""
        endpoint = cls._get_endpoint()
        if not endpoint:
            return {"success": False, "error": "Audio endpoint not accessible"}

        clamped = max(0, min(100, level_percent))
        scalar = clamped / 100.0

        try:
            endpoint.SetMasterVolumeLevelScalar(scalar, None)
            # Unmute automatically if volume is raised
            if clamped > 0 and endpoint.GetMute():
                endpoint.SetMute(0, None)

            logger.info("Master audio volume set to %d%%.", clamped)
            return {
                "success": True,
                "level": clamped,
                "message": f"Volume set to {clamped}%.",
            }
        except Exception as exc:
            logger.error("Failed to set volume to %d%%: %s", clamped, exc)
            return {"success": False, "error": str(exc)}

    @classmethod
    def set_mute(cls, mute: bool) -> Dict[str, Any]:
        """Mutes or unmutes master audio output."""
        endpoint = cls._get_endpoint()
        if not endpoint:
            return {"success": False, "error": "Audio endpoint not accessible"}

        try:
            endpoint.SetMute(1 if mute else 0, None)
            action = "muted" if mute else "unmuted"
            logger.info("Master audio %s.", action)
            return {
                "success": True,
                "is_muted": mute,
                "message": f"Audio {action}.",
            }
        except Exception as exc:
            logger.error("Failed setting mute state: %s", exc)
            return {"success": False, "error": str(exc)}

    @classmethod
    def adjust_volume(cls, delta: int) -> Dict[str, Any]:
        """Increases or decreases volume by delta percentage."""
        status = cls.get_status()
        current = status.get("level", 50)
        target = current + delta
        return cls.set_volume(target)


# Global volume manager singleton
volume_manager = VolumeManager()

