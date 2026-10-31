"""
Unit tests for AI Runtime router and provider fallback mechanisms.
"""

import pytest
from aegis_core.ai_runtime.base import LLMChunk, LLMMessage, LLMProvider, LLMResponse
from aegis_core.ai_runtime.router import AIRuntimeRouter


class MockFailingProvider(LLMProvider):
    name = "mock_failing"

    async def is_available(self) -> bool:
        return False

    async def list_models(self):
        return []

    async def generate_stream(self, messages, model=None, tools=None, temperature=0.7):
        raise ConnectionError("Endpoint down")

    async def generate(self, messages, model=None, tools=None, temperature=0.7):
        raise ConnectionError("Endpoint down")


class MockHealthyProvider(LLMProvider):
    name = "mock_healthy"

    async def is_available(self) -> bool:
        return True

    async def list_models(self):
        return ["healthy-model-1"]

    async def generate_stream(self, messages, model=None, tools=None, temperature=0.7):
        yield LLMChunk(delta="Hello from ", provider=self.name)
        yield LLMChunk(delta="Aegis AI!", provider=self.name)

    async def generate(self, messages, model=None, tools=None, temperature=0.7):
        return LLMResponse(content="Hello from Aegis AI!", provider=self.name, model="healthy-model-1")


@pytest.mark.asyncio
async def test_router_fallback_resolution():
    """Verify router selects healthy provider when primary fails."""
    router = AIRuntimeRouter()
    router.ollama = MockFailingProvider()
    router.pollinations = MockHealthyProvider()

    provider = await router.get_active_provider()
    assert provider.name == "mock_healthy"

    # Test generation aggregation
    res = await router.chat([LLMMessage(role="user", content="Hi")])
    assert res.content == "Hello from Aegis AI!"
    assert res.provider == "mock_healthy"

