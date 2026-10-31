"""
Aegis AI - RESTful API Gateway.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from aegis_core.agent.planner import agent_planner
from aegis_core.ai_runtime.ollama_provider import OllamaProvider
from aegis_core.ai_runtime.router import ai_router
from aegis_core.config import settings
from aegis_core.memory.session_manager import session_manager
from aegis_core.plugins.registry import plugin_registry
from aegis_core.utils.system_info import get_system_telemetry
from aegis_core.voice.pipeline import voice_controller

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Conversational session ID")
    prompt: str = Field(description="User prompt or desktop command")
    user_confirmed: bool = Field(default=False, description="Whether user explicitly confirmed high-risk action")


class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(description="Name of the registered tool to invoke")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool execution parameters")
    user_confirmed: bool = Field(default=False, description="Confirmation flag for restricted tools")


class SpeakRequest(BaseModel):
    text: str = Field(description="Text to synthesize to speech")


class PullModelRequest(BaseModel):
    model: str = Field(default="qwen2.5:1.5b", description="Model identifier to pull from Ollama")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check and daemon metadata."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "zero_api_keys_enforced": True,
    }


@router.get("/system/status")
async def system_status() -> Dict[str, Any]:
    """Returns combined hardware, OS, voice, and AI runtime telemetry."""
    telemetry = get_system_telemetry()
    ai_status = await ai_router.get_system_status()
    voice_status = voice_controller.get_status()

    return {
        "telemetry": telemetry,
        "ai_runtime": ai_status,
        "voice": voice_status,
        "version": settings.app_version,
    }


@router.get("/runtime/health")
async def runtime_health() -> Dict[str, Any]:
    """Dedicated AI runtime diagnostic and model discovery."""
    return await ai_router.get_system_status()


@router.post("/ollama/start")
async def start_ollama_server() -> Dict[str, Any]:
    """Attempts to auto-launch local Ollama server if installed."""
    ollama = OllamaProvider()
    started = ollama.ensure_server_started()
    return {"started": started, "installed": ollama.is_ollama_installed()}


@router.post("/models/pull")
async def pull_model(req: PullModelRequest):
    """Streams model downloading progress from the Ollama library."""
    ollama = OllamaProvider()

    async def progress_generator():
        import json
        try:
            async for progress in ollama.pull_model_stream(req.model):
                yield f"data: {json.dumps(progress)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'status': 'error', 'error': str(exc)})}\n\n"

    return StreamingResponse(progress_generator(), media_type="text/event-stream")


@router.get("/models")
async def list_available_models() -> Dict[str, Any]:
    """Lists models available via local Ollama and zero-cost providers."""
    status = await ai_router.get_system_status()
    return status


@router.get("/sessions")
async def list_sessions(limit: int = Query(default=30, ge=1, le=100)) -> List[Dict[str, Any]]:
    """Retrieves conversation sessions."""
    return session_manager.list_sessions(limit=limit)


@router.post("/sessions")
async def create_session(title: str = "New Conversation") -> Dict[str, Any]:
    """Initializes a new conversational session."""
    session_id = session_manager.create_session(title=title)
    return {"session_id": session_id, "title": title}


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, limit: int = Query(default=100, ge=1, le=200)) -> List[Dict[str, Any]]:
    """Retrieves message history for a session."""
    return session_manager.get_messages(session_id=session_id, limit=limit)


@router.post("/chat")
async def post_chat(req: ChatRequest) -> Dict[str, Any]:
    """Non-streaming conversational endpoint."""
    session_id = req.session_id or session_manager.create_session(title="Quick Chat")
    chunks = []
    async for event in agent_planner.execute_task(
        user_prompt=req.prompt,
        session_id=session_id,
        user_confirmed=req.user_confirmed,
    ):
        if event.get("type") == "token":
            chunks.append(event.get("delta", ""))
        elif event.get("type") == "stream_end":
            return {
                "session_id": session_id,
                "content": event.get("full_content", "".join(chunks)),
            }

    return {"session_id": session_id, "content": "".join(chunks)}


@router.get("/tools")
async def list_tools() -> List[Dict[str, Any]]:
    """Lists registered desktop automation and utility tools."""
    return plugin_registry.list_tools()


@router.post("/tools/execute")
async def execute_tool(req: ToolExecuteRequest) -> Dict[str, Any]:
    """Executes a registered tool directly."""
    res = await plugin_registry.execute_tool(
        tool_name=req.tool_name,
        arguments=req.arguments,
        user_confirmed=req.user_confirmed,
    )
    return res.to_dict()


@router.post("/voice/speak")
async def speak_text(req: SpeakRequest) -> Dict[str, Any]:
    """Triggers local voice speech synthesis."""
    success = await voice_controller.speak_text(req.text)
    return {"success": success, "text": req.text}
