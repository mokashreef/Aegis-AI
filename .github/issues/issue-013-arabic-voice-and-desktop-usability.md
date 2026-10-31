# Issue #13: Arabic Voice Command Routing, URL Opening, Draggable Window & Native Background App Mode

- **Labels**: `voice`, `arabic`, `desktop`, `ux`, `usability`, `p1`
- **Milestone**: MVP Usability & Accessibility
- **Status**: CLOSED
- **Branch**: `feat/arabic-voice-draggable-desktop`
- **Resolution**: Implemented & Verified with Empirical Proof

## Problem Analysis
User testing revealed four critical usability bottlenecks:
1. **Voice Commands in Arabic Fail Silently**: Whisper accurately transcribes Arabic speech, but `IntentRouter` only contained English regex patterns. Arabic requests (e.g. "افتح لي موقع يوتيوب بمتصفح كروم") were dropped to the LLM, resulting in zero action if local models were unconfigured.
2. **Missing Web/URL Opening Capability**: The toolchain lacked an `OpenUrlTool`. Commands requesting to visit websites or search web queries were misrouted to executable finders.
3. **Immobile / Fixed Window**: `easy_drag=False` was configured on the PyWebView window, preventing users from dragging or repositioning the companion overlay on their screen.
4. **Aggressive `on_top` & Modal Blocking**: When `on_top=True` was rigidly enforced, newly launched applications opened behind the companion without an option to unpin or multitask smoothly.
5. **Console Terminal Dependency**: Launching via `python aegis.py` kept an open black CMD window, breaking the native desktop app feel.

## Delivered Solutions
1. **Bilingual Arabic Natural Language Routing (`intent_router.py`)**:
   - Implemented zero-latency Arabic regex matching and entity extraction for web navigation, application launching, audio volume (mute/unmute/increase/decrease), display brightness, screenshots, and daily notes.
   - Built Arabic domain dictionary (`يوتيوب`, `جوجل`, `غيتهاب`, `تويتر`, `فيسبوك`, `شات جي بي تي`, etc.) and browser aliases (`كروم`, `كومت`, `ايدج`, `بريف`, `فايرفوكس`).
2. **First-Class `OpenUrlTool` (`system_tools.py`)**:
   - Added `OpenUrlTool` registered under `RiskLevel.MUTATING_SAFE`.
   - Supports targeted browsers (`chrome`, `msedge`, `brave`, `comet`, `firefox`, default) with automatic `https://` normalization.
3. **Draggable Companion Window & Pin Toggle (`window.py`, `CompanionOverlay.tsx`)**:
   - Enabled `easy_drag=True` and `resizable=True` on PyWebView window.
   - Added visible drag handle (`pywebview-drag-region`) in top navigation header with `GripHorizontal` icon.
   - Added Pin / Always-on-Top toggle button with real-time REST (`/api/desktop/pin`) and JS bridge synchronization.
4. **Zero-Console Background Launcher (`run.bat`, `AegisAI.vbs`)**:
   - Updated `run.bat` to launch `.venv\Scripts\pythonw.exe` detached with `start ""`, immediately exiting the command prompt.
   - Added `AegisAI.vbs` for 100% windowless double-click execution directly from Windows Explorer.

## Empirical Verification
- **Unit Tests**: Added `backend/tests/test_arabic_voice_tools.py` covering Arabic URL routing, Arabic app launching, system controls, `OpenUrlTool` execution, `/api/desktop/pin` endpoints, and `DesktopOverlayManager.toggle_on_top`.
- **Full Suite**: 54/54 tests passing in 33.07s (`pytest backend/tests -v`).
- **Linter**: 0 flake8 warnings, 0 errors across `backend scripts aegis.py`.
- **Frontend Build**: Vite + TypeScript compiled successfully with 0 errors.
- **Distribution**: Rebuilt release package `releases/Aegis-AI-v0.2.0-alpha-Windows-x64-Portable.zip` with verified SHA-256 checksum.
