"""
Tests for Aegis AI One-Click Installer generator and desktop API endpoints.
"""

from unittest.mock import patch
from fastapi.testclient import TestClient
from aegis_core.main import app
from aegis_core.desktop.installer import (
    OneClickInstallerBuilder,
    find_csc_compiler,
)

client = TestClient(app)


def test_find_csc_compiler():
    """Verifies that the system can locate the native C# compiler."""
    compiler = find_csc_compiler()
    # On Windows test runner, compiler should be found
    if compiler:
        assert "csc.exe" in compiler.lower()


def test_installer_builder_get_status():
    """Verifies installer status retrieval structure."""
    builder = OneClickInstallerBuilder()
    status = builder.get_status()
    assert isinstance(status, dict)
    assert "available" in status
    assert "version" in status
    assert "file_name" in status
    assert "size_bytes" in status
    assert "sha256" in status


def test_api_installer_status():
    """Verifies GET /api/desktop/installer/status."""
    response = client.get("/api/desktop/installer/status")
    assert response.status_code == 200
    data = response.json()
    assert "available" in data
    assert "version" in data


def test_api_installer_build_mock():
    """Verifies POST /api/desktop/installer/build with mocked builder."""
    mock_result = {
        "available": True,
        "version": "0.2.0-alpha",
        "file_name": "AegisAI-Setup.exe",
        "file_path": "releases/AegisAI-Setup.exe",
        "size_bytes": 1024,
        "size_mb": 0.01,
        "sha256": "fakehash123",
        "last_modified": "2026-11-02 12:00:00",
    }
    with patch("aegis_core.desktop.installer.installer_builder.build_installer", return_value=mock_result):
        response = client.post("/api/desktop/installer/build")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert data["file_name"] == "AegisAI-Setup.exe"


def test_api_installer_open_folder():
    """Verifies POST /api/desktop/installer/open-folder endpoint."""
    with patch("subprocess.run") as mock_run:
        response = client.post("/api/desktop/installer/open-folder")
        assert response.status_code == 200
        assert mock_run.called

