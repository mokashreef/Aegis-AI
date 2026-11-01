"""
Aegis AI - AI Runtime Router & Intelligent Fallback Orchestrator.
Maintains the Zero API Key Guarantee by prioritizing local Ollama and smoothly managing runtime states.
"""

import time
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
        self._last_tokens_per_second: float = 0.0

    @property
    def last_tokens_per_second(self) -> float:
        return self._last_tokens_per_second

    async def get_active_provider(self) -> LLMProvider:
        """Determines the primary active inference provider."""
        # Check if local Ollama is fully ready with installed models
        if await self.ollama.is_available():
            return self.ollama

        # If Ollama has no models or is offline, check fallback
        if settings.enable_cloud_fallback and await self.pollinations.is_available():
            logger.info("Local Ollama has no models or is offline. Using emergency fallback (Pollinations AI).")
            return self.pollinations

        return self.ollama

    async def get_system_status(self) -> Dict[str, Any]:
        """Returns health telemetry for AI runtime providers."""
        ollama_health = await self.ollama.probe_health()
        pollinations_ok = await self.pollinations.is_available()

        if ollama_health["status"] == "ready":
            active_provider = "ollama"
        elif pollinations_ok:
            active_provider = "pollinations_fallback"
        else:
            active_provider = "offline"

        return {
            "active_provider": active_provider,
            "tokens_per_second": self._last_tokens_per_second,
            "ollama": ollama_health,
            "pollinations_fallback": {
                "available": pollinations_ok,
                "enabled": settings.enable_cloud_fallback,
                "notice": "Emergency fallback only (rate limited to 1 request / 45s).",
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
        """Streams responses from the optimal provider with speed measurement and failover."""
        provider = await self.get_active_provider()
        ollama_health = (
            await self.ollama.probe_health()
            if hasattr(self.ollama, "probe_health")
            else {"status": "ready", "models": []}
        )

        # If Ollama is running but has no models, inform the user directly with action guidance
        needs_model = provider.name == "ollama" and ollama_health["status"] == "needs_model"
        if needs_model and not settings.enable_cloud_fallback:
            yield LLMChunk(
                delta=(
                    "⚠️ **No local AI model installed.**\n\n"
                    "Ollama is running, but you have not downloaded a model yet.\n"
                    "Please click the **Install Model** button in the top banner or run:\n"
                    "```powershell\nollama run qwen2.5:1.5b\n```\n"
                ),
                provider="system",
                model="none",
                finish_reason="stop",
            )
            return

        # Enforce user language lock preference (e.g. Always Arabic or Always English)
        from aegis_core.memory.session_manager import session_manager
        lang_pref = session_manager.get_preference("language", "auto")
        effective_messages = list(messages)
        if lang_pref == "ar":
            ar_inst = (
                "توجيه إلزامي ومحدد: لقد حدد المستخدم لغة الرد لتكون اللغة العربية دائماً. "
                "يجب عليك دوماً صياغة كامل ردك باللغة العربية الفصحى، "
                "حتى لو كتب المستخدم أو تحدث بالإنجليزية أو أي لغة أخرى."
            )
            if effective_messages and effective_messages[0].role == "system":
                effective_messages[0] = LLMMessage(
                    role="system",
                    content=f"{effective_messages[0].content}\n\n{ar_inst}",
                )
            else:
                effective_messages.insert(0, LLMMessage(role="system", content=ar_inst))
        elif lang_pref == "en":
            en_inst = (
                "MANDATORY INSTRUCTION: The user has locked the response language to English. "
                "You must strictly formulate your entire response in clear English, "
                "even if the user writes or speaks in Arabic or another language."
            )
            if effective_messages and effective_messages[0].role == "system":
                effective_messages[0] = LLMMessage(
                    role="system",
                    content=f"{effective_messages[0].content}\n\n{en_inst}",
                )
            else:
                effective_messages.insert(0, LLMMessage(role="system", content=en_inst))

        start_time = time.perf_counter()
        token_count = 0

        try:
            async for chunk in provider.generate_stream(
                messages=effective_messages,
                model=model,
                tools=tools,
                temperature=temperature,
            ):
                if chunk.delta:
                    token_count += 1
                yield chunk

            elapsed = time.perf_counter() - start_time
            if elapsed > 0 and token_count > 0:
                self._last_tokens_per_second = round(token_count / elapsed, 1)

        except Exception as exc:
            logger.warning(
                "Inference stream failed on primary provider '%s': %s. Attempting emergency fallback...",
                provider.name,
                exc,
            )
            if provider.name == "ollama" and settings.enable_cloud_fallback:
                yield LLMChunk(
                    delta="*[Local model unavailable; connecting to emergency fallback...]*\n\n",
                    provider="pollinations",
                    model="openai",
                )
                async for chunk in self.pollinations.generate_stream(
                    messages=effective_messages,
                    model="openai",
                    temperature=temperature,
                ):
                    if chunk.delta:
                        token_count += 1
                    yield chunk

                elapsed = time.perf_counter() - start_time
                if elapsed > 0 and token_count > 0:
                    self._last_tokens_per_second = round(token_count / elapsed, 1)
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
