"""
Aegis AI - Core Daemon Entrypoint.
Starts the FastAPI application, initializes database schemas, registers system tools,
and opens the HTTP/WebSocket gateway for the Tauri Desktop Shell.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aegis_core.ai_runtime.router import ai_router
from aegis_core.api.routes import router as api_router
from aegis_core.api.websocket import ws_router
from aegis_core.automation.system_tools import (
    CloseAppTool,
    FocusWindowTool,
    GetClipboardTool,
    GetSystemTelemetryTool,
    LaunchAppTool,
    ListProcessesTool,
    ListWindowsTool,
    SetClipboardTool,
)
from aegis_core.config import settings
from aegis_core.memory.db import db_engine
from aegis_core.plugins.registry import plugin_registry
from aegis_core.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle supervisor."""
    logger.info("Initializing %s v%s...", settings.app_name, settings.app_version)

    # 1. Ensure storage directory and database schemas
    settings.ensure_directories()
    db_engine.init_db()

    # 2. Register core desktop automation tools
    plugin_registry.register(LaunchAppTool())
    plugin_registry.register(CloseAppTool())
    plugin_registry.register(ListProcessesTool())
    plugin_registry.register(GetClipboardTool())
    plugin_registry.register(SetClipboardTool())
    plugin_registry.register(ListWindowsTool())
    plugin_registry.register(FocusWindowTool())
    plugin_registry.register(GetSystemTelemetryTool())
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

    # Configure CORS for local Tauri overlay and web development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount REST and WebSocket routers
    app.include_router(api_router, prefix="/api")
    app.include_router(ws_router)

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
