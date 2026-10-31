# Issue #3: Real Voice Pipeline (Faster-Whisper STT, Microphone Capture & Neural TTS)

- **Labels**: `enhancement`, `voice`, `stt`, `tts`, `mvp`, `p0`
- **Milestone**: MVP Recovery (Phase 3)
- **Status**: RESOLVED (Completed & Verified)
- **Branch**: `feat/phase3-real-voice-pipeline`

## Resolution Summary
1. **Faster-Whisper STT (`backend/aegis_core/voice/stt.py`)**:
   - Integrated offline CTranslate2 INT8 quantized model (`tiny.en`) with Silero VAD filtering.
   - 100% offline, zero cloud exfiltration, zero API keys required.
2. **Neural TTS (`backend/aegis_core/voice/tts.py`)**:
   - Integrated high-fidelity Edge Neural voices (`en-US-AriaNeural`, `en-US-GuyNeural`, `en-US-JennyNeural`, `en-GB-SoniaNeural`).
   - Zero-cost, zero-API-key natural neural audio generation with local SAPI offline fallback.
3. **Microphone Capture Hook (`apps/desktop-ui/src/hooks/useMicrophoneCapture.ts`)**:
   - Web Audio API and `MediaRecorder` hook recording audio in 16kHz mono.
   - Real-time audio waveform volume level analyzer powering live microphone button reactivity.
   - Dispatches audio to `/api/voice/transcribe` and triggers companion agent execution.
4. **Voice Endpoints & Pipeline Controller**:
   - `GET /api/voice/voices`
   - `POST /api/voice/transcribe`
   - `POST /api/voice/synthesize`
   - `POST /api/voice/speak`
5. **Quality Verification**:
   - 22/22 pytest tests passing (`test_voice.py` included).
   - `flake8 backend` 0 warnings.
   - Frontend bundle built with 0 errors.

## Problem Statement
The current voice pipeline is largely fake:
1. `transcribe_audio_file` in `pipeline.py` was a dummy `await asyncio.sleep(0.1)` returning `""`.
2. Speech output relied on a legacy, synchronous PowerShell call to Windows SAPI5 (`System.Speech.Synthesis`), producing robotic audio that locked process threads.
3. No microphone recording, no voice activity detection (VAD), and no wake word support existed.

## Scope & Acceptance Criteria
1. **Delete All Stubs**:
   - Completely remove the `asyncio.sleep(0.1)` dummy code.
2. **Offline Speech Recognition (STT)**:
   - Integrate `faster-whisper` (CTranslate2 INT8 quantized offline Whisper models, `tiny.en` / `base.en`).
   - Support transcribing audio buffers and file inputs with zero cloud dependency.
3. **Natural Neural TTS**:
   - Integrate `edge-tts` (Microsoft Edge natural neural speech voices with zero API keys) for crystal-clear natural voice synthesis.
   - Integrate local `piper-tts` / offline audio playback fallback.
4. **Microphone Audio Input & Voice Activity**:
   - Provide `/api/voice/transcribe` endpoint accepting microphone audio uploads (WAV / WebM) from the React HUD.
   - React HUD captures live microphone stream via Web Audio API / `MediaRecorder` when mic button is clicked, sending audio directly for transcription and execution.
5. **End-to-End Voice Flow**:
   - User clicks mic or speaks -> Audio transcribed by Faster-Whisper -> ReAct Agent executes command -> Response synthesized into natural neural speech.
