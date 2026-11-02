"""
Aegis AI - RESTful API Gateway.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from aegis_core.agent.planner import agent_planner
from aegis_core.ai_runtime.ollama_provider import OllamaProvider
from aegis_core.ai_runtime.router import ai_router
from aegis_core.config import settings
from aegis_core.memory.session_manager import session_manager
from aegis_core.plugins.registry import plugin_registry
from aegis_core.utils.logger import logger
from aegis_core.utils.system_info import get_system_telemetry
from aegis_core.voice.pipeline import voice_controller
from aegis_core.voice.tts import VOICE_CATALOG, tts_engine
from aegis_core.voice.wake_word import wake_word_listener

router = APIRouter()


class WakeWordConfigRequest(BaseModel):
    wake_word: Optional[str] = Field(default=None, description="Active wake word model name (e.g. hey_jarvis, alexa)")
    confidence_threshold: Optional[float] = Field(default=None, description="Confidence threshold [0.0 - 1.0]")


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
    voice: Optional[str] = Field(default=None, description="Neural voice identifier")
    rate: Optional[str] = Field(default=None, description="Speech rate adjustment")


class VoicePreviewRequest(BaseModel):
    voice: str = Field(description="Voice identifier to preview")
    text: Optional[str] = Field(default=None, description="Sample text to synthesize")
    rate: Optional[str] = Field(default="+0%", description="Speech speed adjustment")


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
        "wake_word": wake_word_listener.get_status(),
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


# -------------------------------------------------------------
# Real Voice Endpoints (Faster-Whisper STT & Edge Neural TTS)
# -------------------------------------------------------------

@router.get("/voice/voices")
async def get_available_voices() -> List[Dict[str, Any]]:
    """Returns available natural neural voices."""
    return VOICE_CATALOG


@router.post("/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Transcribes uploaded microphone audio using local Faster-Whisper."""
    cache_dir = settings.storage_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    temp_path = cache_dir / f"upload_{file.filename or 'input.webm'}"

    try:
        content = await file.read()
        temp_path.write_bytes(content)
        text = await voice_controller.transcribe_audio_file(temp_path)
        return {"text": text, "length": len(text), "success": True}
    except Exception as exc:
        logger.error("Audio upload transcription failed: %s", exc)
        return {"text": "", "error": str(exc), "success": False}
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


@router.post("/voice/synthesize")
async def synthesize_speech(req: SpeakRequest):
    """Generates natural neural speech audio bytes (MP3) for browser/webview playback."""
    audio_bytes = await tts_engine.synthesize_to_bytes(req.text, req.voice)
    if not audio_bytes:
        return Response(status_code=500, content="Failed to synthesize neural audio.")
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.post("/voice/speak")
async def speak_text(req: SpeakRequest) -> Dict[str, Any]:
    """Triggers voice speech output through Windows audio system."""
    success = await voice_controller.speak_text(req.text, req.voice)
    return {"success": success, "text": req.text}


@router.get("/voice/wakeword/status")
async def get_wakeword_status() -> Dict[str, Any]:
    """Returns the live telemetry and state of the background wake word listener."""
    return wake_word_listener.get_status()


@router.post("/voice/wakeword/toggle")
async def toggle_wakeword_listener() -> Dict[str, Any]:
    """Toggles active wake word detection on or off."""
    if wake_word_listener.is_running():
        wake_word_listener.stop()
    else:
        wake_word_listener.start()
    return wake_word_listener.get_status()


@router.post("/voice/wakeword/config")
async def update_wakeword_config(req: Dict[str, Any]) -> Dict[str, Any]:
    """Updates model or sensitivity for the wake word engine."""
    wake_word = req.get("wake_word")
    confidence = req.get("confidence_threshold")
    if wake_word:
        wake_word_listener.wake_word = wake_word
    if confidence is not None:
        wake_word_listener.confidence_threshold = float(confidence)
    return wake_word_listener.get_status()


# -------------------------------------------------------------
# User Settings & Personalization Endpoints
# -------------------------------------------------------------

@router.get("/settings")
async def get_user_settings() -> Dict[str, Any]:
    """Retrieves all user personalization settings, hotkey state, and startup configuration."""
    from aegis_core.desktop.hotkey import PRESET_HOTKEYS, hotkey_manager
    from aegis_core.desktop.startup import WindowsStartupManager
    from aegis_core.memory.session_manager import session_manager

    prefs = session_manager.get_all_preferences()
    prefs["start_with_windows"] = WindowsStartupManager.is_enabled()
    prefs["wake_word_enabled"] = wake_word_listener.is_running()
    prefs["active_hotkey"] = hotkey_manager.current_hotkey
    prefs["preset_hotkeys"] = PRESET_HOTKEYS
    return prefs


@router.post("/settings")
async def update_user_settings(req: Dict[str, Any]) -> Dict[str, Any]:
    """Updates user personalization settings and executes system side-effects."""
    from aegis_core.desktop.startup import WindowsStartupManager
    from aegis_core.memory.session_manager import session_manager

    # 1. Update persisted preferences
    updated = session_manager.update_preferences(req)

    # 2. Side-effect: Windows startup
    if "start_with_windows" in req:
        if req["start_with_windows"]:
            WindowsStartupManager.enable()
        else:
            WindowsStartupManager.disable()
        updated["start_with_windows"] = WindowsStartupManager.is_enabled()

    # 3. Side-effect: TTS default voice
    if "tts_voice" in req and req["tts_voice"]:
        tts_engine.default_voice = req["tts_voice"]

    # 4. Side-effect: Wake word state
    if "wake_word_enabled" in req:
        should_run = bool(req["wake_word_enabled"])
        if should_run and not wake_word_listener.is_running():
            wake_word_listener.start()
        elif not should_run and wake_word_listener.is_running():
            wake_word_listener.stop()
        updated["wake_word_enabled"] = wake_word_listener.is_running()

    # 5. Side-effect: Dynamic Hotkey configuration
    if "global_hotkey" in req and req["global_hotkey"]:
        from aegis_core.desktop.hotkey import hotkey_manager

        hotkey_manager.set_hotkey(req["global_hotkey"])
        updated["active_hotkey"] = hotkey_manager.current_hotkey

    return updated


@router.get("/desktop/hotkey")
async def get_desktop_hotkey() -> Dict[str, Any]:
    """Returns the currently active global hotkey and preset options."""
    from aegis_core.desktop.hotkey import PRESET_HOTKEYS, hotkey_manager
    from aegis_core.memory.session_manager import session_manager

    saved = session_manager.get_preference("global_hotkey", "Alt+Space")
    return {
        "current_hotkey": hotkey_manager.current_hotkey or saved,
        "is_running": hotkey_manager.is_running,
        "presets": PRESET_HOTKEYS,
    }


@router.post("/desktop/hotkey")
async def update_desktop_hotkey(req: Dict[str, Any]) -> Dict[str, Any]:
    """Dynamically updates the global hotkey and persists user preference."""
    new_hotkey = req.get("hotkey")
    if not new_hotkey:
        raise HTTPException(status_code=400, detail="Field 'hotkey' is required.")

    from aegis_core.desktop.hotkey import hotkey_manager
    from aegis_core.memory.session_manager import session_manager

    ok = hotkey_manager.set_hotkey(new_hotkey)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Failed to parse or register hotkey: {new_hotkey}")

    session_manager.set_preference("global_hotkey", new_hotkey)
    return {
        "success": True,
        "hotkey": hotkey_manager.current_hotkey,
        "message": f"Global shortcut updated to {hotkey_manager.current_hotkey}.",
    }


@router.get("/voice/catalog")
async def get_voice_catalog() -> List[Dict[str, Any]]:
    """Returns available natural neural voices with metadata and sample texts."""
    return VOICE_CATALOG


@router.post("/voice/preview")
async def preview_voice(req: VoicePreviewRequest):
    """Generates a short audio preview for any selected voice."""
    target_text = req.text
    if not target_text:
        for v in VOICE_CATALOG:
            if v["id"] == req.voice:
                target_text = v.get("sample_text", "مرحباً، هذه عينة صوتية لتجربة الصوت.")
                break
        if not target_text:
            target_text = "Hello, this is a sample audio preview for Aegis AI."

    audio_bytes = await tts_engine.synthesize_to_bytes(target_text, voice=req.voice, rate=req.rate)
    if not audio_bytes:
        return Response(status_code=500, content="Failed generating voice preview.")
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.post("/sessions/{session_id}/clear")
async def clear_session_history(session_id: str) -> Dict[str, Any]:
    """Clears message history for the specified session."""
    from aegis_core.memory.db import db_engine

    with db_engine.get_connection() as conn:
        conn.execute("DELETE FROM messages WHERE session_id = ?;", (session_id,))
        conn.execute("DELETE FROM tool_executions WHERE session_id = ?;", (session_id,))
    return {"session_id": session_id, "cleared": True}


@router.get("/desktop/installer/status")
async def get_installer_status() -> Dict[str, Any]:
    """Returns the availability and metadata of the One-Click Installer."""
    from aegis_core.desktop.installer import installer_builder

    return installer_builder.get_status()


@router.post("/desktop/installer/build")
async def build_desktop_installer() -> Dict[str, Any]:
    """Compiles and generates the standalone Windows One-Click Installer executable."""
    from aegis_core.desktop.installer import installer_builder

    try:
        return installer_builder.build_installer()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/desktop/installer/open-folder")
async def open_installer_folder() -> Dict[str, Any]:
    """Opens Windows Explorer with the compiled installer selected."""
    from aegis_core.desktop.installer import installer_builder

    return installer_builder.open_folder()


@router.post("/desktop/installer/run")
async def run_desktop_installer() -> Dict[str, Any]:
    """Launches the compiled installer executable."""
    from aegis_core.desktop.installer import installer_builder

    try:
        return installer_builder.launch_installer()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

