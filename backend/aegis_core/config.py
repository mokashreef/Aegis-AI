"""
Aegis AI - Application Configuration & Environment Management.
Adheres strictly to the Zero API Keys Assumption while providing flexible local configuration.
"""

from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project Root Resolution
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
STORAGE_DIR = PROJECT_ROOT / "storage"
LOGS_DIR = STORAGE_DIR / "logs"


class Settings(BaseSettings):
    """Core settings configuration loaded from environment variables and defaults."""

    model_config = SettingsConfigDict(
        env_prefix="AEGIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application Metadata
    app_name: str = Field(default="Aegis AI", description="Application display name")
    app_version: str = Field(default="0.1.0-alpha", description="Semantic version string")
    debug: bool = Field(default=False, description="Debug mode toggle for verbose telemetry")
    environment: str = Field(default="development", description="Environment: development, test, production")

    # Networking & Gateway
    host: str = Field(default="127.0.0.1", description="Binding address (strictly local by default)")
    port: int = Field(default=8420, description="Daemon HTTP & WebSocket listener port")
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8420",
            "tauri://localhost",
        ],
        description="Allowed CORS origins for the frontend HUD and desktop wrapper",
    )

    # Storage & Persistence
    base_dir: Path = Field(default=PROJECT_ROOT, description="Application root directory")
    storage_dir: Path = Field(default=STORAGE_DIR, description="Root directory for local storage")
    db_path: Path = Field(default=STORAGE_DIR / "aegis.db", description="Path to primary SQLite database")
    logs_dir: Path = Field(default=LOGS_DIR, description="Directory for rolling log files")

    # AI Runtime & Inference Engine (Zero API Key Priority)
    ollama_host: str = Field(default="http://localhost:11434", description="Local Ollama instance endpoint")
    default_model: str = Field(default="llama3.2:latest", description="Primary model identifier for local inference")
    fallback_model: str = Field(default="mistral", description="Secondary fallback model")
    request_timeout_seconds: float = Field(default=60.0, description="Maximum wait time for inference streaming")
    enable_cloud_fallback: bool = Field(
        default=True,
        description="Enable free, zero-key anonymous fallback endpoints (Pollinations) if Ollama is unreachable",
    )

    # Desktop Automation & Safety
    require_confirmation_for_destructive: bool = Field(
        default=True,
        description="Always pause and request confirmation before deleting files or killing external processes",
    )
    allowed_apps: List[str] = Field(
        default_factory=lambda: [
            "notepad.exe",
            "calc.exe",
            "explorer.exe",
            "cmd.exe",
            "powershell.exe",
            "code.cmd",
            "mspaint.exe",
        ],
        description="Whitelisted application executables for safe launching",
    )

    # Voice Pipeline
    voice_enabled: bool = Field(default=True, description="Enable voice synthesis and transcription interfaces")
    whisper_model_size: str = Field(default="tiny", description="Faster-Whisper model size (tiny, base, small, medium)")
    piper_voice: str = Field(default="en_US-lessac-medium", description="Piper neural TTS voice identifier")
    wake_word_enabled: bool = Field(default=True, description="Enable continuous background wake word listening")
    wake_word_model: str = Field(default="hey_jarvis", description="Acoustic keyword model name")
    wake_word_threshold: float = Field(default=0.55, description="Confidence threshold [0.0 - 1.0]")

    def ensure_directories(self) -> None:
        """Create necessary persistent storage and log directories."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


# Global singleton instance
settings = Settings()
settings.ensure_directories()
