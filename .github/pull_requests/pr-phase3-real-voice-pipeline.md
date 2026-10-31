# Pull Request: Real Voice Pipeline (Faster-Whisper STT & Neural TTS)

## Title
`feat(voice): implement Faster-Whisper offline STT, Edge neural TTS, and microphone capture (Phase 3)`

## Summary
Replaces fake stub voice code (`asyncio.sleep(0.1)`) with a production-grade local and neural voice pipeline adhering to the Zero Mandatory API Key mandate:
1. **Offline Faster-Whisper Speech Recognition**:
   - `FasterWhisperEngine` (`backend/aegis_core/voice/stt.py`) powered by CTranslate2 with INT8 quantization on CPU and Silero VAD silence filtering.
2. **Natural Neural TTS**:
   - `NeuralTTSEngine` (`backend/aegis_core/voice/tts.py`) delivering natural human-like voice synthesis (`en-US-AriaNeural`, `en-US-GuyNeural`, etc.) with zero paid API keys, with local Windows SAPI fallback.
3. **Microphone Audio Capture**:
   - `useMicrophoneCapture` hook (`apps/desktop-ui/src/hooks/useMicrophoneCapture.ts`) capturing audio with Web Audio API, dynamic volume level metering, and automatic submission to `/api/voice/transcribe`.
4. **Desktop HUD Integration**:
   - Companion overlay microphone button with sound-level reactive scaling and direct voice query execution.

## Verification
- `pytest backend/tests -v` -> 22/22 tests passing.
- `flake8 backend` -> 0 warnings.
- `npm run build` in `apps/desktop-ui` -> 0 errors.
