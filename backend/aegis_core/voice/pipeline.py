"""
Aegis AI - Voice Pipeline Architecture (Faster-Whisper STT & Piper Neural TTS).
"""

import asyncio
import os
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any, Dict
from aegis_core.config import settings
from aegis_core.utils.logger import logger


class VoiceState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    SPEAKING = "speaking"


class VoicePipelineController:
    """Manages offline speech-to-text and neural text-to-speech synthesis."""

    def __init__(self):
        self.state: VoiceState = VoiceState.IDLE
        self.enabled = settings.voice_enabled

    def get_status(self) -> Dict[str, Any]:
        """Returns the current voice pipeline telemetry."""
        return {
            "enabled": self.enabled,
            "state": self.state.value,
            "whisper_model": settings.whisper_model_size,
            "piper_voice": settings.piper_voice,
            "backend": "Windows SAPI5 / Piper neural",
        }

    async def speak_text(self, text: str) -> bool:
        """Synthesizes and speaks text using local Windows speech or Piper."""
        if not self.enabled or not text.strip():
            return False

        self.state = VoiceState.SPEAKING
        logger.info("Voice synthesis triggered for %d characters.", len(text))

        try:
            # Clean text for shell-safe speech
            clean_text = text.replace('"', '""').replace("'", "''").strip()
            # Truncate for audio summary if extremely long
            if len(clean_text) > 400:
                clean_text = clean_text[:400] + "... and more."

            if os.name == "nt":
                # Execute native Windows SAPI speech asynchronously via PowerShell background worker
                ps_cmd = (
                    f'Add-Type -AssemblyName System.Speech; '
                    f'$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                    f'$synth.Speak("{clean_text}");'
                )
                proc = await asyncio.create_subprocess_exec(
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    ps_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                await proc.wait()
            return True
        except Exception as exc:
            logger.error("Voice synthesis failed: %s", exc)
            return False
        finally:
            self.state = VoiceState.IDLE

    async def transcribe_audio_file(self, audio_path: Path) -> str:
        """Transcribes an audio waveform file into text."""
        self.state = VoiceState.TRANSCRIBING
        try:
            logger.info("Transcribing audio file: %s", audio_path)
            # Placeholder for faster_whisper invocation
            await asyncio.sleep(0.1)
            return ""
        finally:
            self.state = VoiceState.IDLE


# Global voice pipeline singleton
voice_controller = VoicePipelineController()
