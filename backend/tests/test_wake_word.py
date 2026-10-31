"""
Unit and integration tests for the Aegis AI Wake Word Engine & Listener.
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient
from aegis_core.main import create_app
from aegis_core.voice.wake_word import WakeWordEngine, WakeWordListener


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_wake_word_engine_initialization():
    engine = WakeWordEngine()
    success = engine.load_models()
    assert success is True
    assert engine.is_initialized is True
    assert "hey_jarvis" in engine._classifiers or "alexa" in engine._classifiers


def test_wake_word_silence_gating():
    engine = WakeWordEngine()
    engine.load_models()

    # Silent audio (all zeros)
    silence = np.zeros(1280, dtype=np.float32)
    scores = engine.process_frame(silence, silence_threshold=0.01)

    assert isinstance(scores, dict)
    for score in scores.values():
        assert score == 0.0


def test_wake_word_synthetic_chunk_inference():
    engine = WakeWordEngine()
    engine.load_models()

    # Synthetic non-silent audio
    chunk = (np.random.randn(1280) * 0.1).astype(np.float32)
    scores = engine.process_frame(chunk, silence_threshold=0.001)

    assert isinstance(scores, dict)
    for name, score in scores.items():
        assert 0.0 <= score <= 1.0


def test_wake_word_listener_lifecycle():
    engine = WakeWordEngine()
    listener = WakeWordListener(engine=engine, wake_word="hey_jarvis", confidence_threshold=0.6)

    status = listener.get_status()
    assert status["is_running"] is False
    assert status["active_model"] == "hey_jarvis"
    assert status["confidence_threshold"] == 0.6

    events = []

    def on_detect(keyword, score):
        events.append((keyword, score))

    listener.register_callback(on_detect)
    assert len(listener._callbacks) == 1

    # Simulate detection dispatch
    listener._dispatch_detection("hey_jarvis", 0.85)
    assert len(events) == 1
    assert events[0] == ("hey_jarvis", 0.85)


def test_wake_word_api_endpoints(client):
    # 1. Status query
    res = client.get("/api/voice/wakeword/status")
    assert res.status_code == 200
    data = res.json()
    assert "is_running" in data
    assert "active_model" in data
    assert "confidence_threshold" in data

    # 2. Config update
    res_cfg = client.post(
        "/api/voice/wakeword/config",
        json={"wake_word": "alexa", "confidence_threshold": 0.75},
    )
    assert res_cfg.status_code == 200
    cfg_data = res_cfg.json()
    assert cfg_data["active_model"] == "alexa"
    assert cfg_data["confidence_threshold"] == 0.75

    # Reset config back to default
    client.post(
        "/api/voice/wakeword/config",
        json={"wake_word": "hey_jarvis", "confidence_threshold": 0.55},
    )
