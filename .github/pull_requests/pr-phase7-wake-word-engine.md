# Pull Request: Phase 7 — Zero-Bloat Local ONNX Wake Word Engine & Background Listener

## 🎯 Summary
This PR resolves [Issue #7](https://github.com/mokashreef/Aegis-AI/issues/7) by implementing an ultra-lightweight, 100% offline acoustic wake-word engine and background microphone listener. Rather than pulling heavy 150MB+ scientific dependencies (`scipy`, `scikit-learn`), the pipeline runs directly on `onnxruntime` and `sounddevice`, executing acoustic frame inference in **4.35 ms** with near-zero CPU idle footprint.

## 🔗 Linked Issues
- Resolves: Issue #7 (`.github/issues/issue-007-missing-wake-word-engine.md`) - Missing Production Wake Word Engine

## 🚀 Key Deliverables
1. **Direct ONNX Acoustic Inference Pipeline (`wake_word.py`)**:
   - Downloads and runs quantized ONNX models (`melspectrogram.onnx`, `embedding_model.onnx`, `hey_jarvis_v0.1.onnx`, `alexa_v0.1.onnx`) directly with `onnxruntime`.
   - Silence gating bypasses inference in **23.99 microseconds** when ambient room noise is low.
   - Active frame inference takes **4.35 ms** for an 80 ms audio chunk (0.054x real-time factor, 18x faster than real-time playback).
2. **Background Audio Daemon (`WakeWordListener`)**:
   - Captures 16 kHz mono float32 audio via `sounddevice.InputStream`.
   - Automatically summons and centers the desktop HUD (`overlay_manager.show()`) upon detection.
   - Cooldown timer (2.5s) prevents spamming triggers.
3. **RESTful Management & Telemetry**:
   - `GET /api/voice/wakeword/status`: returns live state, active model, and sensitivity.
   - `POST /api/voice/wakeword/toggle`: starts or stops background listening thread.
   - `POST /api/voice/wakeword/config`: switches active keyword model and threshold.
4. **Desktop HUD Integration**:
   - Header bar displays live Wake Word status badge with pulsing indicator and one-click toggle.
   - Full Vite production build generated (`dist/assets/index-Bk-_JdNW.js`).

## 📊 Benchmark Telemetry
- **Init Latency**: `71.62 ms`
- **Silence Gate**: `23.99 us`
- **Acoustic Inference**: `4.35 ms`
- **Total RAM Footprint**: `86.62 MB`
- **Benchmark Artifact**: `.github/validation_evidence/section2b_wake_word.json`

## 🧪 Testing & Quality
- Test Suite: 38 passed in 17.48s (`pytest backend/tests -v`).
- Flake8: 0 warnings (`flake8 backend`).
- Frontend Build: Passed in 15.43s (2,064 modules).
