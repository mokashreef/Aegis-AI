# PR: Arabic Voice Command Routing, Targeted URL/Browser Opening, Draggable Companion & Native Background Mode

## Summary of Changes
Addresses **Issue #13** and user feedback regarding Arabic voice command failures, missing URL/browser opening, immovable fixed window, and terminal console dependency.

### Key Changes
1. **Bilingual Arabic Natural Language Intent Routing (`backend/aegis_core/automation/intent_router.py`)**:
   - Added regex intent routing and entity extraction for Arabic spoken commands.
   - Supports natural Arabic queries for opening websites (e.g. "افتح لي موقع يوتيوب بمتصفح كروم", "افتح جوجل بمتصفح كومت").
   - Maps Arabic app names (`المفكرة`, `الرسام`, `كروم`, `كومت`, etc.) and system controls (`كتم الصوت`, `علي الصوت`, `صور الشاشة`, `صغر كل النوافذ`).
2. **First-Class URL/Browser Tool (`backend/aegis_core/automation/system_tools.py`)**:
   - Implemented `OpenUrlTool` (`open_url`) supporting direct browser targeting (`chrome`, `msedge`, `brave`, `comet`, `firefox`).
   - Normalizes known domains and queries with automatic `https://` protocol enforcement.
3. **Draggable Companion Window & Always-on-Top Toggle (`backend/aegis_core/desktop/window.py`, `apps/desktop-ui/src/components/CompanionOverlay.tsx`)**:
   - Configured `easy_drag=True` and `resizable=True` on PyWebView window.
   - Added visual drag region handle (`pywebview-drag-region`) in top navigation header.
   - Added Always-on-Top (`Pin`) toggle button with synchronized REST (`/api/desktop/pin`) and JS bridge.
4. **Consoleless Background Launchers (`run.bat`, `AegisAI.vbs`)**:
   - Updated `run.bat` to launch `pythonw.exe` detached with `start ""`, immediately closing the CMD prompt.
   - Added `AegisAI.vbs` for silent double-click execution directly from Windows Explorer.
5. **Quality & Test Automation (`backend/tests/test_arabic_voice_tools.py`)**:
   - Added comprehensive tests for Arabic intent parsing, URL opening, and pin toggling.
   - All 54 tests in the test suite pass cleanly (`54 passed in 33.07s`).
   - Flake8 linting: 0 warnings, 0 errors.

## Verification
- Unit test suite: `pytest backend/tests -v` -> 54/54 PASSED.
- Linter: `flake8 backend scripts aegis.py` -> Clean (0 warnings).
- Frontend: `npm --prefix apps/desktop-ui run build` -> Clean build (code 0).
- Distribution: `python scripts/build_distribution.py` -> Successfully generated portable zip & SHA-256.
