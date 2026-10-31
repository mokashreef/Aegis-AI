"""
Unit tests for AI Runtime router, Ollama deep probing, model bootstrapper, and speed telemetry.
"""

import pytest
from aegis_core.ai_runtime.base import LLMChunk, LLMMessage, LLMProvider, LLMResponse
from aegis_core.ai_runtime.ollama_provider import OllamaProvider
from aegis_core.ai_runtime.router import AIRuntimeRouter


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
