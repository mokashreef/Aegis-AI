"""
Aegis AI - Core Daemon Entrypoint.
Starts the FastAPI application, mounts compiled desktop UI assets, registers system tools,
and exposes the HTTP/WebSocket gateway for native desktop interaction.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from aegis_core.ai_runtime.router import ai_router
from aegis_core.api.routes import router as api_router
from aegis_core.api.websocket import ws_router
from aegis_core.automation.system_tools import (
    BrightnessControlTool,
    CloseAppTool,
    FocusWindowByTitleTool,
    FocusWindowTool,
    GetClipboardTool,
    GetSystemTelemetryTool,
    LaunchAppTool,
    ListProcessesTool,
    ListWindowsTool,
    MinimizeAllWindowsTool,
    OpenUrlTool,
    QuickNotesTool,
    ScreenCaptureTool,
    AnalyzeScreenTool,
    QueryDocumentTool,
    SetTimerTool,
    SetReminderTool,
    ListRemindersTool,
    CancelReminderTool,
    SetClipboardTool,
    SnapWindowTool,
    VolumeControlTool,
)
from aegis_core.config import settings
from aegis_core.desktop.window import overlay_manager
from aegis_core.memory.db import db_engine
from aegis_core.plugins.registry import plugin_registry
from aegis_core.utils.logger import logger


def register_default_tools() -> None:
    """Registers core desktop automation tools into the registry idempotently."""
    tools = [
        LaunchAppTool(),
        OpenUrlTool(),
        CloseAppTool(),
        ListProcessesTool(),
        GetClipboardTool(),
        SetClipboardTool(),
        ListWindowsTool(),
        FocusWindowTool(),
        FocusWindowByTitleTool(),
        MinimizeAllWindowsTool(),
        SnapWindowTool(),
        VolumeControlTool(),
        BrightnessControlTool(),
        ScreenCaptureTool(),
        AnalyzeScreenTool(),
        QueryDocumentTool(),
        SetTimerTool(),
        SetReminderTool(),
        ListRemindersTool(),
        CancelReminderTool(),
        QuickNotesTool(),
        GetSystemTelemetryTool(),
    ]
    for t in tools:
        if not plugin_registry.get(t.name):
            plugin_registry.register(t)


# Register immediately on module load so CLI/testing has immediate access
register_default_tools()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle supervisor."""
    logger.info("Initializing %s v%s...", settings.app_name, settings.app_version)

    # 1. Ensure storage directory and database schemas
    settings.ensure_directories()
    db_engine.init_db()

    # 2. Register tools
    register_default_tools()
    logger.info("Registered %d built-in desktop automation tools.", len(plugin_registry.list_tools()))

    # 3. Probe AI Runtime Matrix and ensure local Ollama daemon starts if installed
    try:
        from aegis_core.ai_runtime.ollama_provider import OllamaProvider

        ollama_p = OllamaProvider()
        health = await ollama_p.probe_health()
        if ollama_p.is_ollama_installed() and not health.get("server_running"):
            logger.info("Ollama is installed on host; auto-launching daemon in background...")
            ollama_p.ensure_server_started()
    except Exception as ex:
        logger.debug("Ollama background auto-start check: %s", ex)

    runtime_status = await ai_router.get_system_status()
    logger.info(
        "AI Runtime initialized. Active: %s (Ollama Available: %s, Fallbacks Enabled: %s)",
        runtime_status["active_provider"],
        runtime_status["ollama"].get("server_running", False),
        runtime_status["pollinations_fallback"]["enabled"],
    )

    from aegis_core.voice.wake_word import wake_word_listener

    if settings.wake_word_enabled:
        wake_word_listener.wake_word = settings.wake_word_model
        wake_word_listener.confidence_threshold = settings.wake_word_threshold
        wake_word_listener.start()

    # Start background reminder scheduler worker
    async def _run_reminders_worker():
        from aegis_core.automation.reminder_manager import reminder_manager

        while True:
            try:
                due = reminder_manager.check_due_reminders()
                for r in due:
                    await reminder_manager.trigger_alert(r)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.debug("Reminder loop tick error: %s", exc)
            await asyncio.sleep(1.0)

    reminders_task = asyncio.create_task(_run_reminders_worker())

    yield

    logger.info("Shutting down %s daemon...", settings.app_name)
    reminders_task.cancel()
    try:
        await reminders_task
    except asyncio.CancelledError:
        pass

    from aegis_core.voice.wake_word import wake_word_listener

    wake_word_listener.stop()


def create_app() -> FastAPI:
    """Factory creating and configuring the primary FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Autonomous, local-first Windows AI companion daemon and automation core.",
        lifespan=lifespan,
    )

    # Configure CORS for local overlay and web development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Desktop window control endpoints
    @app.post("/api/desktop/toggle")
    async def toggle_desktop_overlay():
        overlay_manager.toggle()
        return {"visible": overlay_manager.is_visible}

    @app.post("/api/desktop/hide")
    async def hide_desktop_overlay():
        overlay_manager.hide()
        return {"visible": False}

    @app.post("/api/desktop/pin")
    async def toggle_desktop_pin():
        new_state = overlay_manager.toggle_on_top()
        return {"on_top": new_state, "is_on_top": new_state}

    @app.get("/api/desktop/pin")
    async def get_desktop_pin():
        return {"on_top": overlay_manager.is_on_top, "is_on_top": overlay_manager.is_on_top}

    @app.get("/api/desktop/startup")
    async def get_startup_status():
        from aegis_core.desktop.startup import WindowsStartupManager

        return {"enabled": WindowsStartupManager.is_enabled()}

    @app.post("/api/desktop/startup/toggle")
    async def toggle_startup_status():
        from aegis_core.desktop.startup import WindowsStartupManager

        new_state = WindowsStartupManager.toggle()
        return {"enabled": new_state}

    # Mount REST and WebSocket routers
    app.include_router(api_router, prefix="/api")
    app.include_router(ws_router)

    # Mount compiled React HUD static assets if dist exists
    frontend_dist = Path(__file__).resolve().parent.parent.parent / "apps" / "desktop-ui" / "dist"
    if frontend_dist.exists() and (frontend_dist / "index.html").exists():
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            file_path = frontend_dist / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(frontend_dist / "index.html")

        logger.info("Mounted static desktop UI bundle from: %s", frontend_dist)
    else:
        logger.warning("Desktop UI bundle missing at: %s. Serving fallback status page.", frontend_dist)

        @app.get("/{full_path:path}")
        async def serve_fallback(full_path: str):
            fallback_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Aegis AI - Desktop Companion</title>
    <style>
        body { margin: 0; background: #0f172a; color: #f8fafc; font-family: system-ui, sans-serif;
               display: flex align-items: center; justify-content: center; height: 100vh; }
        .card { background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255,255,255,0.1);
                border-radius: 20px; padding: 32px; max-width: 480px; text-align: center; }
        h1 { margin-top: 0; color: #38bdf8; font-size: 22px; }
        p { color: #94a3b8; font-size: 14px; line-height: 1.6; }
        code { background: #1e293b; padding: 4px 8px; border-radius: 6px; color: #38bdf8; font-family: monospace; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🛡️ Aegis AI Companion</h1>
        <p>The compiled desktop UI bundle was not found at <code>apps/desktop-ui/dist</code>.</p>
        <p>To build the UI, run <code>npm run build</code> inside <code>apps/desktop-ui</code>.</p>
    </div>
</body>
</html>"""
            return HTMLResponse(content=fallback_html, status_code=200)

    return app


app = create_app()


def start():
    """CLI execution entrypoint."""
    uvicorn.run(
        "aegis_core.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )


if __name__ == "__main__":
    start()
