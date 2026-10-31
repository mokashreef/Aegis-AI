# Issue #7: Missing Production Wake Word Engine (OpenWakeWord Integration Required)

- **Labels**: `bug`, `voice`, `wake-word`, `reality-check`, `p0`
- **Milestone**: MVP Production Validation
- **Status**: OPEN / IDENTIFIED GAP
- **Branch**: `audit/product-validation-execution`

## Reality Check Finding
During the Production Validation Audit of Section 2 (Voice), an exhaustive search across the entire backend code (`backend/aegis_core`) confirmed:
**Continuous wake-word detection ("Hey Aegis") is NOT implemented.**

### Current State
1. Voice activation is currently triggered manually by the user clicking the microphone button or pressing a shortcut in the desktop HUD (`useMicrophoneCapture`).
2. There is no active PyAudio / SoundDevice background thread continuously running an ONNX wake word detector (e.g. `openWakeWord`) with an acoustic model for "Hey Aegis".
3. Claiming continuous wake-word listening without an ONNX model is vaporware.

### Required Architecture & Deliverables
1. Integrate `openwakeword` with pre-trained or custom ONNX model for "Hey Aegis" / "Aegis".
2. Run an isolated, low-power background worker thread consuming single-channel 16kHz audio from `pyaudio` or `sounddevice`.
3. Trigger the `overlay_manager.show()` native method and switch HUD to `listening` state upon high-confidence acoustic detection (> 0.65 threshold).
4. Ensure CPU consumption remains under 2% during continuous background acoustic monitoring.
