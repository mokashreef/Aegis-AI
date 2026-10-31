"""
Unit tests for AI Runtime router, Ollama deep probing, model bootstrapper, and speed telemetry.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import pytest
from aegis_core.ai_runtime.base import LLMChunk, LLMMessage, LLMProvider, LLMResponse
from aegis_core.ai_runtime.ollama_provider import OllamaProvider
from aegis_core.ai_runtime.router import AIRuntimeRouter
from aegis_core.main import app


class MockEmptyOllamaProvider(LLMProvider):
    name = "ollama"

    async def is_available(self) -> bool:
        # Crucial Phase 2 fix: Available is False when zero models are downloaded!
        return False

    async def list_models(self):
        return []

    async def probe_health(self):
        return {
            "server_running": True,
            "installed_on_host": True,
            "status": "needs_model",
            "reason": "Ollama server is active, but zero models have been downloaded.",
            "models": [],
            "model_count": 0,
            "host": "http://localhost:11434",
            "recommended_models": [],
        }

    async def generate_stream(self, messages, model=None, tools=None, temperature=0.7):
        raise RuntimeError("No models installed.")

    async def generate(self, messages, model=None, tools=None, temperature=0.7):
        raise RuntimeError("No models installed.")


class MockReadyOllamaProvider(LLMProvider):
    name = "ollama"

    async def is_available(self) -> bool:
        return True

    async def list_models(self):
        return ["qwen2.5:1.5b"]

    async def probe_health(self):
        return {
            "server_running": True,
            "installed_on_host": True,
            "status": "ready",
            "reason": None,
            "models": ["qwen2.5:1.5b"],
            "model_count": 1,
            "host": "http://localhost:11434",
            "recommended_models": [],
        }

    async def generate_stream(self, messages, model=None, tools=None, temperature=0.7):
        yield LLMChunk(delta="Hello ", provider=self.name, model="qwen2.5:1.5b")
        yield LLMChunk(delta="from local Qwen!", provider=self.name, model="qwen2.5:1.5b")

    async def generate(self, messages, model=None, tools=None, temperature=0.7):
        return LLMResponse(content="Hello from local Qwen!", provider=self.name, model="qwen2.5:1.5b")


@pytest.mark.asyncio
async def test_ollama_empty_model_prevention():
    """Verify router does NOT attempt Ollama execution when no models are installed."""
    router = AIRuntimeRouter()
    router.ollama = MockEmptyOllamaProvider()

    # When Ollama has no models, is_available must be False
    assert await router.ollama.is_available() is False

    health = await router.get_system_status()
    assert health["ollama"]["status"] == "needs_model"


@pytest.mark.asyncio
async def test_tokens_per_second_telemetry():
    """Verify router records tokens/sec after streaming."""
    router = AIRuntimeRouter()
    router.ollama = MockReadyOllamaProvider()

    res = await router.chat([LLMMessage(role="user", content="Test")])
    assert res.content == "Hello from local Qwen!"
    assert router.last_tokens_per_second > 0.0


def test_ollama_installation_detection():
    """Verify host binary detection function runs cleanly."""
    detected = OllamaProvider.is_ollama_installed()
    assert isinstance(detected, bool)


@pytest.mark.asyncio
async def test_ollama_pull_model_stream():
    """Verify OllamaProvider.pull_model_stream parses NDJSON chunks and yields percentage."""
    provider = OllamaProvider()

    mock_lines = [
        json.dumps({"status": "pulling manifest"}),
        json.dumps({"status": "downloading", "total": 1000, "completed": 500}),
        json.dumps({"status": "verifying sha256"}),
        json.dumps({"status": "success"}),
    ]

    async def mock_aiter_lines():
        for line in mock_lines:
            yield line

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.aiter_lines = mock_aiter_lines

    mock_client = MagicMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.stream.return_value.__aenter__.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_client):
        chunks = []
        async for chunk in provider.pull_model_stream("qwen2.5:1.5b"):
            chunks.append(chunk)

        assert len(chunks) == 4
        assert chunks[0]["status"] == "pulling manifest"
        assert chunks[1]["percent"] == 50.0
        assert chunks[1]["completed_bytes"] == 500
        assert chunks[1]["total_bytes"] == 1000
        assert chunks[3]["status"] == "success"


def test_pull_model_api_endpoint():
    """Verify /api/models/pull streams SSE events with valid progress data."""
    client = TestClient(app)

    async def mock_pull_stream(model_name: str):
        yield {
            "status": "downloading",
            "total_bytes": 1000,
            "completed_bytes": 450,
            "percent": 45.0,
            "model": model_name,
        }
        yield {
            "status": "success",
            "total_bytes": 1000,
            "completed_bytes": 1000,
            "percent": 100.0,
            "model": model_name,
        }

    with patch("aegis_core.ai_runtime.ollama_provider.OllamaProvider.pull_model_stream", side_effect=mock_pull_stream):
        response = client.post("/api/models/pull", json={"model": "qwen2.5:1.5b"})
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        lines = response.text.strip().split("\n\n")
        assert len(lines) == 2
        assert lines[0].startswith("data: ")

        data0 = json.loads(lines[0][6:])
        assert data0["status"] == "downloading"
        assert data0["percent"] == 45.0

        data1 = json.loads(lines[1][6:])
        assert data1["status"] == "success"
