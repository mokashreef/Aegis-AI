"""
Aegis AI - Production Validation Benchmark: Model System Matrix.
Empirically tests:
1. Ollama installation and running status
2. Empty model crash prevention
3. Model bootstrapper endpoint
4. Offline fallback resilience
5. First token latency & generation speed (tokens/sec)
"""

import asyncio
import json
from pathlib import Path
import time
from httpx import ASGITransport, AsyncClient
from aegis_core.ai_runtime.base import LLMMessage
from aegis_core.ai_runtime.ollama_provider import OllamaProvider
from aegis_core.ai_runtime.router import ai_router
from aegis_core.main import create_app

EVIDENCE_DIR = Path(".github/validation_evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


async def benchmark_model_system():
    results = {}
    print("=== EXECUTING MODEL SYSTEM VALIDATION MATRIX ===")

    # 1. Probe Live Ollama Server
    ollama = OllamaProvider()
    probe = await ollama.probe_health()
    available = await ollama.is_available()

    results["ollama_probe"] = {
        "installed_binary": probe.get("installed", False),
        "server_running": probe.get("reachable", False),
        "model_count": probe.get("model_count", 0),
        "installed_models": probe.get("models", []),
        "provider_available_gate": available,
        "recommendation": probe.get("recommendation"),
    }
    inst = probe.get('installed')
    reach = probe.get('reachable')
    m_count = probe.get('model_count')
    print(f"Ollama Probe: Installed={inst}, Running={reach}, Models={m_count}")

    # 2. Simulate Ollama Empty Model (Crash Prevention Gate)
    simulated_empty_provider = OllamaProvider()
    simulated_empty_provider._last_probe = {"installed": True, "reachable": True, "model_count": 0, "models": []}
    simulated_empty_provider._probe_timestamp = time.time()
    empty_gate = await simulated_empty_provider.is_available()
    results["empty_model_crash_prevention"] = {
        "scenario": "Server running but 0 models installed",
        "gate_status": "BLOCKED" if not empty_gate else "FAILED",
        "prevented_404_crash": not empty_gate,
    }
    print(f"Empty Model Gate: {'PASSED (Blocked 404)' if not empty_gate else 'FAILED'}")

    # 3. Test Offline Fallback & First Token Latency
    test_messages = [
        LLMMessage(role="system", content="You are Aegis AI."),
        LLMMessage(role="user", content="Respond with exactly: 'Aegis System Ready'"),
    ]

    t0 = time.perf_counter()
    first_token_latency_ms = None
    chunks = []
    active_provider = "unknown"
    active_model = "unknown"

    try:
        async for chunk in ai_router.stream_chat(test_messages):
            if chunk.delta and first_token_latency_ms is None:
                first_token_latency_ms = (time.perf_counter() - t0) * 1000.0
            if chunk.delta:
                chunks.append(chunk.delta)
            if chunk.provider:
                active_provider = chunk.provider
            if chunk.model:
                active_model = chunk.model
    except Exception as exc:
        print(f"Inference error: {exc}")

    total_time_ms = (time.perf_counter() - t0) * 1000.0
    full_text = "".join(chunks).strip()
    total_tokens = len(full_text.split())
    tokens_per_sec = (total_tokens / (total_time_ms / 1000.0)) if total_time_ms > 0 else 0.0

    results["inference_telemetry"] = {
        "active_provider": active_provider,
        "active_model": active_model,
        "first_token_latency_ms": round(first_token_latency_ms, 2) if first_token_latency_ms else None,
        "total_latency_ms": round(total_time_ms, 2),
        "tokens_per_sec": round(tokens_per_sec, 2),
        "output_length_chars": len(full_text),
        "output_snippet": full_text[:100],
        "graceful_fallback": bool(full_text),
    }
    print(f"Inference: Provider={active_provider}, 1st Token={first_token_latency_ms}ms, Output: '{full_text[:50]}...'")

    # 4. Test Model Bootstrapper API (/api/models/pull)
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test pulling invalid or test model stream response
        pull_req = await client.post("/api/models/pull", json={"model_name": "qwen2.5:1.5b"})
        results["bootstrapper_endpoint"] = {
            "status_code": pull_req.status_code,
            "content_type": pull_req.headers.get("content-type"),
            "success": pull_req.status_code == 200,
        }
        print(f"Bootstrapper API Status: {pull_req.status_code}")

    evidence_file = EVIDENCE_DIR / "section4_model_system.json"
    evidence_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved model system audit to {evidence_file}")
    return results


if __name__ == "__main__":
    asyncio.run(benchmark_model_system())

