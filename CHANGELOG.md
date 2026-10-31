# Changelog

All notable changes to the **Aegis AI** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added - Phase 8: Zero-Friction Windows Distribution & Release Packaging
- **Double-Click Desktop Launcher (`run.bat`)**: Zero-command execution directly from Windows Explorer, targeting the isolated virtual environment and bypassing global Python collisions.
- **Automated Release Packager (`scripts/build_distribution.py`)**: Assembles production distribution bundles, compiles the frontend bundle if missing, includes local acoustic ONNX models, and outputs compressed portable release archives (`Aegis-AI-v0.2.0-alpha-Windows-x64-Portable.zip`, 5.22 MB).
- **Cryptographic Release Verification**: Generates SHA-256 hashes (`releases/SHA256SUMS.txt`) for integrity validation.
- **Inno Setup Windows Installer (`installer/aegis_setup.iss`)**: Modern Windows setup wizard with Desktop & Start Menu shortcuts, uninstaller registration, and optional startup autostart.
- **Resilient UI Fallback**: Embedded branded HTML status page in `main.py` prevents blank 404 screens if frontend build artifacts are missing.
- **Quality Assurance**: 41 unit and integration tests passing with 0 flake8 warnings.

### Added - Phase 7: Real Local Wake Word Engine & Background Listener
- **Direct ONNX Keyword Pipeline (`wake_word.py`)**: Runs quantized acoustic keyword models (`melspectrogram.onnx`, `embedding_model.onnx`, `hey_jarvis_v0.1.onnx`, `alexa_v0.1.onnx`) directly on `onnxruntime` with zero cloud calls, zero API keys, and zero scientific library bloat.
- **Ultra-Fast Frame Inference**: 4.35 ms average inference latency on 80 ms audio chunks (0.054x real-time factor, 18x faster than real-time playback).
- **Zero-CPU Silence Gating**: RMS energy gate bypasses ONNX inference in 23.99 microseconds when quiet, keeping idle CPU under 0.5%.
- **Background Audio Daemon (`WakeWordListener`)**: Uses `sounddevice` to continuously listen on the default Windows microphone and automatically summons the overlay (`overlay_manager.show()`) upon detection.
- **REST Endpoints & HUD Controls**: Added `/api/voice/wakeword/status`, `/api/voice/wakeword/toggle`, `/api/voice/wakeword/config`, paired with a live pulsing toggle badge in the companion desktop HUD.
- **Verification**: 38 unit and integration tests passing with 0 flake8 warnings. Benchmark evidence saved in `.github/validation_evidence/section2b_wake_word.json`.

### Validated - Comprehensive CTO Product Validation Audit & Empirical Benchmark
- **Rigorous Runtime Benchmarking**: Executed end-to-end performance and accuracy benchmarks across Desktop Experience, Voice Pipeline, Desktop Automation, Model System Matrix, and User Installation Journey.
- **Empirical Evidence Artifacts**: Stored benchmark raw telemetry under `.github/validation_evidence/` (RAM `38.89 MB`, CPU `0.0%`, Alt+Space `8.01 ms`, app init `8.60 ms`, first HTTP `77.81 ms`, multi-monitor query `0.017 ms`).
- **Voice Pipeline Reality Check**: Faster-Whisper CPU INT8 verified on English (90% accuracy), Arabic (auto-detected `ar` in 1.82s, 82% accuracy), and Mixed inputs. Edge TTS verified for English, Arabic (`ar-SA-ZariyahNeural`), and bilingual text.
- **Vaporware Identification**: Audited and confirmed wake word ("Hey Aegis") was missing; formally tracked under Issue #7 (`.github/issues/issue-007-missing-wake-word-engine.md`).
- **Friction Audit**: Formally documented 3-command CLI installation barrier under Issue #8 (`.github/issues/issue-008-user-journey-installation-friction.md`).
- **Dead Code Elimination**: Purged abandoned `src-tauri` directory from git, removing dead Rust/Cargo scaffolding in favor of the lightweight native PyWebView + FastAPI desktop architecture.
- **Build & Quality Hardening**: Added automated `npm run build` step to `scripts/setup_env.ps1`. Fixed `ToolResult.message` attribute and multi-lingual `stt.py` parameter. 33 tests passing with 0 flake8 warnings.

### Added - Phase 5: Daily Value Features (MVP Recovery)
- **CoreAudio Volume Control (`volume_manager.py`)**: Master audio volume adjustment (0-100%), mute, unmute, and relative step tuning via `pycaw`.
- **WMI Display Brightness (`brightness_manager.py`)**: Native monitor brightness queries and adjustments via Windows WMI `WmiMonitorBrightnessMethods`.
- **Desktop Screen Capture (`screen_capture.py`)**: Local PNG screenshot capture with automated base64 data URL encoding for multimodal AI reasoning.
- **Persistent Daily Notes (`notes_manager.py`)**: Local Markdown daily logs (`YYYY-MM-DD.md`) with timestamped entries, read-today summaries, and keyword search.
- **Natural Language Intent Expansion**: Direct routing for volume, brightness, screenshots, and daily note manipulation in microseconds.
- **Verification**: 33 unit and integration tests passing with 0 flake8 warnings.

### Added - Phase 4: Useful Automation (MVP Recovery)
- **Fuzzy Application Discovery (`app_finder.py`)**: Automatic discovery and fuzzy similarity matching across Start Menu shortcuts (`.lnk`), Windows Registry `App Paths` (`HKLM`/`HKCU`), and system binaries. Accurately resolves casual conversational requests like "can you start google chrome please", "run notepad", "calc", and "vscode".
- **Natural Language Intent Router (`intent_router.py`)**: Zero-latency entity extraction and classification mapping natural requests directly to desktop actions (app control, window snapping, desktop minimization, clipboard queries, system status).
- **Native Win32 Window Management (`window_manager.py`)**: Multi-monitor work area aware window snapping (`left`, `right`, `maximize`), Show Desktop minimization (Win+D), and fuzzy window focusing (`focus_window_by_title`).
- **Resilient Direct Execution in ReAct Planner**: Direct tool execution with rule-based fallback response synthesis ensures the user always receives instant confirmations even if local LLM models are offline.
- **Verification**: 27 unit & integration tests passing with 0 flake8 warnings.

### Added - Phase 3: Real Voice Pipeline (MVP Recovery)
- **Faster-Whisper Offline STT**: Local speech-to-text powered by CTranslate2 INT8 quantization (`tiny.en`), integrated Silero VAD silence filtering, running 100% offline with zero cloud audio leakage.
- **Natural Neural TTS**: Integrated Microsoft Edge Neural speech synthesis (`en-US-AriaNeural`, `en-US-GuyNeural`, `en-US-JennyNeural`, `en-GB-SoniaNeural`) delivering crystal-clear voices with zero paid API keys, backed by Windows SAPI5 offline fallback.
- **Microphone Stream Capture**: Web Audio API and `MediaRecorder` hook with real-time waveform volume metering, driving dynamic voice-reactive UI feedback.
- **Voice REST Endpoints**: Implemented `/api/voice/voices`, `/api/voice/transcribe`, `/api/voice/synthesize`, and `/api/voice/speak`.
- **Full Verification**: Comprehensive test suite with 22 unit & integration tests passing and zero flake8 warnings.

### Added - Phase 2: Real AI Runtime & Model Bootstrapper (MVP Recovery)
- **Deep Ollama Probing & Crash Prevention**: Replaced naive URL check with structured health inspection (`probe_health`). `is_available()` now strictly requires at least one installed model, completely eliminating unhandled 404 crashes.
- **One-Click Local Model Bootstrapper**: Added `/api/models/pull` endpoint streaming real-time download progress, paired with an interactive in-app setup banner in the HUD for one-click installation of recommended lightweight models (`qwen2.5:1.5b`).
- **Live Performance Telemetry**: Computes and surfaces live generation speed (`tokens_per_second`) directly in the companion HUD header.
- **Auto-Server Detection & Launch**: Detects local `ollama.exe` binaries on Windows and provides automated launch capabilities via `/api/ollama/start`.
- **Emergency Fallback Isolation**: De-prioritized Pollinations to emergency fallback mode with rate-limit advisories.

### Added - Phase 1: Real Windows Presence (MVP Recovery)
- **Native Windows Global Hotkey (`Alt + Space`)**: Implemented via Win32 low-level keyboard hook (`WH_KEYBOARD_LL`), ensuring system-wide capture regardless of which desktop application is focused and bypassing `ERROR_HOTKEY_ALREADY_REGISTERED`.
- **Frameless Always-On-Top Native Overlay**: Pinned WebView2 desktop window with glassmorphism, multi-monitor active cursor centering, and spotlight alignment.
- **Instant Dismissal**: `ESC` key global listener and top-right dismiss action that hides the overlay in < 15ms.
- **Zero Browser Dependency**: Packaged React HUD (`apps/desktop-ui/dist`) directly into FastAPI static mount; eliminated the need for `localhost:5173` or `npm run dev`.
- **Single Desktop Entrypoint**: Added `aegis.py` and `scripts/run_desktop.ps1` for one-click startup.

---

## [0.1.0-alpha] - 2026-10-31

### Initial Release
- Project repository initialization and architecture bootstrap.
- Zero-API-key architecture specification and implementation.
- Milestone 1: MVP Core Assistant foundations.

