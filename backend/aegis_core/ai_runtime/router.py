"""
Aegis AI - AI Runtime Router & Intelligent Fallback Orchestrator.
Maintains the Zero API Key Guarantee by prioritizing local Ollama and smoothly falling back.
"""

from typing import Any, AsyncGenerator, Dict, List, Optional
from aegis_core.ai_runtime.base import LLMChunk, LLMMessage, LLMProvider, LLMResponse
from aegis_core.ai_runtime.ollama_provider import OllamaProvider
from aegis_core.ai_runtime.pollinations_provider import PollinationsProvider
from aegis_core.config import settings
from aegis_core.utils.logger import logger


class AIRuntimeRouter:
    """Dispatches generation requests to the best available zero-cost provider."""

    def __init__(self):
        self.ollama = OllamaProvider()
        self.pollinations = PollinationsProvider()

    async def get_active_provider(self) -> LLMProvider:
        """Determines the primary active inference provider."""
        if await self.ollama.is_available():
            return self.ollama

        if settings.enable_cloud_fallback and await self.pollinations.is_available():
            logger.info("Local Ollama offline. Routing to free fallback provider: Pollinations AI.")
            return self.pollinations

        # Default back to Ollama even if temporarily offline to trigger clear guidance
        return self.ollama

    async def get_system_status(self) -> Dict[str, Any]:
        """Returns health telemetry for AI runtime providers."""
        ollama_ok = await self.ollama.is_available()
        ollama_models = await self.ollama.list_models() if ollama_ok else []
        pollinations_ok = await self.pollinations.is_available()

        active_provider = "ollama" if ollama_ok else ("pollinations" if pollinations_ok else "offline")

        return {
            "active_provider": active_provider,
            "ollama": {
                "available": ollama_ok,
                "host": self.ollama.base_url,
                "models": ollama_models,
            },
            "pollinations_fallback": {
                "available": pollinations_ok,
                "enabled": settings.enable_cloud_fallback,
            },
            "zero_api_keys_enforced": True,
        }

    async def stream_chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[LLMChunk, None]:
        """Streams responses from the optimal provider with automatic fallback failover."""
        provider = await self.get_active_provider()

        try:
            async for chunk in provider.generate_stream(
                messages=messages,
                model=model,
                tools=tools,
                temperature=temperature,
            ):
                yield chunk
        except Exception as exc:
            logger.warning(
                "Inference stream failed on primary provider '%s': %s. Attempting fallback...",
                provider.name,
                exc,
            )
            # If Ollama failed and fallback is enabled, switch to Pollinations
            if provider.name == "ollama" and settings.enable_cloud_fallback:
                logger.info("Switching to Pollinations fallback...")
                yield LLMChunk(
                    delta="*[Switching to free zero-key fallback provider...]*\n\n",
                    provider="pollinations",
                    model="openai",
                )
                async for chunk in self.pollinations.generate_stream(
                    messages=messages,
                    model="openai",
                    temperature=temperature,
                ):
                    yield chunk
            else:
                raise

    async def chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Executes one-shot chat completion."""
        full_tokens = []
        tool_calls = None
        last_provider = "unknown"
        last_model = model or settings.default_model

        async for chunk in self.stream_chat(messages, model=model, tools=tools, temperature=temperature):
            if chunk.delta:
                full_tokens.append(chunk.delta)
            if chunk.tool_call_delta:
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(chunk.tool_call_delta)
            if chunk.provider:
                last_provider = chunk.provider
            if chunk.model:
                last_model = chunk.model

        return LLMResponse(
            content="".join(full_tokens),
            tool_calls=tool_calls,
            provider=last_provider,
            model=last_model,
        )


# Global AI runtime router instance
ai_router = AIRuntimeRouter()
