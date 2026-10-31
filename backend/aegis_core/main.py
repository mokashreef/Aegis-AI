"""
Aegis AI - Core Daemon Entrypoint.
Starts the FastAPI application, mounts compiled desktop UI assets, registers system tools,
and exposes the HTTP/WebSocket gateway for native desktop interaction.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from aegis_core.ai_runtime.router import ai_router
from aegis_core.api.routes import router as api_router
from aegis_core.api.websocket import ws_router
from aegis_core.automation.system_tools import (
    CloseAppTool,
    FocusWindowByTitleTool,
    FocusWindowTool,
    GetClipboardTool,
    GetSystemTelemetryTool,
    LaunchAppTool,
    ListProcessesTool,
    ListWindowsTool,
    MinimizeAllWindowsTool,
    SetClipboardTool,
    SnapWindowTool,
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
        CloseAppTool(),
        ListProcessesTool(),
        GetClipboardTool(),
        SetClipboardTool(),
        ListWindowsTool(),
        FocusWindowTool(),
        FocusWindowByTitleTool(),
        MinimizeAllWindowsTool(),
        SnapWindowTool(),
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

    # 3. Probe AI Runtime Matrix
    runtime_status = await ai_router.get_system_status()
    logger.info(
        "AI Runtime initialized. Active: %s (Ollama Available: %s, Fallbacks Enabled: %s)",
        runtime_status["active_provider"],
        runtime_status["ollama"]["available"],
        runtime_status["pollinations_fallback"]["enabled"],
    )

    yield

    logger.info("Shutting down %s daemon...", settings.app_name)


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
