"""
Aegis AI - Voice Pipeline Architecture (Faster-Whisper STT & Neural TTS).
Connects offline local transcription with natural neural speech synthesis.
"""

import asyncio
import os
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from aegis_core.config import settings
from aegis_core.utils.logger import logger
from aegis_core.voice.stt import stt_engine
from aegis_core.voice.tts import tts_engine


class VoiceState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    SPEAKING = "speaking"


class VoicePipelineController:
    """Manages offline speech-to-text and natural neural voice synthesis."""

    def __init__(self):
        self.state: VoiceState = VoiceState.IDLE
        self.enabled = settings.voice_enabled
        self.stt = stt_engine
        self.tts = tts_engine

    def get_status(self) -> Dict[str, Any]:
        """Returns the current voice pipeline telemetry."""
        return {
            "enabled": self.enabled,
            "state": self.state.value,
            "stt": self.stt.get_status(),
            "tts": self.tts.get_status(),
        }

    async def speak_text(
        self, text: str, voice: Optional[str] = None, rate: Optional[str] = None
    ) -> bool:
        """Synthesizes text using Edge Neural TTS, falling back to local SAPI if offline."""
        if not self.enabled or not text.strip():
            return False

        self.state = VoiceState.SPEAKING
        logger.info("Voice synthesis triggered for %d characters.", len(text))

        try:
            # 1. Attempt natural neural synthesis
            audio_bytes = await self.tts.synthesize_to_bytes(text, voice=voice, rate=rate)
            if audio_bytes:
                # Save to temporary file for Windows playback
                temp_audio = settings.storage_dir / "cache" / "speech_output.mp3"
                temp_audio.parent.mkdir(parents=True, exist_ok=True)
                temp_audio.write_bytes(audio_bytes)

                # Play via Windows media player asynchronously in background
                if os.name == "nt":
                    ps_cmd = (
                        f'$player = New-Object System.Media.SoundPlayer; '
                        f'Add-Type -AssemblyName presentationCore; '
                        f'$mediaPlayer = New-Object System.Windows.Media.MediaPlayer; '
                        f'$mediaPlayer.Open("{temp_audio.resolve()}"); '
                        f'$mediaPlayer.Play(); '
                        f'Start-Sleep -Seconds 1;'
                    )
                    subprocess.Popen(
                        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                return True

            # 2. Offline fallback: Windows native SAPI5
            logger.info("Using local Windows SAPI fallback for speech output.")
            clean_text = text.replace('"', '""').replace("'", "''").strip()
            if len(clean_text) > 400:
                clean_text = clean_text[:400] + "... and more."

            if os.name == "nt":
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
        """Transcribes an audio waveform file into text using real Faster-Whisper."""
        self.state = VoiceState.TRANSCRIBING
        try:
            logger.info("Transcribing audio file: %s", audio_path)
            # Run in worker thread to prevent blocking async event loop
            text = await asyncio.to_thread(self.stt.transcribe_file, audio_path)
            return text
        except Exception as exc:
            logger.error("Transcription failed: %s", exc)
            return ""
        finally:
            self.state = VoiceState.IDLE


# Global voice pipeline singleton
voice_controller = VoicePipelineController()
