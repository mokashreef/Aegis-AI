"""
Aegis AI - Unit & Integration Tests for User Settings & Customization.
Verifies preferences persistence, language lock, voice catalog, and REST endpoints.
"""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from aegis_core.ai_runtime.base import LLMChunk, LLMMessage
from aegis_core.main import app
from aegis_core.memory.session_manager import session_manager


def test_session_manager_preferences():
    """Verify get_all_preferences and update_preferences in session_manager."""
    prefs = session_manager.get_all_preferences()
    assert "theme" in prefs
    assert "language" in prefs
    assert "auto_speak" in prefs
    assert "tts_voice" in prefs
    assert "global_hotkey" in prefs
    assert "quick_actions" in prefs

    # Update preferences
    updated = session_manager.update_preferences({"theme": "light", "auto_speak": True})
    assert updated["theme"] == "light"
    assert updated["auto_speak"] is True

    # Revert back
    session_manager.update_preferences({"theme": "dark", "auto_speak": False})


def test_settings_api_endpoints():
    """Verify GET and POST /api/settings endpoints."""
    client = TestClient(app)

    # 1. GET settings
    resp_get = client.get("/api/settings")
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert "theme" in data_get
    assert "language" in data_get
    assert "active_hotkey" in data_get
    assert "preset_hotkeys" in data_get
    assert "quick_actions" in data_get

    # 2. POST update settings
    resp_post = client.post(
        "/api/settings",
        json={"language": "ar", "tts_voice": "ar-SA-ZariyahNeural", "default_browser": "comet"},
    )
    assert resp_post.status_code == 200
    data_post = resp_post.json()
    assert data_post["language"] == "ar"
    assert data_post["tts_voice"] == "ar-SA-ZariyahNeural"
    assert data_post["default_browser"] == "comet"

    # Reset
    session_manager.update_preferences({"language": "auto", "tts_voice": "ar-SA-HamedNeural"})


def test_voice_catalog_and_preview_endpoints():
    """Verify GET /api/voice/catalog and POST /api/voice/preview endpoints."""
    client = TestClient(app)

    # 1. GET /api/voice/catalog
    resp_cat = client.get("/api/voice/catalog")
    assert resp_cat.status_code == 200
    voices = resp_cat.json()
    assert len(voices) >= 8

    # Verify presence of Arabic voices
    voice_ids = [v["id"] for v in voices]
    assert "ar-SA-HamedNeural" in voice_ids
    assert "ar-SA-ZariyahNeural" in voice_ids
    assert "en-US-AriaNeural" in voice_ids

    # 2. POST /api/voice/preview
    with patch(
        "aegis_core.voice.tts.tts_engine.synthesize_to_bytes",
        new=AsyncMock(return_value=b"fake-mp3-bytes"),
    ):
        resp_prev = client.post(
            "/api/voice/preview",
            json={"voice": "ar-SA-HamedNeural", "rate": "+0%"},
        )
        assert resp_prev.status_code == 200
        assert resp_prev.content == b"fake-mp3-bytes"


@pytest.mark.asyncio
async def test_ai_language_lock_injection():
    """Verify AIRouter injects forced Arabic/English system instructions when language is locked."""
    from aegis_core.ai_runtime.router import ai_router

    # Mock provider generate_stream
    captured_messages = []

    async def mock_generate_stream(messages, **kwargs):
        captured_messages.extend(messages)
        yield LLMChunk(delta="تم الرد", finish_reason="stop")

    mock_provider = AsyncMock()
    mock_provider.name = "ollama"
    mock_provider.generate_stream = mock_generate_stream

    with patch.object(ai_router, "get_active_provider", return_value=mock_provider):
        # 1. Lock to Arabic
        session_manager.set_preference("language", "ar")
        captured_messages.clear()
        res = [
            chunk
            async for chunk in ai_router.stream_chat(
                [LLMMessage(role="user", content="Hello, what time is it?")]
            )
        ]
        assert len(res) > 0
        assert any("اللغة العربية" in m.content for m in captured_messages if m.role == "system")

        # 2. Lock to English
        session_manager.set_preference("language", "en")
        captured_messages.clear()
        res2 = [
            chunk
            async for chunk in ai_router.stream_chat(
                [LLMMessage(role="user", content="كم الساعة الآن؟")]
            )
        ]
        assert len(res2) > 0
        assert any("English" in m.content for m in captured_messages if m.role == "system")

    # Reset
    session_manager.set_preference("language", "auto")


@pytest.mark.asyncio
async def test_open_url_tool_default_browser_preference():
    """Verify OpenUrlTool adopts preferred default browser when no specific browser is spoken."""
    from aegis_core.automation.system_tools import OpenUrlTool

    tool = OpenUrlTool()
    session_manager.set_preference("default_browser", "comet")

    with patch("subprocess.Popen") as mock_popen:
        res = await tool.execute(url="https://example.com", browser="")
        assert res.success is True
        assert res.data["browser"] == "comet"
        mock_popen.assert_called_once()

    # Reset
    session_manager.set_preference("default_browser", "chrome")


def test_clear_session_endpoint():
    """Verify POST /api/sessions/{session_id}/clear resets session messages."""
    client = TestClient(app)
    resp = client.post("/api/sessions/test-session-123/clear")
    assert resp.status_code == 200
    assert resp.json() == {"session_id": "test-session-123", "cleared": True}
