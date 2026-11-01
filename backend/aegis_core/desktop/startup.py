"""
Aegis AI - Windows Startup Integration.
Manages automatic launch with Windows in the background via HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run.
100% offline, native Windows registry persistence.
"""

import os
import sys
from pathlib import Path
from aegis_core.utils.logger import logger

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "AegisAI"


class WindowsStartupManager:
    """Manages Windows startup autostart registration."""

    @staticmethod
    def get_executable_command() -> str:
        """Determines the best executable path for startup launch."""
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        exe_path = base_dir / "AegisAI.exe"
        if exe_path.exists():
            return f'"{exe_path}" --background'

        # Fallback to pythonw.exe in virtualenv
        pythonw = base_dir / ".venv" / "Scripts" / "pythonw.exe"
        aegis_py = base_dir / "aegis.py"
        if pythonw.exists() and aegis_py.exists():
            return f'"{pythonw}" "{aegis_py}" --background'

        return f'"{sys.executable}" "{aegis_py}" --background'

    @classmethod
    def is_enabled(cls) -> bool:
        """Checks if Aegis AI is registered in Windows Startup."""
        if os.name != "nt":
            return False

        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ) as key:
                try:
                    val, _ = winreg.QueryValueEx(key, APP_NAME)
                    return bool(val)
                except FileNotFoundError:
                    return False
        except Exception as exc:
            logger.debug("Error checking startup registry: %s", exc)
            return False

    @classmethod
    def enable(cls) -> bool:
        """Enables launching Aegis AI on Windows startup in background mode."""
        if os.name != "nt":
            return False

        try:
            import winreg

            cmd = cls.get_executable_command()
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            logger.info("Aegis AI successfully registered for Windows Startup: %s", cmd)
            return True
        except Exception as exc:
            logger.error("Failed to register Aegis AI for Windows Startup: %s", exc)
            return False

    @classmethod
    def disable(cls) -> bool:
        """Removes Aegis AI from Windows Startup."""
        if os.name != "nt":
            return False

        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    logger.info("Aegis AI successfully removed from Windows Startup.")
                    return True
                except FileNotFoundError:
                    return True
        except Exception as exc:
            logger.error("Failed to remove Aegis AI from Windows Startup: %s", exc)
            return False

    @classmethod
    def toggle(cls) -> bool:
        """Toggles Windows startup autostart state."""
        if cls.is_enabled():
            cls.disable()
            return False
        else:
            cls.enable()
            return True

