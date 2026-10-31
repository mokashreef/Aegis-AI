"""
Aegis AI - Local Ollama Provider.
Primary local inference engine for zero-cost, 100% private AI execution.
"""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx
from aegis_core.ai_runtime.base import LLMChunk, LLMMessage, LLMProvider, LLMResponse
from aegis_core.config import settings
from aegis_core.utils.logger import logger


class OllamaProvider(LLMProvider):
    """Integrates with a locally running Ollama instance."""

    name = "ollama"

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.ollama_host).rstrip("/")

    async def is_available(self) -> bool:
        """Checks if local Ollama daemon is reachable and responding."""
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """Lists models installed in the local Ollama repository."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except Exception as exc:
            logger.debug("Failed to query Ollama model list: %s", exc)
        return []

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[LLMChunk, None]:
        """Streams tokens from local Ollama instance via NDJSON."""
        target_model = model or settings.default_model
        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": [m.to_dict() for m in messages],
            "stream": True,
            "options": {"temperature": temperature},
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
            ) as response:
                if response.status_code != 200:
                    err_text = await response.aread()
                    raise RuntimeError(f"Ollama error ({response.status_code}): {err_text.decode('utf-8')}")

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk_json = json.loads(line)
                        msg = chunk_json.get("message", {})
                        delta = msg.get("content", "")
                        tool_calls = msg.get("tool_calls")
                        finish = "stop" if chunk_json.get("done") else None

                        yield LLMChunk(
                            delta=delta,
                            finish_reason=finish,
                            tool_call_delta=tool_calls[0] if tool_calls else None,
                            provider=self.name,
                            model=target_model,
                        )
                    except json.JSONDecodeError:
                        continue

    async def generate(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Aggregates a non-streamed response from Ollama."""
        full_content = []
        tool_calls = None
        target_model = model or settings.default_model

        async for chunk in self.generate_stream(messages, model=target_model, tools=tools, temperature=temperature):
            if chunk.delta:
                full_content.append(chunk.delta)
            if chunk.tool_call_delta:
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(chunk.tool_call_delta)

        return LLMResponse(
            content="".join(full_content),
            tool_calls=tool_calls,
            provider=self.name,
            model=target_model,
        )
