"""
Aegis AI - Offline Speech-To-Text Engine (Faster-Whisper).
Runs locally on CPU using CTranslate2 INT8 quantization with Silero VAD filtering.
100% offline, zero cloud exfiltration, zero API keys required.
"""

from pathlib import Path
from typing import Any, Dict, Optional
from aegis_core.config import settings
from aegis_core.utils.logger import logger


class FasterWhisperEngine:
    """Wrapper around faster-whisper CTranslate2 offline transcription engine."""

    def __init__(self, model_size: Optional[str] = None):
        self.model_size = model_size or settings.whisper_model_size
        self._model = None
        self._is_loading = False

    def is_loaded(self) -> bool:
        return self._model is not None

    def load_model(self) -> None:
        """Loads or downloads the quantized CTranslate2 Whisper model."""
        if self._model is not None:
            return

        self._is_loading = True
        try:
            from faster_whisper import WhisperModel

            models_dir = settings.storage_dir / "models" / "whisper"
            models_dir.mkdir(parents=True, exist_ok=True)

            logger.info("Loading Faster-Whisper model '%s' (CPU / INT8)...", self.model_size)
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
                download_root=str(models_dir),
                cpu_threads=4,
            )
            logger.info("Faster-Whisper model '%s' loaded successfully.", self.model_size)
        except Exception as exc:
            logger.error("Failed to load Faster-Whisper model: %s", exc)
            self._model = None
            raise
        finally:
            self._is_loading = False

    def transcribe_file(self, audio_path: Path, language: Optional[str] = None) -> str:
        """Transcribes an audio waveform file into text using VAD filtering and language detection."""
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if self._model is None:
            self.load_model()

        if self._model is None:
            raise RuntimeError("Faster-Whisper model could not be initialized.")

        logger.info("Transcribing audio file: %s...", audio_path.name)
        segments, info = self._model.transcribe(
            str(audio_path),
            beam_size=1,  # Greedy for maximum real-time speed
            language=language,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        text_pieces = []
        for segment in segments:
            text_pieces.append(segment.text.strip())

        transcription = " ".join(text_pieces).strip()
        logger.info(
            "Transcription complete (%d chars, detected lang: %s, duration: %.1fs): '%s'",
            len(transcription),
            info.language,
            info.duration,
            transcription,
        )
        return transcription

    def get_status(self) -> Dict[str, Any]:
        return {
            "model_size": self.model_size,
            "loaded": self.is_loaded(),
            "loading": self._is_loading,
            "device": "cpu",
            "compute_type": "int8",
        }


# Global STT engine singleton
stt_engine = FasterWhisperEngine()

