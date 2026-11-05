# Changelog

All notable changes to the **Aegis AI** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [1.0.0] - 2026-11-05

### Added - Phase 21: Precision Canonical Navigation, Arbitrary Screen Vision AI, Zero-Console Silent Daemon & Landing Page
- **Direct Canonical Website Resolution (`intent_router.py`, `system_tools.py`)**:
  - Eliminated ambiguous search engine fallbacks by mapping 80+ spoken Arabic and English aliases directly to official canonical endpoints (`كود التطور` -> `https://code-elta6ur.net`, `Claude`, `Gemini`, `ChatGPT`, `Canva`, `Figma`, `YouTube`, `GitHub`, etc.).
  - Added domain suffix stripping (`دوت نت`, `دوت كوم`, `دوت اورج`, `dot com`, `dot net`) and compound browser pairing (`افتح المتصفح وافتح كود التطور`).
- **Open-Ended Arbitrary Screen Vision Analysis (`vision_analyzer.py`, `CompanionOverlay.tsx`, `intent_router.py`)**:
  - Expanded screen query routing to allow arbitrary user questions ("شو هذا الخطأ؟", "ترجم النص الظاهر في المتصفح", "ما هو الكود المعروض").
  - Rewrote vision synthesizer to reason intelligently using desktop inspection and local LLM context without false "access denied" errors.
  - Enhanced Eye button in HUD UI with interactive query trigger: analyzes custom queries immediately or prepopulates editable starter prompts with auto-focus.
- **Silent Background Execution & Zero Console Flashes (`aegis.py`, `AegisAI.vbs`, `run.bat`, backend modules)**:
  - Enforced `CREATE_NO_WINDOW` and `SW_HIDE` across all child subprocess invocations and background tools.
  - Upgraded Windows Startup daemon and launcher scripts for clean, invisible execution.
- **Official GitHub Pages Landing Page (`docs/index.html`, `index.html`)**:
  - Deployed modern, responsive bilingual landing page with glassmorphism design.
  - Official attribution to Eng. Mohammad Abu Kashreef (MOHAMMAD ABU KASHREEF) and Code Evolution (كود التطور).
  - Direct download links to latest Windows installer and release packages.
- **System Diagnostics API & Test Suite (`main.py`, `test_screen_and_direct_routing.py`)**:
  - Added `/api/system/diagnostics` endpoint reporting health, screen latency, tool counts, and privacy guarantees.
  - Added dedicated test suite verifying canonical routing, arbitrary screen vision, and silent execution flags.

### Added - Phase 16: Native Windows Taskbar Branding & Application Identity Alignment
- **Windows AppUserModelID Decoupling (`aegis.py`, `window.py`, `launcher.cs`)**: Explicitly registered `AegisAI.Desktop.Companion.2026` via Windows `shell32.SetCurrentProcessExplicitAppUserModelID`, permanently preventing Windows Taskbar from grouping Aegis AI under generic `python.exe` / `.py` document file associations.
- **PyWebView WinForms Icon Binding (`window.py`)**: Bound `assets/icon.ico` directly into `webview.start(icon=...)`, preventing PyWebView from extracting the generic Python icon from `sys.executable`.
- **Win32 Native `WM_SETICON` Dispatch (`window.py`)**: Directly applied `WM_SETICON` (`ICON_BIG` 32x32 and `ICON_SMALL` 16x16) onto the native window HWND via `user32.LoadImageW` and `user32.SendMessageW`, ensuring the official shield logo appears on the Taskbar and in Alt+Tab window switching.
- **Recompiled Launcher (`AegisAI.exe`)**: Synchronized the C# native launcher to share the same AppUserModelID and recompiled with embedded `/win32icon:assets\icon.ico`.

### Added - Phase 15: Comprehensive User Personalization & Customization Settings, Reliable App Launching & Auto-Ollama Resilience
- **Interactive Personalization Settings Modal (`SettingsModal.tsx`, `CompanionOverlay.tsx`)**: Full-featured settings dialog accessible via header gear icon with 4 comprehensive tabs:
  1. *General*: Theme switcher (Dark / Light / System) with daytime CSS styles, Forced Language Lock (Auto / Arabic / English), Default browser preference (Chrome, Comet, Edge, Brave, Firefox, System Default), and Windows Startup auto-run toggle.
  2. *Voice & Audio*: Auto voice response toggle (`auto_speak`), speech rate speed control (-15%, 0%, +15%, +30%), and rich 13-voice neural catalog with instant live MP3 sample preview.
  3. *Quick Actions*: Customize and toggle welcome screen action tiles, add custom shortcut cards with command and title.
  4. *System*: Global summoning shortcut reference (`Alt + Space`), local storage diagnostics, and 1-click active session chat history wipe.
- **Persistent User Preferences Store (`session_manager.py`)**: SQLite `user_preferences` table persisting user configuration across app restarts with automatic migration.
- **Forced Language Enforcement (`router.py`)**: System instruction prompt injection ensuring that when Arabic is locked, the AI always answers in Arabic even if the user writes in English, and vice versa.
- **Multilingual Neural Voice Catalog & Preview API (`tts.py`, `routes.py`)**: Expanded edge-tts neural voice catalog to 13 regional accents (Saudi, Egyptian, Emirati, Jordanian, US, UK) with live `/api/voice/preview` MP3 synthesis.
- **Reliable Process & Browser Launching with Arguments (`process_manager.py`)**: Fixed critical bug where commands with arguments (e.g. opening URLs in Chrome or Comet) bypassed `AppFinder`, resolving exact executables (`chrome.exe`, `comet.exe`) directly from registry/install paths.
- **Expanded Arabic Application Translations (`intent_router.py`)**: Added friendly Arabic mappings for VS Code / Visual Studio (`فيجوال استديو`, `فيجوال ستوديو`, `كود`), browsers (`متصفح كروم`, `متصفح كومت`, `متصفح ايدج`), Telegram, WhatsApp, Discord, Spotify, Steam, Office apps, and PowerShell.
- **Resilient Ollama Auto-Start & Pollinations Rate Limit Guard (`main.py`, `ollama_provider.py`, `pollinations_provider.py`)**: Automatically detects and launches local Ollama daemon on Windows host startup using full path resolution, and intercepts cloud rate limits with friendly status messages and instant local model wake-up.
- **Quality Assurance**: 64 passing unit and integration tests (100% pass rate in `backend/tests`), 0 Flake8 lint warnings, clean Vite production bundle, and verified distribution package.

### Added - Phase 14: Native Windows Binary (`AegisAI.exe`), Auto-Startup Integration, Arabic Spoken NLP & Modern UI Overhaul
- **Native Windows Desktop Binary (`AegisAI.exe`, `launcher.cs`)**: Compiled via native Roslyn `csc.exe` into a fast, single-instance (`Global\AegisAI_Desktop_Mutex_2026`) GUI binary (`winexe`) with embedded official shield icon. Launches detached with zero console windows.
- **Windows Startup Integration (`startup.py`)**: Integrated with `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` to launch Aegis AI automatically on Windows logon in silent background mode (`--background`). Controlled via system tray right-click menu ("Start with Windows") and REST API (`/api/desktop/startup`).
- **Arabic Spoken NLP & Phonetic Normalization (`intent_router.py`)**: Automatic phonetic conversion of Arabic spoken domains ("دوت نت" -> `.net`, "دوت كوم" -> `.com`, "دوت اورج" -> `.org`) and robust compound browser routing ("كروم وافتح موقع كود التطور دوت نت"). Added defensive web-intent redirection inside `LaunchAppTool`.
- **Natural Z-Order Window Layering (`window.py`, `CompanionOverlay.tsx`)**: Unpinned by default (`is_on_top = False`), allowing Aegis to smoothly drop behind Chrome, VSCode/Codex, and other applications when clicking outside, with full pin-on-top toggle support.
- **Spacious & Modern UI Overhaul (`ActionCard.tsx`, `window.py`)**: Expanded window size (780x640) and completely redesigned action cards with human-readable titles, tool-specific icons, browser badges, and collapsible execution details, eliminating cramped layouts and raw JSON dumps.
- **Solid Desktop Surface & Clean Header Dragging (`App.tsx`, `index.css`, `CompanionOverlay.tsx`)**: Replaced translucent padding and bleeding margins with a 100% solid, opaque desktop application canvas (`#0b0f19`) preventing background apps from bleeding through. Configured native full-header dragging (`pywebview-drag-region`) with non-overlapping title, badges, and controls.
- **Generic Arabic Browser Intent & Ollama Auto-Start (`intent_router.py`, `main.py`)**: Added support for generic browser phrasing (*"افتح المتصفح و افتح كود التطور"*) routing directly in 0.0ms without triggering cloud fallback or rate limits, and added automatic background launch of local Ollama daemon if installed on host.
- **Whisper & VAD Performance Optimizations**: Configured `condition_on_previous_text=False` and optimized CPU thread allocation for faster STT response.
- **Quality Assurance**: Added full test suite in `backend/tests/test_arabic_voice_tools.py` (58 total passing tests across full codebase, 0 flake8 warnings). Built updated portable distribution archive with SHA-256 validation.

### Added - Phase 13: Arabic Voice Command Routing, Targeted URL/Browser Opening, Draggable Companion & Native Background Mode
- **Zero-Latency Arabic Voice Intent Routing (`intent_router.py`)**: Real-time regex-based natural language intent router supporting Arabic spoken requests for launching applications (`المفكرة`, `الرسام`, `كروم`, `كومت`), opening websites, muting/unmuting/adjusting volume (`كتم الصوت`, `علي الصوت`), capturing screenshots (`صور الشاشة`), minimizing all windows (`صغر كل النوافذ`), and taking daily notes (`اكتب ملاحظة`).
- **First-Class Browser & URL Navigation Tool (`system_tools.py`)**: Added `OpenUrlTool` (`open_url`) supporting targeted browser execution (`chrome`, `msedge`, `brave`, `comet`, `firefox`, default) with automatic `https://` protocol resolution and common domain expansion.
- **Draggable Companion Window (`window.py`, `CompanionOverlay.tsx`)**: Configured native `easy_drag=True` and `resizable=True` on PyWebView with dedicated `pywebview-drag-region` header handle (`GripHorizontal`), allowing fluid repositioning anywhere across multiple displays.
- **Always-on-Top Toggle / Pin Button**: Added interactive Pin button in overlay header with `/api/desktop/pin` REST endpoint and JS bridge method (`toggle_on_top`) to permit other windows to be viewed alongside or over Aegis smoothly.
- **Silent Background App Launchers (`run.bat`, `AegisAI.vbs`)**: Updated `run.bat` to launch `pythonw.exe` detached with `start ""`, immediately closing the command prompt. Added `AegisAI.vbs` for 100% windowless double-click execution directly from Windows Explorer.
- **Quality Assurance**: Added full test suite in `backend/tests/test_arabic_voice_tools.py` (54 total passing tests across full codebase, 0 flake8 warnings). Built updated portable distribution archive with SHA-256 validation.

### Added - Phase 12: 1-Click Offline Model Download Wizard with Live Byte Progress
- **Interactive Model Selection Grid (`ModelSetupBanner.tsx`)**: Transparent multi-model selection card wizard displaying size, capabilities, and CPU recommendation badges for Qwen 2.5 (1.5B), Llama 3.2 (1B), and Llama 3.2 (3B).
- **Streaming Byte Telemetry**: Real-time download progress displaying formatted bytes (`MB / GB`), percentage, and detailed phases ("pulling manifest", "downloading", "verifying sha256").
- **Smart System Diagnostics**: Contextual recovery options directing users to download Ollama if missing, or auto-starting the local daemon with one click if stopped.
- **Backend Streaming Test Suite (`test_ai_runtime.py`)**: Added integration tests verifying Ollama NDJSON progress streaming and FastAPI `/api/models/pull` Server-Sent Events.
- **Quality Assurance**: Production frontend bundle compiled in 9.42s; 48 backend tests passing with 0 flake8 warnings.

### Added - Phase 11: Client-Side Voice Activity Detection (VAD) & Silence Auto-Stop
- **Client-Side VAD Engine (`useMicrophoneCapture.ts`)**: Built-in real-time energy analysis via Web Audio API `AudioContext` and `AnalyserNode` automatically detects active speech onset and natural sentence pauses.
- **Hands-Free Trailing Silence Auto-Stop**: Stops recording automatically after a 1.3-second trailing pause following speech, triggering Faster-Whisper transcription without requiring a second manual click.
- **Acoustic Guardrails**: 500 ms minimum speech duration rejects transient mouth clicks or keyboard taps; 20-second safety timeout protects against loud ambient background environments.
- **Dynamic Feedback & Visual Cues**: Added real-time speaking indicators, transcribing spinner, and adaptive placeholder text in `CompanionOverlay.tsx`.
- **Quality Assurance**: Production frontend bundle compiled with 0 TypeScript errors; 46 backend unit & integration tests passing with 0 flake8 warnings.

### Added - Phase 10: Native System Tray Icon, Background Daemon Mode & Minimization
- **Windows System Tray Icon (`tray.py`)**: Dedicated notification area companion icon running detached on a background daemon thread with quick-action right-click context menu via `pystray`.
- **Hide-to-Tray on Window Close**: Intercepted PyWebView `closing` event in `window.py` to prevent accidental process termination. Clicking close, pressing `ESC`, or `Alt+F4` minimizes the overlay to the tray while keeping background wake-word and API servers active.
- **Dynamic Tray Menu Actions**: Instant overlay summon ("Show Aegis AI (Alt+Space)", double-click default), live checkmark toggle for wake word listening ("Wake Word: Hey Aegis"), quick web HUD launcher, and graceful application exit.
- **Official Brand Assets**: Added procedural shield icon generator and multi-resolution Windows icon bundle (`assets/icon.ico`, `assets/icon.png`) integrated into Inno Setup and distribution packager.
- **Quality Assurance**: Added full test suite in `backend/tests/test_tray.py` (46 total passing tests, 0 flake8 warnings).

### Added - Phase 9: High-Performance In-Process Screen Capture (< 100ms)
- **Direct Win32 Station Attachment (`_ensure_interactive_desktop()`)**: Connects process and calling thread to `winsta0\default` to unlock GDI desktop capture across background agent threads and worker processes.
- **In-Process Ultra-Fast Capture**: Swapped slow external PowerShell subprocess (`5,031 ms`) for native Pillow `ImageGrab` with in-memory `io.BytesIO` encoding, achieving **153.3 ms** mean PNG capture (**32.8x speedup**) and **66.8 ms** mean JPEG capture (**75.3x speedup**).
- **Multi-Monitor Bounding Box**: Native `all_screens=True` virtual desktop capture spans multi-monitor setups without cropping.
- **Resilient Fallback Hierarchy**: Secondary PowerShell subprocess and tertiary headless simulated capture ensure continuous execution across headless CI and secure service sessions.
- **Empirical Validation**: Benchmarked over 5 warm iterations on Windows 11 host with JSON evidence stored in `.github/validation_evidence/section3b_screen_capture.json`. 41 unit/integration tests passing with 0 flake8 warnings.

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

