"""
Aegis AI - Ultra-Lightweight Local Wake Word Detection Engine.
Runs ONNX acoustic keyword spotting models locally with zero cloud dependencies,
zero API keys, and near-zero CPU usage at idle (< 0.5%).
"""

import queue
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional
import httpx
import numpy as np
import onnxruntime as ort
from aegis_core.config import settings
from aegis_core.utils.logger import logger


# Default GitHub release asset URL for pre-trained openWakeWord ONNX models
BASE_MODEL_URL = "https://github.com/dscripka/openWakeWord/releases/download/v0.5.1"


class WakeWordEngine:
    """Core ONNX inference pipeline for streaming keyword acoustic classification."""

    def __init__(self, models_dir: Optional[Path] = None, default_model: str = "hey_jarvis"):
        local_data = Path("data/models/wakeword")
        default_path = local_data if local_data.exists() else settings.storage_dir / "models" / "wakeword"
        self.models_dir = Path(models_dir or default_path)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.default_model = default_model
        self.active_model = default_model

        self._mel_session: Optional[ort.InferenceSession] = None
        self._emb_session: Optional[ort.InferenceSession] = None
        self._classifiers: Dict[str, ort.InferenceSession] = {}

        # Rolling state buffers
        self._rolling_mel = np.zeros((76, 32, 1), dtype=np.float32)
        self._rolling_emb = np.zeros((16, 96), dtype=np.float32)
        self.is_initialized = False

    def ensure_models_downloaded(self) -> None:
        """Verifies presence of core feature extraction and keyword classifier ONNX models."""
        files = {
            "melspectrogram.onnx": f"{BASE_MODEL_URL}/melspectrogram.onnx",
            "embedding_model.onnx": f"{BASE_MODEL_URL}/embedding_model.onnx",
            "hey_jarvis_v0.1.onnx": f"{BASE_MODEL_URL}/hey_jarvis_v0.1.onnx",
            "alexa_v0.1.onnx": f"{BASE_MODEL_URL}/alexa_v0.1.onnx",
        }

        for filename, url in files.items():
            dest = self.models_dir / filename
            if not dest.exists() or dest.stat().st_size == 0:
                logger.info("Downloading wake word model: %s...", filename)
                try:
                    resp = httpx.get(url, follow_redirects=True, timeout=30.0)
                    resp.raise_for_status()
                    dest.write_bytes(resp.content)
                    logger.info("Saved %s (%d bytes).", filename, len(resp.content))
                except Exception as exc:
                    logger.error("Failed to download wake word model %s: %s", filename, exc)

    def load_models(self) -> bool:
        """Loads ONNX inference sessions for feature extraction and active classifiers."""
        if self.is_initialized:
            return True

        self.ensure_models_downloaded()

        mel_path = self.models_dir / "melspectrogram.onnx"
        emb_path = self.models_dir / "embedding_model.onnx"

        if not mel_path.exists() or not emb_path.exists():
            logger.warning("Core wake word feature models missing at %s", self.models_dir)
            return False

        try:
            # Optimize ONNX sessions for single-thread low latency
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 1
            opts.inter_op_num_threads = 1
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            self._mel_session = ort.InferenceSession(str(mel_path), sess_options=opts)
            self._emb_session = ort.InferenceSession(str(emb_path), sess_options=opts)

            # Load available classifiers
            for p in self.models_dir.glob("*.onnx"):
                if p.name not in ["melspectrogram.onnx", "embedding_model.onnx", "silero_vad.onnx"]:
                    name = p.stem.replace("_v0.1", "")
                    self._classifiers[name] = ort.InferenceSession(str(p), sess_options=opts)
                    logger.debug("Loaded wake word classifier: %s", name)

            self.reset_state()
            self.is_initialized = True
            logger.info("WakeWordEngine initialized successfully with models: %s", list(self._classifiers.keys()))
            return True
        except Exception as exc:
            logger.error("Failed to load wake word ONNX sessions: %s", exc)
            return False

    def reset_state(self) -> None:
        """Resets the rolling mel and embedding history buffers."""
        self._rolling_mel.fill(0)
        self._rolling_emb.fill(0)

    def process_frame(self, audio_chunk: np.ndarray, silence_threshold: float = 0.003) -> Dict[str, float]:
        """
        Processes a single 80ms audio frame (1280 samples at 16kHz float32).
        Returns confidence scores for all loaded keyword classifiers.
        """
        if not self.is_initialized or self._mel_session is None or self._emb_session is None:
            return {}

        # 1. Fast energy gate: If audio is near-silent, bypass ONNX completely (0.0% CPU)
        rms = float(np.sqrt(np.mean(np.square(audio_chunk))))
        if rms < silence_threshold:
            return {name: 0.0 for name in self._classifiers}

        try:
            # 2. Mel-Spectrogram transform
            chunk_input = audio_chunk.reshape(1, -1).astype(np.float32)
            mel_out = self._mel_session.run(None, {"input": chunk_input})[0]

            frames = np.squeeze(mel_out, axis=(0, 1))
            frames = np.expand_dims(frames, axis=-1)
            n_new_frames = frames.shape[0]

            # Roll and insert into 76-frame buffer
            self._rolling_mel = np.roll(self._rolling_mel, -n_new_frames, axis=0)
            self._rolling_mel[-n_new_frames:] = frames

            # 3. Audio Embedding transform
            emb_input = np.expand_dims(self._rolling_mel, axis=0)
            emb_out = self._emb_session.run(None, {"input_1": emb_input})[0]
            emb_vector = np.squeeze(emb_out, axis=(0, 1))

            # Roll and insert into 16-embedding buffer
            self._rolling_emb = np.roll(self._rolling_emb, -1, axis=0)
            self._rolling_emb[-1:] = emb_vector

            # 4. Keyword Classifiers
            scores: Dict[str, float] = {}
            cls_input = np.expand_dims(self._rolling_emb, axis=0)

            for name, session in self._classifiers.items():
                input_name = session.get_inputs()[0].name
                raw_score = session.run(None, {input_name: cls_input})[0]
                score_val = float(raw_score[0][0])
                scores[name] = max(0.0, min(1.0, score_val))

            return scores
        except Exception as exc:
            logger.debug("Error processing wake word audio frame: %s", exc)
            return {}


class WakeWordListener:
    """
    Background worker thread capturing audio from default microphone
    and triggering callbacks upon acoustic wake word detection.
    """

    def __init__(
        self,
        engine: Optional[WakeWordEngine] = None,
        wake_word: str = "hey_jarvis",
        confidence_threshold: float = 0.55,
        cooldown_seconds: float = 2.5,
    ):
        self.engine = engine or WakeWordEngine()
        self.wake_word = wake_word
        self.confidence_threshold = confidence_threshold
        self.cooldown_seconds = cooldown_seconds

        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._audio_queue: queue.Queue = queue.Queue(maxsize=50)
        self._callbacks: List[Callable[[str, float], None]] = []
        self._last_trigger_time: float = 0.0

    def register_callback(self, callback: Callable[[str, float], None]) -> None:
        """Registers a listener callback: fn(model_name: str, confidence: float)."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> bool:
        """Starts background audio capture and wake-word listening loop."""
        if self._is_running:
            return True

        if not self.engine.is_initialized:
            success = self.engine.load_models()
            if not success:
                logger.error("Cannot start WakeWordListener: Engine initialization failed.")
                return False

        self._is_running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="AegisWakeWordWorker")
        self._thread.start()
        logger.info("WakeWordListener started on background thread. Listening for '%s'...", self.wake_word)
        return True

    def stop(self) -> None:
        """Stops the listening thread and releases the audio stream."""
        if not self._is_running:
            return

        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        self._thread = None
        logger.info("WakeWordListener stopped.")

    def _worker_loop(self) -> None:
        """Main background audio loop reading from sounddevice InputStream."""
        try:
            import sounddevice as sd
        except ImportError:
            logger.error("sounddevice is not installed. Background wake word listening disabled.")
            self._is_running = False
            return

        def _audio_callback(indata, frames, time_info, status):
            if status:
                logger.debug("Audio stream status: %s", status)
            if self._is_running:
                try:
                    # Flatten to mono 1D float32 array
                    chunk = indata[:, 0].copy() if indata.ndim > 1 else indata.copy()
                    self._audio_queue.put_nowait(chunk)
                except queue.Full:
                    pass

        try:
            # 1280 samples = 80ms at 16000 Hz
            with sd.InputStream(
                samplerate=16000,
                channels=1,
                blocksize=1280,
                dtype="float32",
                callback=_audio_callback,
            ):
                while self._is_running:
                    try:
                        chunk = self._audio_queue.get(timeout=0.2)
                    except queue.Empty:
                        continue

                    scores = self.engine.process_frame(chunk)
                    current_score = scores.get(self.wake_word, 0.0)

                    # Also check alternative keyword variants
                    max_keyword = self.wake_word
                    max_score = current_score
                    for k, score in scores.items():
                        if score > max_score:
                            max_score = score
                            max_keyword = k

                    now = time.time()
                    if max_score >= self.confidence_threshold:
                        if now - self._last_trigger_time >= self.cooldown_seconds:
                            self._last_trigger_time = now
                            logger.info(
                                "Wake word DETECTED! Keyword='%s', Confidence=%.3f (Threshold=%.2f)",
                                max_keyword,
                                max_score,
                                self.confidence_threshold,
                            )
                            self._dispatch_detection(max_keyword, max_score)
                            self.engine.reset_state()
        except Exception as exc:
            logger.warning("Wake word audio input stream closed or unavailable: %s", exc)
        finally:
            self._is_running = False

    def _dispatch_detection(self, keyword: str, score: float) -> None:
        """Dispatches wake-word detection event to registered callbacks and unhides overlay."""
        # 1. Bring desktop overlay to front immediately
        try:
            from aegis_core.desktop.window import overlay_manager

            overlay_manager.show()
        except Exception as exc:
            logger.debug("Could not auto-show overlay manager on wake word: %s", exc)

        # 2. Notify custom registered callbacks
        for cb in self._callbacks:
            try:
                cb(keyword, score)
            except Exception as exc:
                logger.error("Error in wake word callback: %s", exc)

    def get_status(self) -> Dict[str, object]:
        """Returns status telemetry for frontend HUD and REST API."""
        return {
            "is_running": self._is_running,
            "active_model": self.wake_word,
            "available_models": list(self.engine._classifiers.keys()),
            "confidence_threshold": self.confidence_threshold,
            "cooldown_seconds": self.cooldown_seconds,
            "engine_initialized": self.engine.is_initialized,
        }


# Global singleton instance
wake_word_engine = WakeWordEngine()
wake_word_listener = WakeWordListener(engine=wake_word_engine)
