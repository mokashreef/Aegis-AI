"""
Aegis AI - Free Remote Fallback Provider (Pollinations AI).
Provides anonymous, zero-API-key open inference when local Ollama is offline or uninstalled.
"""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx
from aegis_core.ai_runtime.base import LLMChunk, LLMMessage, LLMProvider, LLMResponse
from aegis_core.config import settings
from aegis_core.utils.logger import logger


class PollinationsProvider(LLMProvider):
    """Anonymous zero-key fallback provider using public endpoints."""

    name = "pollinations"
    BASE_URL = "https://text.pollinations.ai"

    async def is_available(self) -> bool:
        """Probes the public endpoint."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.BASE_URL}/models")
                return res.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """Lists available public models."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.BASE_URL}/models")
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list):
                        return [m.get("name", "") if isinstance(m, dict) else str(m) for m in data]
        except Exception as exc:
            logger.debug("Failed to list Pollinations models: %s", exc)
        return ["openai", "mistral", "qwen"]

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[LLMChunk, None]:
        """Streams generation from the free endpoint."""
        target_model = model or "openai"
        payload = {
            "messages": [m.to_dict() for m in messages],
            "model": target_model,
            "stream": True,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            try:
                async with client.stream(
                    "POST",
                    self.BASE_URL,
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        # Fallback to direct prompt endpoint if stream isn't accepted
                        last_prompt = messages[-1].content if messages else "Hello"
                        direct_res = await client.get(f"{self.BASE_URL}/{httpx.URL(last_prompt)}")
                        res_text = direct_res.text
                        if "Free limit reached" in res_text or direct_res.status_code == 429:
                            from aegis_core.ai_runtime.ollama_provider import OllamaProvider
                            OllamaProvider().ensure_server_started()
                            res_text = (
                                "⚠️ خادم الذكاء السحابي المجاني يواجه ضغطاً مؤقتاً (حد المعدل).\n"
                                "تم تشغيل محرك الذكاء المحلي (Ollama) تلقائياً على جهازك "
                                "لتوفير ردود سريعة ومجانية بدون إنترنت وبلا حدود."
                            )
                        yield LLMChunk(
                            delta=res_text,
                            finish_reason="stop",
                            provider=self.name,
                            model=target_model,
                        )
                        return

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            line_data = line[6:].strip()
                            if line_data == "[DONE]":
                                break
                            try:
                                data_obj = json.loads(line_data)
                                choices = data_obj.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {}).get("content", "")
                                    if delta:
                                        yield LLMChunk(
                                            delta=delta,
                                            provider=self.name,
                                            model=target_model,
                                        )
                            except json.JSONDecodeError:
                                pass
                        else:
                            if "Free limit reached" in line:
                                from aegis_core.ai_runtime.ollama_provider import OllamaProvider
                                OllamaProvider().ensure_server_started()
                                yield LLMChunk(
                                    delta=(
                                        "⚠️ خادم الذكاء السحابي المجاني يواجه ضغطاً مؤقتاً (حد المعدل).\n"
                                        "تم تشغيل محرك الذكاء المحلي (Ollama) تلقائياً على جهازك "
                                        "لتوفير ردود سريعة ومجانية بدون إنترنت وبلا حدود."
                                    ),
                                    provider=self.name,
                                    model=target_model,
                                )
                                return
                            yield LLMChunk(delta=line, provider=self.name, model=target_model)

            except Exception as exc:
                logger.error("Pollinations streaming failed: %s", exc)
                raise

    async def generate(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Aggregates a complete response."""
        full_text = []
        async for chunk in self.generate_stream(messages, model=model, tools=tools, temperature=temperature):
            if chunk.delta:
                full_text.append(chunk.delta)

        return LLMResponse(
            content="".join(full_text),
            provider=self.name,
            model=model or "openai",
        )

