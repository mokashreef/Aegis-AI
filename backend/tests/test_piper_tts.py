"""
Tests for Piper Offline Neural Arabic Speech Synthesis Engine.
"""

from unittest.mock import MagicMock, patch
import pytest
from aegis_core.voice.piper_engine import PiperNeuralEngine, PIPER_VOICE_CATALOG
from aegis_core.voice.tts import NeuralTTSEngine, VOICE_CATALOG


def test_piper_engine_catalog_and_status():
    """Verify Piper catalog contains official Arabic models and status is reportable."""
    engine = PiperNeuralEngine()
    status = engine.get_status()
    assert status["available"] is True
    assert "catalog" in status
    assert len(status["catalog"]) >= 2

    # Check model keys
    keys = [m["model_key"] for m in PIPER_VOICE_CATALOG]
    assert "ar_JO-kareem-medium" in keys
    assert "ar_JO-kareem-low" in keys


def test_piper_voices_exposed_in_tts_catalog():
    """Verify Piper offline voices are registered in primary TTS VOICE_CATALOG."""
    piper_voices = [v for v in VOICE_CATALOG if v["id"].startswith("piper-")]
    assert len(piper_voices) >= 2
    assert any("كريم" in v["name"] for v in piper_voices)


@pytest.mark.asyncio
async def test_piper_offline_neural_synthesis():
    """Verify Piper synthesis executes and returns audio bytes when model is loaded."""
    engine = PiperNeuralEngine()

    mock_voice = MagicMock()

    def fake_synthesize(text, wav_file):
        # Write valid minimal WAV header into output buffer
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22050)
        wav_file.writeframes(b"\x00\x00" * 50)

    mock_voice.synthesize = fake_synthesize

    with patch.object(engine, "load_voice", return_value=mock_voice):
        wav_bytes = engine.synthesize_wav_bytes("مرحباً بك في إيجيس", "ar_JO-kareem-medium")
        assert len(wav_bytes) > 44  # Valid WAV header is at least 44 bytes
        assert wav_bytes[:4] == b"RIFF"


@pytest.mark.asyncio
async def test_neural_tts_routes_to_piper():
    """Verify NeuralTTSEngine routes piper- prefixed voice IDs to PiperNeuralEngine."""
    tts = NeuralTTSEngine()

    with patch("aegis_core.voice.tts.piper_engine.is_model_installed", return_value=True):
        with patch(
            "aegis_core.voice.tts.piper_engine.synthesize_wav_bytes",
            return_value=b"RIFFFAKEAUDIOBYTES",
        ):
            audio = await tts.synthesize_to_bytes(
                text="تجربة النطق العصبي",
                voice="piper-ar_JO-kareem-medium",
            )
            assert audio == b"RIFFFAKEAUDIOBYTES"


@pytest.mark.asyncio
async def test_neural_tts_edge_fallback_to_piper():
    """Verify that when edge-tts fails, it recovers via offline Piper if model is installed."""
    tts = NeuralTTSEngine()

    with patch("edge_tts.Communicate", side_effect=RuntimeError("Network offline")):
        with patch("aegis_core.voice.tts.piper_engine.is_model_installed", return_value=True):
            with patch(
                "aegis_core.voice.tts.piper_engine.synthesize_wav_bytes",
                return_value=b"RIFFRECOVEREDAUDIO",
            ):
                audio = await tts.synthesize_to_bytes(
                    text="اختبار الاسترداد الصامت",
                    voice="ar-SA-HamedNeural",
                )
                assert audio == b"RIFFRECOVEREDAUDIO"

