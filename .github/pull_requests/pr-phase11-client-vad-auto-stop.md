# PR: Phase 11 - Client-Side Voice Activity Detection (VAD) & Automatic Silence Auto-Stop

## Summary
- **Issue**: Resolves [Issue #11](https://github.com/mokashreef/Aegis-AI/issues/11)
- **Branch**: `feat/client-vad-auto-stop` -> `main`
- **Labels**: `voice`, `vad`, `frontend`, `ux`, `p1`

## Motivation & Problem
Previously, voice queries required two manual clicks: one to start recording, and another to stop recording.
This PR delivers an autonomous ambient voice experience using client-side Voice Activity Detection (VAD).

## Changes
1. **Adaptive VAD Engine (`useMicrophoneCapture.ts`)**:
   - Web Audio API real-time energy analysis via `AnalyserNode`.
   - Voice onset detection threshold (`0.04`).
   - Trailing silence detection (`1300 ms` pause) triggers automatic recording completion.
   - Guardrails: 500 ms minimum speech duration to discard spurious clicks; 20 s maximum safety cutoff.
2. **Companion UI Visual State (`CompanionOverlay.tsx`)**:
   - Added `isTranscribing` and `isSpeaking` visual states.
   - Contextual placeholder and status text.
   - Pulsing mic scale based on real-time acoustic input energy.
3. **Compilation & Testing**:
   - Production bundle compiled with Vite in 10.62s.
   - 46 backend unit & integration tests passing in 13.02s.
   - 0 flake8 warnings.
