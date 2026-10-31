"""
Unit tests for configuration and environment settings.
"""

from aegis_core.config import Settings


def test_settings_default_values():
    """Verify that default settings enforce the Zero API Key Guarantee."""
    s = Settings()
    assert s.app_name == "Aegis AI"
    assert s.port == 8420
    assert s.ollama_host == "http://localhost:11434"
    assert s.enable_cloud_fallback is True
    assert s.require_confirmation_for_destructive is True
    assert "notepad.exe" in s.allowed_apps


def test_settings_storage_resolution():
    """Ensure storage directory creation resolves properly."""
    s = Settings()
    assert s.storage_dir.exists()
    assert s.logs_dir.exists()
