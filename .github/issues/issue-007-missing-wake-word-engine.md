# Issue #7: Missing Production Wake Word Engine (OpenWakeWord Integration Required)

- **Labels**: `voice`, `wake-word`, `onnx`, `p0`
- **Milestone**: MVP Production Hardening
- **Status**: CLOSED (Resolved with Empirical Proof)
- **Branch**: `feat/wake-word-engine`
- **Resolution PR**: `.github/pull_requests/pr-phase7-wake-word-engine.md`

## Resolution Summary
Implemented a 100% offline, local ONNX acoustic wake-word engine and background microphone listener:
1. **Zero Bloat Architecture**: Engineered directly on `onnxruntime` and `sounddevice` (PortAudio bundled), completely avoiding 150MB+ scientific libraries (`scipy`, `scikit-learn`). Total model weight is only 3.6 MB on disk (`data/models/wakeword`).
2. **Sub-5ms Inference**:
   - Engine initialization latency: **71.62 ms**
   - Silence RMS gate latency: **23.99 microseconds**
   - Active acoustic frame latency: **4.35 ms** (against an 80ms audio chunk budget, 0.054x real-time factor)
   - Process RAM (RSS): **86.62 MB**
3. **Hardware & Win32 Integration**:
   - `WakeWordListener` runs on an isolated daemon thread capturing 16kHz mono audio from default microphone.
   - Automatically unhides and centers the desktop overlay (`overlay_manager.show()`) upon detection.
   - Debounce / cooldown timer (2.5s) prevents false double triggers.
4. **Desktop HUD & REST API**:
   - Exposes `/api/voice/wakeword/status`, `/api/voice/wakeword/toggle`, `/api/voice/wakeword/config`.
   - Desktop HUD top bar displays active wake-word state badge with live pulsing indicator and 1-click toggle.
5. **Validation Artifacts**:
   - Test Suite: 5 dedicated tests added (`backend/tests/test_wake_word.py`), 38/38 tests passing.
   - Flake8: 0 warnings.
   - Benchmark Evidence: Stored at `.github/validation_evidence/section2b_wake_word.json`.
