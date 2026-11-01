"""
Unit and integration tests for Aegis AI Voice Pipeline (STT & TTS).
Zero API keys, 100% local/free neural architecture.
"""

from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient
from aegis_core.main import create_app
from aegis_core.voice.pipeline import VoicePipelineController, VoiceState
from aegis_core.voice.stt import FasterWhisperEngine
from aegis_core.voice.tts import NeuralTTSEngine, VOICE_CATALOG


def test_voice_catalog():
    """Verify that voice catalog contains expected zero-API neural models."""
    assert len(VOICE_CATALOG) >= 2
    voice_ids = [v["id"] for v in VOICE_CATALOG]
    assert "en-US-AriaNeural" in voice_ids
    assert "en-US-GuyNeural" in voice_ids


def test_stt_engine_initialization_and_status():
    """Verify FasterWhisperEngine initial properties without downloading full weights."""
    stt = FasterWhisperEngine(model_size="tiny.en")
    assert stt.model_size == "tiny.en"
    assert stt.is_loaded() is False
    status = stt.get_status()
    assert status["device"] == "cpu"
    assert status["compute_type"] == "int8"
    assert status["loaded"] is False


def test_tts_engine_status():
    """Verify NeuralTTSEngine returns zero API key configuration."""
    tts = NeuralTTSEngine()
    status = tts.get_status()
    assert status["zero_api_keys"] is True
    assert status["backend"] == "edge_tts_neural"
    assert status["default_voice"] in ["ar-SA-HamedNeural", "en-US-AriaNeural"]


@pytest.mark.asyncio
async def test_voice_pipeline_speak_mocked():
    """Verify pipeline state transitions during speech synthesis."""
    controller = VoicePipelineController()
    controller.enabled = True

    with patch.object(controller.tts, "synthesize_to_bytes", new=AsyncMock(return_value=b"fake-mp3-bytes")):
        with patch("aegis_core.voice.pipeline.subprocess.Popen"):
            res = await controller.speak_text("Hello from Aegis AI")
            assert res is True
            assert controller.state == VoiceState.IDLE


@pytest.mark.asyncio
async def test_voice_api_endpoints():
    """Verify /api/voice/voices, /api/voice/speak, /api/voice/synthesize and /api/voice/transcribe."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Voice list
        voices_res = await client.get("/api/voice/voices")
        assert voices_res.status_code == 200
        voices = voices_res.json()
        assert any(v["id"] == "en-US-AriaNeural" for v in voices)

        # 2. Speak API
        with patch("aegis_core.voice.pipeline.voice_controller.speak_text", new=AsyncMock(return_value=True)):
            speak_res = await client.post("/api/voice/speak", json={"text": "Test greeting"})
            assert speak_res.status_code == 200
            assert speak_res.json()["success"] is True

        # 3. Synthesize API
        with patch("aegis_core.voice.tts.tts_engine.synthesize_to_bytes", new=AsyncMock(return_value=b"audio-data")):
            syn_res = await client.post("/api/voice/synthesize", json={"text": "Test audio synthesis"})
            assert syn_res.status_code == 200
            assert syn_res.headers["content-type"] == "audio/mpeg"
            assert syn_res.content == b"audio-data"

        # 4. Transcribe API
        with patch(
            "aegis_core.voice.pipeline.voice_controller.transcribe_audio_file",
            new=AsyncMock(return_value="open notepad"),
        ):
            files = {"file": ("test.webm", b"fake-audio-payload", "audio/webm")}
            trans_res = await client.post("/api/voice/transcribe", files=files)
            assert trans_res.status_code == 200
            data = trans_res.json()
            assert data["success"] is True
            assert data["text"] == "open notepad"

