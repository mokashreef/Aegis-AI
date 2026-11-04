"""
Aegis AI - Local Ollama Provider.
Primary local inference engine for zero-cost, 100% private AI execution.
Includes deep server probing, model discovery, auto-server bootstrap, and model pulling.
"""

import json
import os
import shutil
import subprocess
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx
from aegis_core.ai_runtime.base import LLMChunk, LLMMessage, LLMProvider, LLMResponse
from aegis_core.config import settings
from aegis_core.utils.logger import logger


RECOMMENDED_MODELS = [
    {
        "id": "qwen2.5:1.5b",
        "name": "Qwen 2.5 (1.5B)",
        "size_mb": 986,
        "description": "Ultra-fast, low memory footprint. Optimal for CPUs and 8GB-16GB RAM PCs.",
    },
    {
        "id": "llama3.2:1b",
        "name": "Llama 3.2 (1B)",
        "size_mb": 1300,
        "description": "Meta's lightweight model. Highly capable reasoning with minimal RAM usage.",
    },
    {
        "id": "llama3.2:3b",
        "name": "Llama 3.2 (3B)",
        "size_mb": 2000,
        "description": "Balanced high-accuracy model for PCs with discrete GPU or 16GB+ RAM.",
    },
]


class OllamaProvider(LLMProvider):
    """Integrates with a locally running Ollama instance."""

    name = "ollama"

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.ollama_host).rstrip("/")

    @staticmethod
    def get_ollama_executable() -> Optional[str]:
        """Finds absolute path to the Ollama executable on the system."""
        p = shutil.which("ollama")
        if p:
            return p
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            standard_path = os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe")
            if os.path.exists(standard_path):
                return standard_path
        program_files = os.environ.get("ProgramFiles", "")
        if program_files:
            pf_path = os.path.join(program_files, "Ollama", "ollama.exe")
            if os.path.exists(pf_path):
                return pf_path
        return None

    @staticmethod
    def is_ollama_installed() -> bool:
        """Checks whether ollama executable exists on the Windows host."""
        return OllamaProvider.get_ollama_executable() is not None

    async def probe_health(self) -> Dict[str, Any]:
        """Performs deep health inspection of the Ollama server and installed models."""
        installed_on_host = self.is_ollama_installed()
        models = []
        server_running = False

        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    server_running = True
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except Exception:
            server_running = False

        if not server_running:
            status = "offline"
            reason = "Ollama daemon is not running." if installed_on_host else "Ollama is not installed on this system."
        elif len(models) == 0:
            status = "needs_model"
            reason = "Ollama server is active, but zero models have been downloaded."
        else:
            status = "ready"
            reason = None

        return {
            "server_running": server_running,
            "installed_on_host": installed_on_host,
            "status": status,
            "reason": reason,
            "models": models,
            "model_count": len(models),
            "host": self.base_url,
            "recommended_models": RECOMMENDED_MODELS,
        }

    async def is_available(self) -> bool:
        """Available ONLY if Ollama server is reachable AND at least one model is downloaded."""
        health = await self.probe_health()
        return health["status"] == "ready"

    async def list_models(self) -> List[str]:
        """Lists models installed in the local Ollama repository."""
        health = await self.probe_health()
        return health["models"]

    def ensure_server_started(self) -> bool:
        """Attempts to launch 'ollama serve' in background if not running."""
        exe = self.get_ollama_executable()
        if not exe:
            return False

        try:
            logger.info("Attempting to auto-start Ollama daemon (%s) in background...", exe)
            subprocess.Popen(
                [exe, "serve"],
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=(subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS) if os.name == "nt" else 0,
            )
            return True
        except Exception as exc:
            logger.error("Failed to auto-start Ollama: %s", exc)
            return False

    async def pull_model_stream(self, model_name: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Pulls a model from the Ollama library and streams percentage progress."""
        logger.info("Initiating Ollama pull for model: %s", model_name)
        payload = {"model": model_name, "stream": True}

        # Generous timeout for downloading model weights
        async with httpx.AsyncClient(timeout=1800.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json=payload,
            ) as response:
                if response.status_code != 200:
                    err_text = await response.aread()
                    raise RuntimeError(f"Ollama pull error ({response.status_code}): {err_text.decode('utf-8')}")

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        total = chunk.get("total", 0)
                        completed = chunk.get("completed", 0)
                        percent = round((completed / total) * 100, 1) if total > 0 else 0.0

                        yield {
                            "status": chunk.get("status", "downloading"),
                            "digest": chunk.get("digest", ""),
                            "total_bytes": total,
                            "completed_bytes": completed,
                            "percent": percent,
                            "model": model_name,
                        }
                    except json.JSONDecodeError:
                        continue

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[LLMChunk, None]:
        """Streams tokens from local Ollama instance via NDJSON."""
        models = await self.list_models()
        if not models:
            raise RuntimeError("Ollama has no models installed. Please pull a model first.")

        # If requested model isn't installed, pick the first available installed model
        target_model = model or settings.default_model
        if target_model not in models:
            # Check if base name matches (e.g. 'llama3.2' matching 'llama3.2:latest')
            matched = [m for m in models if m.startswith(target_model.split(":")[0])]
            target_model = matched[0] if matched else models[0]

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": [m.to_dict() for m in messages],
            "stream": True,
            "keep_alive": "30m",
            "options": {
                "temperature": temperature,
                "num_predict": 512,
            },
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
            if chunk.model:
                target_model = chunk.model

        return LLMResponse(
            content="".join(full_content),
            tool_calls=tool_calls,
            provider=self.name,
            model=target_model,
        )
