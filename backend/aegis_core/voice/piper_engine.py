"""
Aegis AI - Offline Neural Arabic Text-To-Speech Engine using Piper.
Provides 100% offline, low-latency (<150ms) neural speech synthesis
without cloud lock-in or external API dependencies.
"""

import io
import wave
from pathlib import Path
from typing import Any, Dict, List
from aegis_core.utils.logger import logger

PIPER_MODELS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "storage" / "models" / "piper"

DEFAULT_PIPER_ARABIC_VOICE = "ar_JO-kareem-medium"

PIPER_VOICE_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "piper-ar-kareem-medium",
        "model_key": "ar_JO-kareem-medium",
        "name": "كريم (عربي أردني - عصبي محلي فائق النعومة)",
        "name_en": "Kareem (Jordanian - Offline Neural / Smooth)",
        "gender": "Male",
        "lang": "ar-JO",
        "lang_name": "العربية (محلي دون اتصال - Piper)",
        "sample_text": "مرحباً، أنا المساعد إيجيس، أعمل بنطق عصبي محلي بالكامل وبدون إنترنت.",
        "download_url_onnx": (
            "https://huggingface.co/rhasspy/piper-voices/resolve/main/ar/ar_JO/kareem/medium/ar_JO-kareem-medium.onnx"
        ),
        "download_url_json": (
            "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
            "ar/ar_JO/kareem/medium/ar_JO-kareem-medium.onnx.json"
        ),
    },
    {
        "id": "piper-ar-kareem-low",
        "model_key": "ar_JO-kareem-low",
        "name": "كريم (خفيف وسريع جداً للأجهزة الضعيفة)",
        "name_en": "Kareem (Low - Ultra-Fast Local)",
        "gender": "Male",
        "lang": "ar-JO",
        "lang_name": "العربية (خفيف محلي - Piper)",
        "sample_text": "أهلاً بك، تم تفعيل النطق العصبي الخفيف والسريع على حاسوبك.",
        "download_url_onnx": (
            "https://huggingface.co/rhasspy/piper-voices/resolve/main/ar/ar_JO/kareem/low/ar_JO-kareem-low.onnx"
        ),
        "download_url_json": (
            "https://huggingface.co/rhasspy/piper-voices/resolve/main/ar/ar_JO/kareem/low/ar_JO-kareem-low.onnx.json"
        ),
    },
]


class PiperNeuralEngine:
    """Offline neural speech synthesis engine based on Piper ONNX runtime."""

    def __init__(self, models_dir: Path = PIPER_MODELS_DIR):
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._loaded_voices: Dict[str, Any] = {}

    def get_model_paths(self, model_key: str) -> tuple[Path, Path]:
        """Returns the expected (.onnx, .onnx.json) paths for a given model key."""
        onnx_path = self.models_dir / f"{model_key}.onnx"
        json_path = self.models_dir / f"{model_key}.onnx.json"
        return onnx_path, json_path

    def is_model_installed(self, model_key: str = DEFAULT_PIPER_ARABIC_VOICE) -> bool:
        """Checks if both ONNX model and config JSON exist locally on disk."""
        onnx_path, json_path = self.get_model_paths(model_key)
        return onnx_path.exists() and json_path.exists() and onnx_path.stat().st_size > 1024

    def load_voice(self, model_key: str = DEFAULT_PIPER_ARABIC_VOICE):
        """Loads and caches a PiperVoice instance into memory."""
        if model_key in self._loaded_voices:
            return self._loaded_voices[model_key]

        onnx_path, json_path = self.get_model_paths(model_key)
        if not (onnx_path.exists() and json_path.exists()):
            raise FileNotFoundError(
                f"Piper model '{model_key}' not found at {onnx_path}. "
                "Download the model files before synthesizing."
            )

        try:
            from piper.voice import PiperVoice

            voice = PiperVoice.load(str(onnx_path), config_path=str(json_path))
            self._loaded_voices[model_key] = voice
            logger.info("Loaded Piper offline neural voice: %s", model_key)
            return voice
        except Exception as exc:
            logger.error("Failed to load Piper model '%s': %s", model_key, exc)
            raise

    async def download_model(self, model_key: str = DEFAULT_PIPER_ARABIC_VOICE) -> bool:
        """Downloads the ONNX model and JSON config for the specified voice asynchronously."""
        meta = next((v for v in PIPER_VOICE_CATALOG if v["model_key"] == model_key), None)
        if not meta:
            logger.error("Unknown Piper model key: %s", model_key)
            return False

        onnx_path, json_path = self.get_model_paths(model_key)
        if self.is_model_installed(model_key):
            logger.info("Piper model '%s' already downloaded.", model_key)
            return True

        import httpx

        try:
            logger.info("Downloading Piper voice model '%s'...", model_key)
            async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                # 1. Download ONNX config JSON
                r_json = await client.get(meta["download_url_json"])
                r_json.raise_for_status()
                json_path.write_bytes(r_json.content)

                # 2. Download ONNX model binary
                r_onnx = await client.get(meta["download_url_onnx"])
                r_onnx.raise_for_status()
                onnx_path.write_bytes(r_onnx.content)

            logger.info(
                "Successfully downloaded Piper model '%s' (%d bytes).",
                model_key,
                len(r_onnx.content),
            )
            return True
        except Exception as exc:
            logger.error("Failed downloading Piper model '%s': %s", model_key, exc)
            if json_path.exists():
                json_path.unlink(missing_ok=True)
            if onnx_path.exists():
                onnx_path.unlink(missing_ok=True)
            return False

    def synthesize_wav_bytes(
        self,
        text: str,
        model_key: str = DEFAULT_PIPER_ARABIC_VOICE,
    ) -> bytes:
        """
        Synthesizes text into 16-bit PCM WAV audio bytes.
        Fast, offline, and thread-safe.
        """
        clean_text = text.strip()
        if not clean_text:
            return b""

        # Truncate overly long text chunks if necessary
        if len(clean_text) > 1200:
            clean_text = clean_text[:1200] + "..."

        voice = self.load_voice(model_key)

        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wav_file:
            voice.synthesize(clean_text, wav_file)

        return wav_io.getvalue()

    def get_status(self) -> Dict[str, Any]:
        """Returns the Piper offline status and list of installed models."""
        installed_models = [
            v["model_key"] for v in PIPER_VOICE_CATALOG if self.is_model_installed(v["model_key"])
        ]
        return {
            "available": True,
            "installed_models": installed_models,
            "catalog": PIPER_VOICE_CATALOG,
            "default_model": DEFAULT_PIPER_ARABIC_VOICE,
            "is_default_ready": self.is_model_installed(DEFAULT_PIPER_ARABIC_VOICE),
        }


# Singleton instance
piper_engine = PiperNeuralEngine()
