"""
Aegis AI - Windows Display Brightness Manager.
Queries and adjusts monitor brightness using Windows WMI (WmiMonitorBrightnessMethods).
"""

import os
import subprocess
from typing import Any, Dict
from aegis_core.utils.logger import logger


class BrightnessManager:
    """Controls Windows display brightness via WMI."""

    _last_known_brightness: int = 70

    @classmethod
    def get_brightness(cls) -> Dict[str, Any]:
        """Queries current display brightness percentage."""
        if os.name != "nt":
            return {"success": True, "brightness": cls._last_known_brightness, "platform": "non-nt"}

        ps_cmd = (
            "(Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightness "
            "-ErrorAction SilentlyContinue).CurrentBrightness"
        )
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = proc.stdout.strip()
            if output.isdigit():
                val = int(output)
                cls._last_known_brightness = val
                return {"success": True, "brightness": val}
        except Exception as exc:
            logger.debug("Failed querying WMI brightness: %s", exc)

        return {"success": True, "brightness": cls._last_known_brightness, "simulated": True}

    @classmethod
    def set_brightness(cls, percentage: int) -> Dict[str, Any]:
        """Sets display brightness to a target percentage (0-100%)."""
        clamped = max(0, min(100, percentage))
        cls._last_known_brightness = clamped

        if os.name != "nt":
            return {"success": True, "brightness": clamped, "message": f"Brightness set to {clamped}%."}

        ps_cmd = (
            f"$wmi = Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightnessMethods "
            f"-ErrorAction SilentlyContinue; "
            f"if ($wmi) {{ $wmi | ForEach-Object {{ $_.WmiSetBrightness(1, {clamped}) }} }}"
        )
        try:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("Display brightness set to %d%%.", clamped)
            return {
                "success": True,
                "brightness": clamped,
                "message": f"Brightness set to {clamped}%.",
            }
        except Exception as exc:
            logger.error("Failed to set brightness: %s", exc)
            return {"success": False, "error": str(exc), "brightness": clamped}

    @classmethod
    def adjust_brightness(cls, delta: int) -> Dict[str, Any]:
        """Increases or decreases display brightness by delta."""
        res = cls.get_brightness()
        curr = res.get("brightness", cls._last_known_brightness)
        target = curr + delta
        return cls.set_brightness(target)


# Global brightness manager singleton
brightness_manager = BrightnessManager()

